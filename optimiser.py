# """
# Builds and solves weekly mixed integer linear program (MILP)

# Decision variable - 
# ------------------------
# x[t,f] = int number of round trips truck (t) performs to forest (f)
#          during the coming week 
 
         
# objective - 
# ------------------------
# Maximise Σ score [t,f] * x[t,f]
# ( score = cubic metre / truck-day )


# Constraints 
# ------------------------
# 1) per truck calendar day budget 
#     Σ_f trip_days[f] * x[t,f] <= drive_days[t]
    
# 2) per forest weekly trip cap 
#     Σ_t x[t,f] <= max_trips_wk[f]
    
# 3) x int and >= 0 ( Implicit in OR-tools IntVar )
# """

# import math
# import pandas as pd #pandas library 
# from ortools.linear_solver import pywraplp #OR tools is library for solving optimizing probs (scheduling, routing, and assignments)
# #pywraplp part of OR tools, creates and solves linear programming and integer programming 

# #CBC = coin or branch and cut solver - open source solver that can handle linear and int programming probs 
# #telling OR tools to use CBC solver 

# def solve_week(df: pd.DataFrame) -> pd.DataFrame:
#     solver = pywraplp.Solver.CreateSolver("CBC")

#     # Print problem size for diagnosis
#     n_trucks = df.index.get_level_values(0).nunique()
#     n_forests = df.index.get_level_values(1).nunique()
#     print(f"Number of trucks: {n_trucks}")
#     print(f"Number of forests: {n_forests}")
#     print(f"Number of variables (truck-forest pairs): {len(df)}")

#     # 1. Decision variables: x[t, f] = number of trips truck t makes to forest f (continuous)
#     var = {}
#     for (t, f), row in df.iterrows():
#         # Upper bound: max trips possible for this truck to this forest (in hours), capped at 15
#         if row.trip_hours > 0:
#             phys_lim = row.drive_hours / row.trip_hours
#         else:
#             phys_lim = 0
#         ub = min(max(0, phys_lim), 15)
#         var[(t, f)] = solver.NumVar(0, ub, f"x_{t}_{f}")  # Continuous variable

#     # 2. Constraint: Each truck can't exceed its available drive hours
#     for t, t_rows in df.groupby(level=0):
#         solver.Add(
#             solver.Sum(row.trip_hours * var[(t, f)]
#                        for (_, f), row in t_rows.iterrows())
#             <= t_rows.drive_hours.iloc[0]
#         )

#     # 3. Constraint: Each forest can't have more logs picked up than its available volume
#     for f, f_rows in df.groupby(level=1):
#         solver.Add(
#             solver.Sum(row.cbm_per_truck * var[(t, f)]
#                        for (t, _), row in f_rows.iterrows())
#             <= f_rows.weekly_stockpile_cbm.iloc[0]
#         )

#     # 4. Objective: Maximize total CBM delivered
#     total_cbm = solver.Sum(df.loc[(t, f), "cbm_per_truck"] * var[(t, f)]
#                            for (t, f) in var)
#     solver.Maximize(total_cbm)

#     # # 5. Set a 10-minute (600,000 ms) time limit
#     # solver.set_time_limit(600000)

#     # 6. Solve and extract the plan
#     status = solver.Solve()
#     if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
#         raise RuntimeError("CBC did not find an optimal or feasible solution within the time limit")
#     if status == pywraplp.Solver.FEASIBLE:
#         print("⚠️  Time limit reached: returning best feasible solution found.")

#     def round_down_to_half(x):
#         return math.floor(x * 2) / 2

#     plan = (
#         pd.DataFrame(
#             [
#                 (t, f, round(round_down_to_half(var[(t, f)].solution_value()), 1))
#                 for (t, f) in var
#             ],
#             columns=["truck_id", "forest_id", "trips_planned"],
#         )
#         .query("trips_planned > 0.01")
#         .sort_values(["truck_id", "forest_id"])
#         .reset_index(drop=True)
#     )
#     return plan


# #improved logic for the trips to reach park then count the cbm (so 0.5 and above, if it were 2.7 then do 3 trip volume collected )
# import math
# import pandas as pd #pandas library 
# from ortools.linear_solver import pywraplp #OR tools is library for solving optimizing probs (scheduling, routing, and assignments)
# #pywraplp part of OR tools, creates and solves linear programming and integer programming 

# #CBC = coin or branch and cut solver - open source solver that can handle linear and int programming probs 
# #telling OR tools to use CBC solver 

# def solve_week(df: pd.DataFrame) -> pd.DataFrame:
#     solver = pywraplp.Solver.CreateSolver("CBC")

#     # Print problem size for diagnosis
#     n_trucks = df.index.get_level_values(0).nunique()
#     n_forests = df.index.get_level_values(1).nunique()
#     print(f"Number of trucks: {n_trucks}")
#     print(f"Number of forests: {n_forests}")
#     print(f"Number of variables (truck-forest pairs): {len(df)}")

