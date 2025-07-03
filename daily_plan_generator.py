import csv
from collections import defaultdict

# Read plan.csv and collect trips per truck
trips_by_truck = defaultdict(list)
with open('plan.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        truck_id = row['truck_id'].strip()
        forest_id = row['forest_id'].strip()
        trips_planned = int(row['trips_planned'])
        cbm_per_truck = row['cbm_per_truck'].strip()
        profit = row['profit'].strip()
        # Store each trip assignment as many times as trips_planned
        trips_by_truck[truck_id].append({
            'forest_id': forest_id,
            'trips_planned': trips_planned,
            'cbm_per_truck': cbm_per_truck,
            'profit': profit
        })

# Expand trips into daily assignments
expanded_trips = []
for truck_id, trips in trips_by_truck.items():
    # Calculate total trips for this truck
    total_trips = sum(trip['trips_planned'] for trip in trips)
    # Expand each trip
    for trip in trips:
        for i in range(trip['trips_planned']):
            expanded_trips.append({
                'truck_id': truck_id,
                'forest_id': trip['forest_id'],
                'cbm_per_truck': trip['cbm_per_truck'],
                'profit': trip['profit'],
                'total_trips_for_truck': total_trips
            })

# Assign day and trip_number for each truck
# Sort by truck_id, then preserve order of appearance
expanded_trips.sort(key=lambda x: int(x['truck_id']))

# For each truck, assign trip_number and day
trip_counters = defaultdict(int)
for trip in expanded_trips:
    truck_id = trip['truck_id']
    trip_counters[truck_id] += 1
    trip['trip_number'] = trip_counters[truck_id]
    trip['day'] = trip_counters[truck_id]  # 1st trip is day 1, etc.

# Write to daily_plan.csv
with open('daily_plan.csv', 'w', newline='') as csvfile:
    fieldnames = ['day', 'truck_id', 'forest_id', 'cbm_per_truck', 'profit', 'trip_number', 'total_trips_for_truck']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for trip in expanded_trips:
        writer.writerow({
            'day': trip['day'],
            'truck_id': trip['truck_id'],
            'forest_id': trip['forest_id'],
            'cbm_per_truck': trip['cbm_per_truck'],
            'profit': trip['profit'],
            'trip_number': trip['trip_number'],
            'total_trips_for_truck': trip['total_trips_for_truck']
        })

# Print the daily schedule grouped by day
def print_daily_schedule(expanded_trips):
    # Group trips by day
    trips_by_day = defaultdict(list)
    for trip in expanded_trips:
        trips_by_day[trip['day']].append(trip)
    
    for day in sorted(trips_by_day.keys(), key=int):
        print(f"Day {day}:")
        # Sort by truck_id within the day
        for trip in sorted(trips_by_day[day], key=lambda x: int(x['truck_id'])):
            print(f"  Truck {trip['truck_id']} -> {trip['forest_id']} (Trip {trip['trip_number']} of {trip['total_trips_for_truck']})")
        print()

# Call the print function at the end
print_daily_schedule(expanded_trips)

# Write a sorted CSV by day and truck_id
sorted_trips = sorted(expanded_trips, key=lambda x: (int(x['day']), int(x['truck_id'])))
with open('daily_plan_by_day.csv', 'w', newline='') as csvfile:
    fieldnames = ['day', 'truck_id', 'forest_id', 'trip_number', 'total_trips_for_truck', 'cbm_per_truck', 'profit']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for trip in sorted_trips:
        writer.writerow({
            'day': trip['day'],
            'truck_id': trip['truck_id'],
            'forest_id': trip['forest_id'],
            'trip_number': trip['trip_number'],
            'total_trips_for_truck': trip['total_trips_for_truck'],
            'cbm_per_truck': trip['cbm_per_truck'],
            'profit': trip['profit']
        })

def print_and_write_forest_daily_schedule(expanded_trips):
    from collections import defaultdict
    # Group by day, then by forest
    schedule = defaultdict(lambda: defaultdict(list))
    for trip in expanded_trips:
        day = trip['day']
        forest = trip['forest_id']
        schedule[day][forest].append(trip)

    # Print to console
    for day in sorted(schedule.keys(), key=int):
        print(f"Day {day}:")
        for forest in sorted(schedule[day].keys()):
            trucks = schedule[day][forest]
            truck_strs = [f"{t['truck_id']} ({t['trip_number']}, {t['total_trips_for_truck']})" for t in sorted(trucks, key=lambda x: int(x['truck_id']))]
            print(f"  {forest}: {', '.join(truck_strs)}")
        print()

    # Write to CSV
    with open('daily_forest_plan_by_day.csv', 'w', newline='') as csvfile:
        fieldnames = ['day', 'forest_id', 'truck_id', 'trip_number', 'total_trips_for_truck', 'cbm_per_truck', 'profit']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for day in sorted(schedule.keys(), key=int):
            for forest in sorted(schedule[day].keys()):
                for t in sorted(schedule[day][forest], key=lambda x: int(x['truck_id'])):
                    writer.writerow({
                        'day': t['day'],
                        'forest_id': t['forest_id'],
                        'truck_id': t['truck_id'],
                        'trip_number': t['trip_number'],
                        'total_trips_for_truck': t['total_trips_for_truck'],
                        'cbm_per_truck': t['cbm_per_truck'],
                        'profit': t['profit']
                    })

# Call the new function at the end
print_and_write_forest_daily_schedule(expanded_trips) 