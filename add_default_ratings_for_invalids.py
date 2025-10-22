#!/usr/bin/env python3
"""
Add default ratings for players with invalid/missing Overstat links
Based on their rank and experience from the signup form
"""

import csv
import json

print("VESA League - Add Default Ratings for Players Without Overstat")
print("="*70)

# Load invalid URLs list
with open('output/invalid_overstat_urls.json', 'r') as f:
    invalid_players = json.load(f)

print(f"Loaded {len(invalid_players)} players with invalid/missing Overstat links")

# Load roster to get rank/experience data
roster_data = {}
with open('data/rosters.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        team_name = row.get('Team Name', '').strip()

        if not team_name or 'Lobby' in team_name:
            continue

        # Store team info
        roster_data[team_name] = {
            'avg_rank': row.get('What is the average rank of your team?', '').strip(),
            'familiarity': row.get('How familiar is your team with competitive apex?', '').strip(),
            'vesa_experience': row.get('Have you and your teammates played in Void Apex leagues before? (this does not include scrims/community events)', '').strip()
        }

# Default rating tiers based on rank (ADJUSTED to match competitive reality)
# Note: Apex ranked performance != competitive tournament performance
# These values are conservative estimates to avoid inflating unproven players
RANK_TO_RATING = {
    'Apex Predator': 120,  # Could be good, but need tournament data to prove it
    'Masters': 100,
    'Diamond': 80,         # Default baseline - most players without data
    'Platinum': 70,
    'Gold': 60,
    'Silver': 50,
    'Bronze': 40,
    'Rookie': 40
}

# Modifiers based on experience (minimal impact - we need data, not claims)
FAMILIARITY_MODIFIER = {
    '5': 1.0,   # Very familiar - still need to prove it
    '4': 1.0,
    '3': 1.0,   # Neutral
    '2': 1.0,
    '1': 1.0    # Not familiar
}

VESA_EXPERIENCE_MODIFIER = {
    'Yes, all 3 did': 1.0,
    '2 of us did, 1 did not': 1.0,
    '1 of us did, 2 did not': 1.0,
    'None of  played in the VESA Apex League Season 11': 1.0
}

# Calculate ratings for invalid players
default_ratings = []

for player in invalid_players:
    team = player['team']
    discord_name = player['discord_name']

    # Get team info
    team_info = roster_data.get(team, {})
    avg_rank = team_info.get('avg_rank', 'Diamond')  # Default to Diamond
    familiarity = team_info.get('familiarity', '3')
    vesa_exp = team_info.get('vesa_experience', 'None of  played in the VESA Apex League Season 11')

    # Calculate base rating from rank
    base_rating = RANK_TO_RATING.get(avg_rank, 80)  # Default 80 if unknown (Diamond baseline)

    # Apply modifiers
    familiarity_mult = FAMILIARITY_MODIFIER.get(familiarity, 1.0)
    vesa_mult = VESA_EXPERIENCE_MODIFIER.get(vesa_exp, 0.95)

    final_rating = base_rating * familiarity_mult * vesa_mult

    default_ratings.append({
        'team': team,
        'discord_name': discord_name,
        'rating': round(final_rating, 2),
        'rank': avg_rank,
        'familiarity': familiarity,
        'vesa_experience': vesa_exp,
        'reason': 'Invalid/missing Overstat link'
    })

# Display the assigned ratings
print(f"\nAssigned default ratings for {len(default_ratings)} players:")
print("="*70)
print(f"{'Player':<30} {'Team':<25} {'Rating':<10} {'Rank'}")
print("-"*70)

for entry in default_ratings:
    print(f"{entry['discord_name']:<30} {entry['team'][:24]:<25} {entry['rating']:<10} {entry['rank']}")

# Save to file
output_file = 'output/default_ratings_for_invalids.json'
with open(output_file, 'w') as f:
    json.dump(default_ratings, f, indent=2)

print(f"\n{'='*70}")
print(f"✅ Default ratings assigned and saved to: {output_file}")

# Now add these to the combined ratings file
print(f"\nMerging with existing combined ratings...")

with open('output/combined_s11_s12_ratings.json', 'r') as f:
    combined_ratings = json.load(f)

print(f"Loaded {len(combined_ratings)} existing players")

# Add the new default-rated players
for entry in default_ratings:
    # Check if player already exists (shouldn't, but just in case)
    player_name_lower = entry['discord_name'].lower().strip()

    # Check if exists
    exists = False
    for existing in combined_ratings:
        if existing['player_name'].lower().strip() == player_name_lower:
            exists = True
            break

    if not exists:
        combined_ratings.append({
            'canonical_id': player_name_lower,
            'player_name': entry['discord_name'],
            'combined_rating': entry['rating'],
            's12_rating': None,
            's11_rating': None,
            'seasons_played': 'New (estimated)',
            'rank': len(combined_ratings) + 1
        })

# Re-sort by rating
combined_ratings_sorted = sorted(combined_ratings, key=lambda x: x['combined_rating'], reverse=True)

# Re-assign ranks
for i, player in enumerate(combined_ratings_sorted, 1):
    player['rank'] = i

# Save updated combined ratings
with open('output/combined_s11_s12_ratings.json', 'w') as f:
    json.dump(combined_ratings_sorted, f, indent=2)

print(f"✅ Added {len(default_ratings)} new players to combined ratings")
print(f"Total players now: {len(combined_ratings_sorted)}")

# Show rating distribution
print(f"\nRating distribution for new players:")
rating_ranges = {
    '300-400': 0,
    '250-299': 0,
    '200-249': 0,
    '150-199': 0,
    '<150': 0
}

for entry in default_ratings:
    rating = entry['rating']
    if rating >= 300:
        rating_ranges['300-400'] += 1
    elif rating >= 250:
        rating_ranges['250-299'] += 1
    elif rating >= 200:
        rating_ranges['200-249'] += 1
    elif rating >= 150:
        rating_ranges['150-199'] += 1
    else:
        rating_ranges['<150'] += 1

for range_name, count in rating_ranges.items():
    print(f"  {range_name}: {count} players")

print(f"\n{'='*70}")
print("✅ COMPLETE - Ready to re-run team seeding")
print("  python3 team_seeding_combined.py")