#     # 1. Decision variables: x[t, f] = number of trips truck t makes to forest f (continuous)
#     var = {}
#     for (t, f), row in df.iterrows():
#         # Upper bound: max trips possible for this truck to this forest (in hours), capped at 15
#         if row.trip_hours > 0:
#             phys_lim = row.drive_hours / row.trip_hours
#         else:
#             phys_lim = 0
#         ub = min(max(0, phys_lim), 15)
#         var[(t, f)] = solver.NumVar(0, ub, f"x_{t}_{f}")  # Continuous variable

#     # 2. Constraint: Each truck can't exceed its available drive hours
#     for t, t_rows in df.groupby(level=0):
#         solver.Add(
#             solver.Sum(row.trip_hours * var[(t, f)]
#                        for (_, f), row in t_rows.iterrows())
#             <= t_rows.drive_hours.iloc[0]
#         )

#     # 3. Constraint: Each forest can't have more logs picked up than its available volume
#     for f, f_rows in df.groupby(level=1):
#         solver.Add(
#             solver.Sum(row.cbm_per_truck * var[(t, f)]
#                        for (t, _), row in f_rows.iterrows())
#             <= f_rows.weekly_stockpile_cbm.iloc[0]
#         )

#     # 4. Objective: Maximize total CBM delivered
#     total_cbm = solver.Sum(df.loc[(t, f), "cbm_per_truck"] * var[(t, f)]
#                            for (t, f) in var)
#     solver.Maximize(total_cbm)

#     # 5. Set a 10-minute (600,000 ms) time limit
#     solver.set_time_limit(600000)

#     # 6. Solve and extract the plan
#     status = solver.Solve()
#     if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
#         raise RuntimeError("CBC did not find an optimal or feasible solution within the time limit")
#     if status == pywraplp.Solver.FEASIBLE:
#         print("⚠️  Time limit reached: returning best feasible solution found.")

#     def round_down_to_half(x):
#         return math.floor(x * 2) / 2

#     def effective_trips(x):
#         frac = x - math.floor(x)
#         if frac < 0.5:
#             return math.floor(x)
#         else:
#             return math.ceil(x)

#     # Build plan DataFrame (trips planned for display)
#     plan = (
#         pd.DataFrame(
#             [
#                 (t, f, round(round_down_to_half(var[(t, f)].solution_value()), 1))
#                 for (t, f) in var
#             ],
#             columns=["truck_id", "forest_id", "trips_planned"],
#         )
#         .query("trips_planned > 0.01")
#         .sort_values(["truck_id", "forest_id"])
#         .reset_index(drop=True)
#     )

#     # Calculate effective trips and delivered CBM for each truck-forest pair
#     plan["effective_trips"] = [
#         effective_trips(var[(t, f)].solution_value()) for t, f in zip(plan["truck_id"], plan["forest_id"])
#     ]
#     # Get cbm_per_truck for each pair
#     plan["cbm_per_truck"] = [
#         df.loc[(t, f), "cbm_per_truck"] for t, f in zip(plan["truck_id"], plan["forest_id"])
#     ]
#     plan["delivered_cbm"] = plan["effective_trips"] * plan["cbm_per_truck"]

#     # Calculate total CBM delivered and total effective trips
#     total_cbm = plan["delivered_cbm"].sum()
#     total_effective_trips = plan["effective_trips"].sum()

#     # Calculate remaining volume for each forest
#     forest_delivered = plan.groupby("forest_id")["delivered_cbm"].sum()
#     forest_stock = df.reset_index().drop_duplicates("forest_id").set_index("forest_id")["weekly_stockpile_cbm"]
#     # Get max cbm_per_truck for each forest
#     cbm_per_truck_by_forest = plan.groupby("forest_id")["cbm_per_truck"].max()
#     forest_remaining = (forest_stock - forest_delivered).fillna(forest_stock)

#     print("\n---- Weekly summary (realistic) ----")
#     print(f"Total effective trips : {total_effective_trips:,.0f}")
#     print(f"Total CBM delivered   : {total_cbm:,.0f} m³")
#     print("\n---- Remaining volume by forest ----")
#     for forest, remaining in forest_remaining.items():
#         cbm_truck = cbm_per_truck_by_forest.get(forest, 0)
#         capped_remaining = max(remaining, -cbm_truck)
#         print(f"{forest}: {capped_remaining:,.0f} m³ left")

#     return plan



# int values 

#ACTUAL ONE - 

# import math
# import pandas as pd
# from ortools.linear_solver import pywraplp

# def solve_week(df: pd.DataFrame) -> pd.DataFrame:
#     solver = pywraplp.Solver.CreateSolver("CBC")

#     # Print problem size for diagnosis
#     n_trucks = df.index.get_level_values(0).nunique()
#     n_forests = df.index.get_level_values(1).nunique()
#     print(f"Number of trucks: {n_trucks}")
#     print(f"Number of forests: {n_forests}")
#     print(f"Number of variables (truck-forest pairs): {len(df)}")

