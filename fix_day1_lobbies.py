#!/usr/bin/env python3
"""
Fix Day 1 Lobby Mappings
Day 1 had different lobby structure - remap to standard .5 lobbies
"""

import json

print("Fixing Day 1 Lobby Mappings")
print("="*70)

# Load raw data
with open('output/s12_placements_raw.json', 'r') as f:
    data = json.load(f)

print(f"Loaded {len(data)} entries")

# Remap Day 1 lobbies
# Day 1: 3 → 3.5, 5 → 5.5
remapped_count = 0

for entry in data:
    if entry.get('day') == 1:
        lobby = str(entry.get('lobby', ''))

        if lobby == '3':
            entry['lobby'] = '3.5'
            remapped_count += 1
        elif lobby == '5':
            entry['lobby'] = '5.5'
            remapped_count += 1

print(f"Remapped {remapped_count} Day 1 lobby entries")

# Save updated data
with open('output/s12_placements_raw.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"\n{'='*70}")
print("✅ Day 1 lobbies remapped:")
print("  3 → 3.5")
print("  5 → 5.5")
print("="*70)

# Show new distribution
from collections import defaultdict

by_day = defaultdict(set)
for entry in data:
    day = entry.get('day', 0)
    lobby = str(entry.get('lobby', ''))
    if lobby:
        by_day[day].add(lobby)

print("\nNew lobby structure by day:")
for day in sorted(by_day.keys()):
    lobbies = sorted(by_day[day], key=lambda x: float(x) if x.replace('.','').isdigit() else 999)
    print(f"  Day {day}: {lobbies}")
