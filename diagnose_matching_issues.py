#!/usr/bin/env python3
"""
Diagnose Player Matching Issues
Finds players who likely played multiple seasons but aren't being matched
"""

import json
from collections import defaultdict
from difflib import SequenceMatcher

def similar(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def normalize_name(name):
    """Normalize player name for comparison"""
    # Remove common prefixes/suffixes
    name = name.lower().strip()
    prefixes = ['ttv', 'twitch.tv/', '@', 'nc ', 'bf ', 'xel ', 'drip_', 'fc ', 'ttv_']
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]

    # Remove common suffixes
    suffixes = ['_tv', '_yt', ' | twitch', ' fps', 'fps']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]

    return name.strip()

print("VESA League - Player Matching Diagnostics")
print("="*70)

# Load season data
with open('output/s8_players_ranked.json', 'r') as f:
    s8_players = json.load(f)
with open('output/s11_players_ranked.json', 'r') as f:
    s11_players = json.load(f)
with open('output/s12_players_ranked_v2.json', 'r') as f:
    s12_players = json.load(f)

# Load alias data
with open('data/player_aliases.json', 'r') as f:
    aliases_data = json.load(f)

# Build name -> discord mapping
name_to_discord = {}
discord_to_names = defaultdict(set)
for player in aliases_data:
    discord = player['discord_name'].lower().strip()
    for alias in player['aliases']:
        alias_lower = alias.lower().strip()
        if alias_lower:
            name_to_discord[alias_lower] = discord
            discord_to_names[discord].add(alias)

print(f"Loaded alias database:")
print(f"  {len(aliases_data)} unique players")
print(f"  {len(name_to_discord)} total aliases")
print()

# Get player names from each season
s8_names = {p['player_name'].lower().strip() for p in s8_players}
s11_names = {p['player_name'].lower().strip() for p in s11_players}
s12_names = {p['player_name'].lower().strip() for p in s12_players}

print(f"Player names per season:")
print(f"  S8: {len(s8_names)} players")
print(f"  S11: {len(s11_names)} players")
print(f"  S12: {len(s12_names)} players")
print()

# Find names not in alias DB
s8_missing = s8_names - set(name_to_discord.keys())
s11_missing = s11_names - set(name_to_discord.keys())
s12_missing = s12_names - set(name_to_discord.keys())

print(f"Names NOT in alias database:")
print(f"  S8: {len(s8_missing)}/{len(s8_names)} ({len(s8_missing)/len(s8_names)*100:.1f}%)")
print(f"  S11: {len(s11_missing)}/{len(s11_names)} ({len(s11_missing)/len(s11_names)*100:.1f}%)")
print(f"  S12: {len(s12_missing)}/{len(s12_names)} ({len(s12_missing)/len(s12_names)*100:.1f}%)")
print()

# Find potential matches using fuzzy matching
print("="*70)
print("FUZZY MATCHING ANALYSIS - Finding Likely Missed Connections")
print("="*70)

# Top S12 players without S11/S8 matches
s12_high_value = [p for p in s12_players if p['final_score'] > 100]
print(f"\nAnalyzing {len(s12_high_value)} high-value S12 players (score > 100)...")

potential_matches = []

for s12_player in s12_high_value:
    s12_name = s12_player['player_name'].lower().strip()

    # Skip if already in alias DB
    if s12_name in name_to_discord:
        continue

    s12_normalized = normalize_name(s12_name)

    # Check against S11 players
    for s11_player in s11_players:
        s11_name = s11_player['player_name'].lower().strip()
        s11_normalized = normalize_name(s11_name)

        # Calculate similarity
        similarity = similar(s12_normalized, s11_normalized)

        if similarity >= 0.7:  # 70% similar
            potential_matches.append({
                's12_name': s12_player['player_name'],
                's12_score': s12_player['final_score'],
                's11_name': s11_player['player_name'],
                's11_score': s11_player['final_score'],
                'similarity': similarity,
                'seasons': 'S11+S12'
            })

    # Check against S8 players
    for s8_player in s8_players:
        s8_name = s8_player['player_name'].lower().strip()
        s8_normalized = normalize_name(s8_name)

        similarity = similar(s12_normalized, s8_normalized)

        if similarity >= 0.7:
            potential_matches.append({
                's12_name': s12_player['player_name'],
                's12_score': s12_player['final_score'],
                's8_name': s8_player['player_name'],
                's8_score': s8_player['final_score'],
                'similarity': similarity,
                'seasons': 'S8+S12'
            })

# Sort by similarity
potential_matches.sort(key=lambda x: x['similarity'], reverse=True)

print(f"\nFound {len(potential_matches)} potential missed matches (70%+ similarity)")
print("\nTOP 50 LIKELY MATCHES:")
print("-"*70)

for i, match in enumerate(potential_matches[:50], 1):
    if 'S11' in match['seasons']:
        print(f"{i:2}. {match['s12_name'][:30]:30} (S12: {match['s12_score']:6.1f}) ≈ "
              f"{match['s11_name'][:30]:30} (S11: {match['s11_score']:6.1f}) "
              f"[{match['similarity']*100:.0f}% match]")
    else:
        print(f"{i:2}. {match['s12_name'][:30]:30} (S12: {match['s12_score']:6.1f}) ≈ "
              f"{match['s8_name'][:30]:30} (S8: {match['s8_score']:6.1f}) "
              f"[{match['similarity']*100:.0f}% match]")

# Save full report
output_file = 'output/matching_diagnostics.json'
with open(output_file, 'w') as f:
    json.dump({
        'summary': {
            'total_aliases': len(name_to_discord),
            's8_missing': len(s8_missing),
            's11_missing': len(s11_missing),
            's12_missing': len(s12_missing),
            'potential_matches': len(potential_matches)
        },
        'missing_names': {
            's8': list(s8_missing)[:100],
            's11': list(s11_missing)[:100],
            's12': list(s12_missing)[:100]
        },
        'potential_matches': potential_matches
    }, f, indent=2)

print(f"\n{'='*70}")
print(f"✅ Full diagnostic report saved to: {output_file}")
print()
print("NEXT STEPS:")
print("1. Review potential matches above")
print("2. Manually verify high-confidence matches (90%+)")
print("3. Add verified matches to player_aliases.json")
print("4. Re-scrape rosters to capture more aliases automatically")
print("5. Implement fuzzy matching fallback in the main pipeline")
