import argparse, pathlib
from preprocess import build_model_input
from optimiser import solve_week
import pandas as pd
import helper_maxflow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", choices=["dry", "rain"], default="dry")
    ap.add_argument("--out", default="plan.csv")
    ap.add_argument("--cost_per_cbm", type=float, default=20000.0, help="Cost per CBM (FCFA)")
    args = ap.parse_args()

    # 1. Build the model input (all possible truck-forest assignments)
    df = build_model_input(season=args.season)

    # 2. Add profit columns if sale_price_per_cbm exists
    if "sale_price_per_cbm" in df.columns:
        df["cost_per_cbm"] = args.cost_per_cbm
        df["profit_per_cbm"] = df["sale_price_per_cbm"] - df["cost_per_cbm"]
        df["profit_per_trip"] = df["cbm_per_truck"] * df["profit_per_cbm"]
        maximize_profit = True
    else:
        maximize_profit = False

    # 3. Solve the weekly optimization problem
    plan = solve_week(df, maximize_profit=maximize_profit)

    # Compute profit using profit_per_cbm_euros from forests.csv
    plan['profit'] = plan.apply(lambda row: row['trips_planned'] * df.loc[(row['truck_id'], row['forest_id']), 'cbm_per_truck'] * df.loc[(row['truck_id'], row['forest_id']), 'profit_per_cbm_euros'], axis=1)

    # 4. Write the plan to CSV
    pathlib.Path(args.out).write_text(plan.to_csv(index=False))

    # 5. Compute and print summary statistics
    total_cbm = (plan["trips_planned"] * plan["cbm_per_truck"]).sum()
    print(f"✅  Plan written to {args.out}")
    print(plan.to_markdown(index=False))
    print("\n---- Weekly summary ----")
    print(f"Total trips : {plan['trips_planned'].sum():,}")
    print(f"Total CBM   : {total_cbm:,.0f} m³")
    if maximize_profit:
        total_profit = plan['profit'].sum()
        print(f"Total Profit  : {total_profit:,.0f} FCFA")

    # Print per-forest volume depletion
    forest_volumes = df.reset_index().drop_duplicates("forest_id").set_index("forest_id")["weekly_stockpile_cbm"]
    plan["depleted_cbm"] = plan["trips_planned"] * plan["cbm_per_truck"]
    depleted_by_forest = plan.groupby("forest_id")["depleted_cbm"].sum()
    print("\n---- Forest Volume Depletion ----")
    print(f"{'Forest':30} {'Original':>10} {'Depleted':>10} {'Remaining':>10}")
    for forest in forest_volumes.index:
        original = forest_volumes[forest]
        depleted = depleted_by_forest.get(forest, 0)
        remaining = original - depleted
        print(f"{forest:30} {original:10,.0f} {depleted:10,.0f} {remaining:10,.0f}")

    # 6. Print unassigned trucks
    trucks = pd.read_csv("data/trucks.csv")
    trucks["truck_id"] = trucks["truck_id"].astype(str).str.strip()
    assigned_trucks = set(plan["truck_id"].astype(str))
    unassigned = trucks[~trucks["truck_id"].isin(assigned_trucks)]
    if not unassigned.empty:
        print("\n---- Unassigned Trucks ----")
        print(unassigned[["truck_id", "type"]].to_markdown(index=False))
    else:
        print("\nAll trucks were assigned at least one trip.")

    # --- Second pass: Max-flow assignment of unassigned trucks to forests with leftover volume ---
    if not unassigned.empty:
        print("\n---- Second Pass: Max-flow Assignment of Unassigned Trucks ----")
        remaining_by_forest = {forest: forest_volumes[forest] - depleted_by_forest.get(forest, 0) for forest in forest_volumes.index}
        idle_df = unassigned.copy()
        idle_df["available_hours"] = idle_df["drive_hours"] - idle_df.get("maintenance_hours", 0)
        forests_with_leftover = [f for f in forest_volumes.index if remaining_by_forest[f] > 0]
        forests_df = (
            df.reset_index()
              .drop_duplicates("forest_id")
              .set_index("forest_id")
              .loc[forests_with_leftover]
              .reset_index()[["forest_id", "trip_hours", "cbm_per_truck"]]
        )
        forests_df = forests_df.rename(columns={"trip_hours": "turnaround_time"})
        forests_df["volume_left"] = forests_df["forest_id"].map(remaining_by_forest)
        if maximize_profit:
            forests_df["profit_per_trip"] = forests_df.apply(lambda row: df.loc[(df.reset_index()["truck_id"].iloc[0], row["forest_id"]), "profit_per_trip"], axis=1)
        extra_assignments = helper_maxflow.top_up_with_flow(idle_df, forests_df)
        if extra_assignments:
            new_plan = pd.DataFrame([
                {"truck_id": a["truck_id"], "forest_id": a["forest_id"], "trips_planned": a["trips"], "cbm_per_truck": df.loc[(int(a["truck_id"]), a["forest_id"]), "cbm_per_truck"]}
                for a in extra_assignments
            ])
            print("\nAdded assignments (max-flow, full trips):")
            print(new_plan.to_markdown(index=False))
            print(f"Extra CBM from max-flow full trips: {new_plan['trips_planned'].mul(new_plan['cbm_per_truck']).sum():,.0f} m³")
        else:
            print("No additional assignments could be made in the second pass (max-flow, full trips).")
        # --- Now run half-trip max-flow ---
        half_assignments = helper_maxflow.half_trip_maxflow(idle_df, forests_df)
        if half_assignments:
            half_plan = pd.DataFrame([
                {"truck_id": a["truck_id"], "forest_id": a["forest_id"], "trips": a["trips"], "cbm_collected": a["cbm_collected"], "hours_used": a["hours_used"]}
                for a in half_assignments
            ])
            print("\nAdded assignments (max-flow, half trips):")
            print(half_plan.to_markdown(index=False))
            print(f"Extra CBM from max-flow half trips: {half_plan['cbm_collected'].sum():,.0f} m³")
        else:
            print("No additional assignments could be made in the half-trip max-flow phase.")

    # Print summary statistics
    total_cbm = (plan["trips_planned"] * plan["cbm_per_truck"]).sum()
    print(f"✅  Plan written to {args.out}")
    print(plan.to_markdown(index=False))
    print("\n---- Weekly summary ----")
    print(f"Total trips : {plan['trips_planned'].sum():,}")
    print(f"Total CBM   : {total_cbm:,.0f} m³")
    if maximize_profit:
        total_profit = plan['profit'].sum()
        print(f"Total Profit  : {total_profit:,.0f} FCFA")

    # --- Build daily schedule ---
    daily_hours_limit = 10.5
    plan_expanded = []
    for _, row in plan.iterrows():
        truck = row['truck_id']
        forest = row['forest_id']
        trips = int(row['trips_planned'])
        trip_hours = df.loc[(truck, forest), 'trip_hours']
        for trip_num in range(trips):
            plan_expanded.append({'truck_id': truck, 'forest_id': forest, 'trip_hours': trip_hours})
    schedule_df = pd.DataFrame(plan_expanded)
    # Assign trips to days for each truck
    schedule_df['day'] = 0
    for truck, group in schedule_df.groupby('truck_id'):
        hours_used = 0
        day = 1
        for idx in group.index:
            if hours_used + group.loc[idx, 'trip_hours'] > daily_hours_limit:
                day += 1
                hours_used = 0
            schedule_df.at[idx, 'day'] = day
            hours_used += group.loc[idx, 'trip_hours']
    # Print daily allocation
    print("\n---- Daily Truck Allocation ----")
    for day in sorted(schedule_df['day'].unique()):
        print(f"Day {day}:")
        for forest in schedule_df[schedule_df['day'] == day]['forest_id'].unique():
            trucks = schedule_df[(schedule_df['day'] == day) & (schedule_df['forest_id'] == forest)]['truck_id'].tolist()
            print(f"  {forest}: {', '.join(map(str, trucks))}")

    # --- Print per-forest truck trip allocation ---
    print("\n---- Per-Forest Truck Trip Allocation ----")
    for forest in plan['forest_id'].unique():
        print(f"Forest: {forest}")
        forest_plan = plan[plan['forest_id'] == forest]
        total_trips = 0
        for _, row in forest_plan.iterrows():
            print(f"  Truck {row['truck_id']}: {int(row['trips_planned'])} trips")
            total_trips += int(row['trips_planned'])
        print(f"  Total trips for {forest}: {total_trips}")

if __name__ == "__main__":
    main()