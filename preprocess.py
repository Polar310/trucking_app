# """
# Reads the csv files in data folder, joins them into a single 
# truck-by-forest table, 
# and engineers all the parameters the optimiser needs

# output - 
# A pandas DataFrame indexed by (truck_id, forest_id) with columns: 

#     drive_days - how many days the truck is free this week 
#     trip_days - rount trip duration for that forest 
#     max_trips_wk - forest's weekly trip cap (dry / wet)
#     cbm_per_truck - cubic metres one truck can haul on that forest 
#     score - efficiency metric (cubic metre pert truck-day) = cbm_per_truck / trip_days 

# How it works - 
# reads the 2csv files 
# converts the monthly caps into weekly caps 
# computes drive_days for every truck (7 - maintenance)
# cross joints trucks x forests so every row is a (truck,forest) pair
# adds score = cbm_per_truck / trip_days 
# returns dataframe to whoever calls it (optimiser)
# """

# import math
# import pandas as pd 

# # DAILY_KM = 300          # Max km a truck can drive in a day
# # we'll be using this for now to get a rough estimate of trip_days 
# #until we can get turn around time for each forest 
# #even if we have 300KM per day for each truck then we hit max cap of 12,249 m^3 assuming all trucks functional 

# #DEFAULT_MAINT_DAYS = 0    # Default maintenance days if missing 


# def build_model_input(
#     forests_csv: str = "data/forests.csv",
#     trucks_csv: str = "data/trucks.csv",
#     season: str = "dry",
# ) -> pd.DataFrame: 
    
    
#     # 1. Read and clean CSVs
#     forests = pd.read_csv(forests_csv)
#     forests.columns = forests.columns.str.strip().str.lower()
#     trucks  = pd.read_csv(trucks_csv)
#     trucks.columns  = trucks.columns.str.strip().str.lower()

#     # Remove cbm_per_truck from forests if present
#     if "cbm_per_truck" in forests.columns:
#         forests = forests.drop(columns=["cbm_per_truck"])

#     # 2. Set trip_hours for each forest (how many hours a round trip takes)
#     season = season.lower()
#     if season == "dry":
#         forests["trip_hours"] = forests["turn_around_time_dry"]
#     else:
#         forests["trip_hours"] = forests["turn_around_time_rain"]

#     # 3. Ensure each forest has a weekly stockpile (volume to be picked up)
#     if "volume" not in forests.columns:
#         raise ValueError("Add a 'volume' column to forests.csv (weekly CBM stock-pile)")
#     forests["weekly_stockpile_cbm"] = forests["volume"]

#     # 4. Remove forests with zero stock-pile (no logs to pick up)
#     forests = forests[forests.weekly_stockpile_cbm > 0].copy()

#     # 5. Calculate drive_hours for each truck (how many hours it can work this week)
#     if "maintenance_hours" not in trucks.columns:
#         trucks["maintenance_hours"] = 0
#     if "drive_hours" not in trucks.columns:
#         trucks["drive_hours"] = 52.5  # default, e.g. 5 days * 10.5 hours
#     trucks["drive_hours"] = (trucks["drive_hours"] - trucks["maintenance_hours"]).clip(lower=0)

#     # 6. Cross-join trucks and forests (all possible assignments)
#     df = pd.merge(trucks, forests, how="cross")
#     # Each row now has truck's cbm_per_truck

#     # 7. Set a multi-index for the optimizer
#     df = df.set_index(["truck_id", "forest_id"], verify_integrity=True)
#     return df
#     #make rows and columns names to truckid and forestid, verify it's all true (no dupes)



"""
Reads the csv files in data folder, joins them into a single 
truck-by-forest table, 
and engineers all the parameters the optimiser needs

output - 
A pandas DataFrame indexed by (truck_id, forest_id) with columns: 

    drive_days - how many days the truck is free this week 
    trip_days - rount trip duration for that forest 
    max_trips_wk - forest's weekly trip cap (dry / wet)
    cbm_per_truck - cubic metres one truck can haul on that forest 
    score - efficiency metric (cubic metre pert truck-day) = cbm_per_truck / trip_days 

How it works - 
reads the 2csv files 
converts the monthly caps into weekly caps 
computes drive_days for every truck (7 - maintenance)
cross joints trucks x forests so every row is a (truck,forest) pair
adds score = cbm_per_truck / trip_days 
returns dataframe to whoever calls it (optimiser)
"""

import math
import pandas as pd 

# DAILY_KM = 300          # Max km a truck can drive in a day
# we'll be using this for now to get a rough estimate of trip_days 
#until we can get turn around time for each forest 
#even if we have 300KM per day for each truck then we hit max cap of 12,249 m^3 assuming all trucks functional 

#DEFAULT_MAINT_DAYS = 0    # Default maintenance days if missing 


def build_model_input(
    forests_csv: str = "data/forests.csv",
    trucks_csv: str = "data/trucks.csv",
    season: str = "dry",
) -> pd.DataFrame: 
    
    
    # 1. Read and clean CSVs
    forests = pd.read_csv(forests_csv)
    forests.columns = forests.columns.str.strip().str.lower()
    trucks  = pd.read_csv(trucks_csv)
    trucks.columns  = trucks.columns.str.strip().str.lower()

    # Remove cbm_per_truck from forests if present
    if "cbm_per_truck" in forests.columns:
        forests = forests.drop(columns=["cbm_per_truck"])

    # 2. Set trip_hours for each forest (how many hours a round trip takes)
    season = season.lower()
    if season == "dry":
        forests["trip_hours"] = forests["turn_around_time_dry"]
    else:
        forests["trip_hours"] = forests["turn_around_time_rain"]

    # 3. Ensure each forest has a weekly stockpile (volume to be picked up)
    if "volume" not in forests.columns:
        raise ValueError("Add a 'volume' column to forests.csv (weekly CBM stock-pile)")
    forests["weekly_stockpile_cbm"] = forests["volume"]

    # 4. Remove forests with zero stock-pile (no logs to pick up)
    forests = forests[forests.weekly_stockpile_cbm > 0].copy()

    # 5. Calculate drive_hours for each truck (how many hours it can work this week)
    if "maintenance_hours" not in trucks.columns:
        trucks["maintenance_hours"] = 0
    if "drive_hours" not in trucks.columns:
        trucks["drive_hours"] = 52.5  # default, e.g. 5 days * 10.5 hours
    trucks["drive_hours"] = (trucks["drive_hours"] - trucks["maintenance_hours"]).clip(lower=0)

    # 6. Cross-join trucks and forests (all possible assignments)
    df = pd.merge(trucks, forests, how="cross")
    # Each row now has truck's cbm_per_truck

    # 7. Set a multi-index for the optimizer
    df = df.set_index(["truck_id", "forest_id"], verify_integrity=True)
    return df
    #make rows and columns names to truckid and forestid, verify it's all true (no dupes)
