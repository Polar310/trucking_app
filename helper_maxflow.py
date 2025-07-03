# import networkx as nx
# import pandas as pd

# def top_up_with_flow(idle_df: pd.DataFrame,
#                      forests_df: pd.DataFrame) -> list[dict]:
#     """
#     Parameters
#     ----------
#     idle_df       columns = truck_id, available_hours, type
#     forests_df    columns = forest_id, turnaround_time, cbm_per_truck, volume_left

#     Returns
#     -------
#     assignments   list of dicts with keys:
#                   truck_id, forest_id, trips, cbm_collected, hours_used
#     """
#     print("Idle trucks for max-flow:", len(idle_df))
#     print("Forests with leftover volume:", len(forests_df))
#     print(idle_df)
#     print(forests_df)

#     G = nx.DiGraph()
#     G.add_node("S"); G.add_node("T")

#     # source → truck
#     for _, t in idle_df.iterrows():
#         max_trips_anywhere = int(t.available_hours // forests_df.turnaround_time.min())
#         if max_trips_anywhere:
#             G.add_edge("S", t.truck_id, capacity=max_trips_anywhere)

#     # forest → sink
#     for _, f in forests_df.iterrows():
#         trips_left = int(f.volume_left // f.cbm_per_truck)
#         if trips_left:
#             G.add_edge(f.forest_id, "T", capacity=trips_left)

#     # truck → forest edges
#     for _, t in idle_df.iterrows():
#         for _, f in forests_df.iterrows():
#             trips_cap = int(min(
#                 t.available_hours // f.turnaround_time,
#                 f.volume_left // f.cbm_per_truck))
#             if trips_cap:
#                 G.add_edge(t.truck_id, f.forest_id,
#                            capacity=trips_cap,
#                            weight=-f.cbm_per_truck)   # maximise CBM

#     flow = nx.max_flow_min_cost(G, "S", "T")

#     # ------------------ decode ------------------
#     assignments = []
#     for t in idle_df.truck_id:
#         if t not in flow: continue
#         for f, trips in flow[t].items():
#             if trips:
#                 forest_row = forests_df.set_index('forest_id').loc[f]
#                 cbm = trips * forest_row.cbm_per_truck
#                 assignments.append(dict(
#                     truck_id=t,
#                     forest_id=f,
#                     trips=int(trips),
#                     cbm_collected=cbm,
#                     hours_used=trips * forest_row.turnaround_time
#                 ))
#     return assignments

# def half_trip_maxflow(idle_df: pd.DataFrame, forests_df: pd.DataFrame) -> list[dict]:
#     """
#     Assigns 'half-trips' from idle trucks to forests with leftover volume.
#     Each truck-forest pair is eligible if:
#       - available_hours >= turnaround_time / 2
#       - volume_left >= cbm_per_truck / 2

#     Returns a list of assignments:
#       - truck_id, forest_id, trips (always 0.5), cbm_collected, hours_used
#     """
#     G = nx.DiGraph()
#     G.add_node("S")
#     G.add_node("T")

#     # Source → truck (each truck can do at most one half-trip)
#     for _, t in idle_df.iterrows():
#         if t.available_hours > 0:
#             G.add_edge("S", t.truck_id, capacity=1)

#     # Forest → sink (each forest can accept as many half-trips as it has volume for)
#     for _, f in forests_df.iterrows():
#         max_half_trips = int(f.volume_left // (f.cbm_per_truck / 2))
#         if max_half_trips > 0:
#             G.add_edge(f.forest_id, "T", capacity=max_half_trips)

#     # Truck → forest (only if both half-trip constraints are met)
#     for _, t in idle_df.iterrows():
#         for _, f in forests_df.iterrows():
#             if (
#                 t.available_hours >= f.turnaround_time / 2
#                 and f.volume_left >= f.cbm_per_truck / 2
#             ):
#                 G.add_edge(
#                     t.truck_id,
#                     f.forest_id,
#                     capacity=1,  # Only one half-trip per truck-forest pair
#                     weight=-f.cbm_per_truck / 2,  # maximize CBM
#                 )

#     flow = nx.max_flow_min_cost(G, "S", "T")

#     # Decode assignments
#     assignments = []
#     for t in idle_df.truck_id:
#         if t not in flow:
#             continue
#         for f, trips in flow[t].items():
#             if trips:
#                 forest_row = forests_df.set_index('forest_id').loc[f]
#                 cbm = 0.5 * forest_row.cbm_per_truck
#                 assignments.append(dict(
#                     truck_id=t,
#                     forest_id=f,
#                     trips=0.5,
#                     cbm_collected=cbm,
#                     hours_used=forest_row.turnaround_time / 2
#                 ))
#     return assignments 




