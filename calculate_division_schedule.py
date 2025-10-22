#!/usr/bin/env python3
"""
VESA League - Division Time Slot Scheduler
Schedules 7 divisions within 12 PM - 9 PM window with 3-hour spacing for adjacent divisions
"""

print("VESA League - Division Time Slot Scheduler")
print("="*70)

# Constraint: Adjacent divisions must be 3+ hours apart
# Non-adjacent divisions CAN play at the same time

# Time window: 12 PM to 9 PM (9 hours total)
# 3-hour spacing requirement for adjacent divisions

# Optimal solution: Group non-adjacent divisions together
# Division pairs: (1,2), (2,3), (3,4), (4,5), (5,6), (6,7) are adjacent

# Strategy: Use graph coloring with minimum colors
# Divisions that are NOT adjacent to each other can share a time slot

# Group 1: Divisions 1, 3, 5, 7 (no two are adjacent)
# Group 2: Divisions 2, 4, 6 (no two are adjacent)

time_slots = {
    "12:00 PM": [1, 3, 5, 7],
    "3:00 PM": [2, 4, 6]
}

print("\nOPTIMAL SCHEDULE:")
print("-"*70)
print("\nTime Slot      Divisions Playing")
print("-"*70)

for time, divisions in time_slots.items():
    div_str = ", ".join([f"Division {d}" for d in divisions])
    print(f"{time:<14} {div_str}")

# Load current division assignments to show with days
print("\n\nFULL SCHEDULE BY DAY:")
print("="*70)

import json

with open('output/division_assignments.json', 'r') as f:
    div_data = json.load(f)

# Group by day
by_day = {}
for div_num, data in div_data['divisions'].items():
    day = data['day']
    if day not in by_day:
        by_day[day] = []
    by_day[day].append(int(div_num))

# Assign time slots to each division
div_to_time = {}
for time, divisions in time_slots.items():
    for div in divisions:
        div_to_time[div] = time

# Show schedule by day
for day in sorted(by_day.keys()):
    divisions = sorted(by_day[day])
    print(f"\n{day.upper()}:")
    print("-"*70)

    for div_num in divisions:
        time = div_to_time[div_num]
        num_teams = len(div_data['divisions'][str(div_num)]['teams'])
        print(f"  {time:<14} Division {div_num} ({num_teams} teams)")

# Verify constraints
print("\n\nCONSTRAINT VERIFICATION:")
print("="*70)

time_to_hour = {
    "12:00 PM": 12,
    "3:00 PM": 15,
}

all_valid = True
for div in range(1, 7):  # Check divisions 1-6 against their next division
    next_div = div + 1

    time1 = div_to_time[div]
    time2 = div_to_time[next_div]

    hour1 = time_to_hour[time1]
    hour2 = time_to_hour[time2]

    diff = abs(hour2 - hour1)

    status = "✅ VALID" if diff >= 3 else "❌ INVALID"
    if diff < 3:
        all_valid = False

    print(f"Division {div} ({time1}) vs Division {next_div} ({time2}): {diff} hours apart - {status}")

print("\n" + "="*70)
if all_valid:
    print("✅ ALL CONSTRAINTS SATISFIED!")
    print("\nSummary:")
    print("  - Only 2 time slots needed (12 PM and 3 PM)")
    print("  - All adjacent divisions are 3+ hours apart")
    print("  - Maximizes concurrent play (up to 4 divisions at once)")
else:
    print("❌ CONSTRAINT VIOLATIONS DETECTED")

print("\n" + "="*70)
