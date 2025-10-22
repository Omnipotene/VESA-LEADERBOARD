#!/usr/bin/env python3
"""
Extract S12 Aliases from rosters_final_placements.csv
Builds Discord -> Overstat name mappings for all S12 players
"""

import csv
import json
from collections import defaultdict
import re

print("VESA S12 - Extract Aliases from Roster CSV")
print("="*70)

# Load the roster CSV
roster_file = 'data/rosters_final_placements.csv'

all_aliases = defaultdict(lambda: {
    'discord_name': None,
    'overstat_names': set(),
    'teams': set()
})

with open(roster_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    for row in reader:
        team_name = row.get('Team Name', '').strip()

        if not team_name or 'Lobby' in team_name:
            continue  # Skip header rows

        # Extract player data
        players = []

        # Player 1 (Team Captain)
        captain_discord = row.get('Team Captain Discord Username(s)', '').strip()
        if captain_discord:
            players.append({'discord': captain_discord, 'overstat_link': None})

        # Rostered Player 1
        p1_discord = row.get('Rostered Player 1 Discord Username', '').strip()
        p1_link = row.get('Rostered Player 1 Overstat Link', '').strip()
        if p1_discord:
            players.append({'discord': p1_discord, 'overstat_link': p1_link})

        # Rostered Player 2
        p2_discord = row.get('Rostered Player 2 Discord Username', '').strip()
        p2_link = row.get('Rostered Player 2 Overstat Link', '').strip()
        if p2_discord:
            players.append({'discord': p2_discord, 'overstat_link': p2_link})

        # Rostered Player 3
        p3_discord = row.get('Rostered Player 3 Discord Username', '').strip()
        p3_link = row.get('Rostered Player 3 Overstat Link', '').strip()
        if p3_discord:
            players.append({'discord': p3_discord, 'overstat_link': p3_link})

        # Process each player
        for player in players:
            discord = player['discord'].lower().strip()
            if not discord:
                continue

            # Extract Overstat name from link
            overstat_name = None
            if player['overstat_link']:
                # Format: https://overstat.gg/player/123456.PlayerName/overview
                # or: https://overstat.gg/player/123456/overview
                match = re.search(r'/player/\d+\.(.+?)(?:/|$)', player['overstat_link'])
                if match:
                    overstat_name = match.group(1).strip()
                    # URL decode common patterns
                    overstat_name = overstat_name.replace('%20', ' ')
                    overstat_name = overstat_name.replace('%2', ' ')

            all_aliases[discord]['discord_name'] = discord
            all_aliases[discord]['teams'].add(team_name)

            if overstat_name:
                all_aliases[discord]['overstat_names'].add(overstat_name)

print(f"Processed roster file: {roster_file}")
print(f"Found {len(all_aliases)} unique players")

# Convert to output format
output_aliases = []

for discord, data in all_aliases.items():
    if data['overstat_names'] or data['teams']:
        # Combine discord name with all overstat names as aliases
        aliases = [discord]  # Discord name itself is an alias
        aliases.extend(list(data['overstat_names']))

        output_aliases.append({
            'discord_name': discord,
            'aliases': sorted(list(set(aliases))),  # Deduplicate
            'teams_s12': sorted(list(data['teams']))
        })

# Sort by discord name
output_aliases.sort(key=lambda x: x['discord_name'])

# Save results
output_file = 'data/s12_aliases_from_csv.json'
with open(output_file, 'w') as f:
    json.dump(output_aliases, f, indent=2)

print(f"\n✅ Saved S12 alias data to: {output_file}")
print(f"   Total players: {len(output_aliases)}")
print(f"   Total aliases: {sum(len(p['aliases']) for p in output_aliases)}")

# Show statistics
print(f"\nAlias Statistics:")
multi_alias = [p for p in output_aliases if len(p['aliases']) > 1]
print(f"  Players with multiple names: {len(multi_alias)}")
print(f"  Average aliases per player: {sum(len(p['aliases']) for p in output_aliases) / len(output_aliases):.1f}")

# Show sample
print(f"\nSample players (first 20):")
for i, player in enumerate(output_aliases[:20], 1):
    aliases_str = ', '.join(player['aliases'][:3])
    if len(player['aliases']) > 3:
        aliases_str += f" (+{len(player['aliases'])-3} more)"
    print(f"  {i:2}. {player['discord_name']:20} → {aliases_str}")

print(f"\nNext step: Merge this data into player_aliases.json")
print("  Run: python3 merge_s12_aliases.py")