#     # 1. Decision variables: x[t, f] = number of trips truck t makes to forest f (integer)
#     var = {}
#     for (t, f), row in df.iterrows():
#         # Upper bound: max trips possible for this truck to this forest (in hours), capped at 15
#         if row.trip_hours > 0:
#             phys_lim = math.floor(row.drive_hours / row.trip_hours)
#         else:
#             phys_lim = 0
#         ub = min(max(0, phys_lim), 15)
#         var[(t, f)] = solver.IntVar(0, ub, f"x_{t}_{f}")  # Integer variable

#     # 2. Constraint: Each truck can't exceed its available drive hours
#     for t, t_rows in df.groupby(level=0):
#         solver.Add(
#             solver.Sum(row.trip_hours * var[(t, f)]
#                        for (_, f), row in t_rows.iterrows())
#             <= t_rows.drive_hours.iloc[0]
#         )

#     # 3. Constraint: Each forest can't have more logs picked up than its available volume
#     for f, f_rows in df.groupby(level=1):
#         solver.Add(
#             solver.Sum(row.cbm_per_truck * var[(t, f)]
#                        for (t, _), row in f_rows.iterrows())
#             <= f_rows.weekly_stockpile_cbm.iloc[0]
#         )

#     # 4. Objective: Maximize total CBM delivered
#     total_cbm = solver.Sum(df.loc[(t, f), "cbm_per_truck"] * var[(t, f)]
#                            for (t, f) in var)
#     solver.Maximize(total_cbm)

#     # 5. Set a 10-minute (600,000 ms) time limit
#     solver.set_time_limit(3000)

#     # 6. Solve and extract the plan
#     status = solver.Solve()
#     if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
#         raise RuntimeError("CBC did not find an optimal or feasible solution within the time limit")
#     if status == pywraplp.Solver.FEASIBLE:
#         print("⚠️  Time limit reached: returning best feasible solution found.")

#     plan = (
#         pd.DataFrame(
#             [(t, f, int(var[(t, f)].solution_value())) for (t, f) in var],
#             columns=["truck_id", "forest_id", "trips_planned"],
#         )
#         .query("trips_planned > 0")
#         .sort_values(["truck_id", "forest_id"])
#         .reset_index(drop=True)
#     )
#     # Add cbm_per_truck for summary in scratch.py
#     plan["cbm_per_truck"] = [
#         df.loc[(t, f), "cbm_per_truck"] for t, f in zip(plan["truck_id"], plan["forest_id"])
#     ]
#     return plan




import math
import pandas as pd
from ortools.linear_solver import pywraplp

def solve_week(df: pd.DataFrame, maximize_profit=False) -> pd.DataFrame:
    solver = pywraplp.Solver.CreateSolver("CBC")

    n_trucks = df.index.get_level_values(0).nunique()
    n_forests = df.index.get_level_values(1).nunique()
    print(f"Number of trucks: {n_trucks}")
    print(f"Number of forests: {n_forests}")
    print(f"Number of variables (truck-forest pairs): {len(df)}")

    var = {}
    for (t, f), row in df.iterrows():
        if row.trip_hours > 0:
            phys_lim = math.floor(row.drive_hours / row.trip_hours)
        else:
            phys_lim = 0
        ub = min(max(0, phys_lim), 15)
        var[(t, f)] = solver.IntVar(0, ub, f"x_{t}_{f}")

    for t, t_rows in df.groupby(level=0):
        solver.Add(
            solver.Sum(row.trip_hours * var[(t, f)]
                       for (_, f), row in t_rows.iterrows())
            <= t_rows.drive_hours.iloc[0]
        )

    for f, f_rows in df.groupby(level=1):
        solver.Add(
            solver.Sum(row.cbm_per_truck * var[(t, f)]
                       for (t, _), row in f_rows.iterrows())
            <= f_rows.weekly_stockpile_cbm.iloc[0]
        )

    if maximize_profit:
        total_profit = solver.Sum(df.loc[(t, f), "cbm_per_truck"] * df.loc[(t, f), "profit_per_cbm_euros"] * var[(t, f)] for (t, f) in var)
        solver.Maximize(total_profit)
    else:
        total_cbm = solver.Sum(df.loc[(t, f), "cbm_per_truck"] * var[(t, f)] for (t, f) in var)
        solver.Maximize(total_cbm)

    solver.set_time_limit(5000)

    status = solver.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        raise RuntimeError("CBC did not find an optimal or feasible solution within the time limit")
    if status == pywraplp.Solver.FEASIBLE:
        print("⚠️  Time limit reached: returning best feasible solution found.")

    plan = (
        pd.DataFrame(
            [(t, f, int(var[(t, f)].solution_value())) for (t, f) in var],
            columns=["truck_id", "forest_id", "trips_planned"],
        )
        .query("trips_planned > 0")
        .sort_values(["truck_id", "forest_id"])
        .reset_index(drop=True)
    )
    plan["cbm_per_truck"] = [
        df.loc[(t, f), "cbm_per_truck"] for t, f in zip(plan["truck_id"], plan["forest_id"])
    ]
    return plan