import networkx as nx
import pandas as pd

def top_up_with_flow(idle_df: pd.DataFrame,
                     forests_df: pd.DataFrame) -> list[dict]:
    """
    Parameters
    ----------
    idle_df       columns = truck_id, available_hours, type
    forests_df    columns = forest_id, turnaround_time, cbm_per_truck, volume_left

    Returns
    -------
    assignments   list of dicts with keys:
                  truck_id, forest_id, trips, cbm_collected, hours_used
    """
    print("Idle trucks for max-flow:", len(idle_df))
    print("Forests with leftover volume:", len(forests_df))
    print(idle_df)
    print(forests_df)

    G = nx.DiGraph()
    G.add_node("S"); G.add_node("T")

    # source → truck
    for _, t in idle_df.iterrows():
        max_trips_anywhere = int(t.available_hours // forests_df.turnaround_time.min())
        if max_trips_anywhere:
            G.add_edge("S", t.truck_id, capacity=max_trips_anywhere)

    # forest → sink
    for _, f in forests_df.iterrows():
        trips_left = int(f.volume_left // f.cbm_per_truck)
        if trips_left:
            G.add_edge(f.forest_id, "T", capacity=trips_left)

    # Ensure profit_per_trip is in forests_df
    if 'profit_per_cbm_euros' in forests_df.columns:
        forests_df['profit_per_trip'] = forests_df['cbm_per_truck'] * forests_df['profit_per_cbm_euros']
    else:
        forests_df['profit_per_trip'] = 0
    # truck → forest edges
    for _, t in idle_df.iterrows():
        for _, f in forests_df.iterrows():
            trips_cap = int(min(
                t.available_hours // f.turnaround_time,
                f.volume_left // f.cbm_per_truck))
            if trips_cap:
                G.add_edge(t.truck_id, f.forest_id,
                           capacity=trips_cap,
                           weight=-f.profit_per_trip)   # maximise profit

    flow = nx.max_flow_min_cost(G, "S", "T")

    # ------------------ decode ------------------
    assignments = []
    for t in idle_df.truck_id:
        if t not in flow: continue
        for f, trips in flow[t].items():
            if trips:
                forest_row = forests_df.set_index('forest_id').loc[f]
                cbm = trips * forest_row.cbm_per_truck
                assignments.append(dict(
                    truck_id=t,
                    forest_id=f,
                    trips=int(trips),
                    cbm_collected=cbm,
                    hours_used=trips * forest_row.turnaround_time
                ))
    return assignments

def half_trip_maxflow(idle_df: pd.DataFrame, forests_df: pd.DataFrame) -> list[dict]:
    """
    Assigns 'half-trips' from idle trucks to forests with leftover volume.
    Each truck-forest pair is eligible if:
      - available_hours >= turnaround_time / 2
      - volume_left >= cbm_per_truck / 2

    Returns a list of assignments:
      - truck_id, forest_id, trips (always 0.5), cbm_collected, hours_used
    """
    G = nx.DiGraph()
    G.add_node("S")
    G.add_node("T")

    # Source → truck (each truck can do at most one half-trip)
    for _, t in idle_df.iterrows():
        if t.available_hours > 0:
            G.add_edge("S", t.truck_id, capacity=1)

    # Forest → sink (each forest can accept as many half-trips as it has volume for)
    for _, f in forests_df.iterrows():
        max_half_trips = int(f.volume_left // (f.cbm_per_truck / 2))
        if max_half_trips > 0:
            G.add_edge(f.forest_id, "T", capacity=max_half_trips)

    # Truck → forest (only if both half-trip constraints are met)
    for _, t in idle_df.iterrows():
        for _, f in forests_df.iterrows():
            if (
                t.available_hours >= f.turnaround_time / 2
                and f.volume_left >= f.cbm_per_truck / 2
            ):
                G.add_edge(
                    t.truck_id,
                    f.forest_id,
                    capacity=1,  # Only one half-trip per truck-forest pair
                    weight=-f.cbm_per_truck / 2,  # maximize CBM
                )

    flow = nx.max_flow_min_cost(G, "S", "T")

    # Decode assignments
    assignments = []
    for t in idle_df.truck_id:
        if t not in flow:
            continue
        for f, trips in flow[t].items():
            if trips:
                forest_row = forests_df.set_index('forest_id').loc[f]
                cbm = 0.5 * forest_row.cbm_per_truck
                assignments.append(dict(
                    truck_id=t,
                    forest_id=f,
                    trips=0.5,
                    cbm_collected=cbm,
                    hours_used=forest_row.turnaround_time / 2
                ))
    return assignments 