#!/usr/bin/env python3
"""
VESA League Rating System - Web Dashboard
Streamlit app for viewing and managing team divisions and ratings
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict
import json

# Page config
st.set_page_config(
    page_title="VESA League S12",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for gaming theme
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }
    .stMetric {
        background-color: #1E2128;
        padding: 10px;
        border-radius: 5px;
    }
    h1, h2, h3 {
        color: #FFD700;
    }
    .tier-sp { color: #FFD700; font-weight: bold; }
    .tier-s { color: #C0C0C0; font-weight: bold; }
    .tier-a { color: #CD7F32; font-weight: bold; }
    .rank-up { color: #32CD32; }
    .rank-down { color: #FF6347; }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_database_connection():
    """Connect to SQLite database"""
    return sqlite3.connect('vesa_league.db', check_same_thread=False)

# Load data functions
@st.cache_data(ttl=300)
def load_divisions():
    """Load division assignments from database"""
    conn = get_database_connection()
    query = """
        SELECT
            d.division_number,
            d.division_day,
            t.team_name,
            t.team_rating,
            t.tier,
            t.schedule_constraint,
            da.rank_in_division
        FROM division_assignments da
        JOIN divisions d ON da.division_id = d.division_id
        JOIN teams t ON da.team_id = t.team_id
        WHERE d.season_id = (SELECT season_id FROM seasons WHERE season_name = 'S12')
        ORDER BY d.division_number, da.rank_in_division
    """
    df = pd.read_sql_query(query, conn)
    return df

@st.cache_data(ttl=300)
def load_teams():
    """Load all teams with ratings"""
    conn = get_database_connection()
    query = """
        SELECT
            t.team_id,
            t.team_name,
            t.team_rating,
            t.tier,
            t.schedule_constraint
        FROM teams t
        WHERE t.season_id = (SELECT season_id FROM seasons WHERE season_name = 'S12')
        ORDER BY t.team_rating DESC
    """
    df = pd.read_sql_query(query, conn)
    return df

@st.cache_data(ttl=300)
def load_players():
    """Load all players with ratings"""
    conn = get_database_connection()
    query = """
        SELECT
            p.player_id,
            p.canonical_name,
            p.discord_name,
            pr.total_rating,
            pr.base_rating,
            pr.lobby_bonus_total,
            pr.rank
        FROM players p
        JOIN player_ratings pr ON p.player_id = pr.player_id
        WHERE pr.season_id = (SELECT season_id FROM seasons WHERE season_name = 'S12')
        ORDER BY pr.total_rating DESC
    """
    df = pd.read_sql_query(query, conn)
    return df

@st.cache_data(ttl=300)
def load_team_rosters():
    """Load team rosters"""
    conn = get_database_connection()
    query = """
        SELECT
            t.team_name,
            p.discord_name,
            pr.total_rating as player_rating,
            tr.position
        FROM team_rosters tr
        JOIN teams t ON tr.team_id = t.team_id
        JOIN players p ON tr.player_id = p.player_id
        JOIN player_ratings pr ON p.player_id = pr.player_id
        WHERE t.season_id = (SELECT season_id FROM seasons WHERE season_name = 'S12')
          AND pr.season_id = (SELECT season_id FROM seasons WHERE season_name = 'S12')
        ORDER BY t.team_name, tr.position
    """
    df = pd.read_sql_query(query, conn)
    return df

@st.cache_data(ttl=300)
def get_database_stats():
    """Get overall database statistics"""
    conn = get_database_connection()
    stats = {}

    # Total teams
    stats['total_teams'] = pd.read_sql_query(
        "SELECT COUNT(*) as cnt FROM teams WHERE season_id = (SELECT season_id FROM seasons WHERE season_name = 'S12')",
        conn
    )['cnt'][0]

    # Total players
    stats['total_players'] = pd.read_sql_query(
        "SELECT COUNT(*) as cnt FROM player_ratings WHERE season_id = (SELECT season_id FROM seasons WHERE season_name = 'S12')",
        conn
    )['cnt'][0]

    # Total divisions
    stats['total_divisions'] = pd.read_sql_query(
        "SELECT COUNT(DISTINCT division_number) as cnt FROM divisions WHERE season_id = (SELECT season_id FROM seasons WHERE season_name = 'S12')",
        conn
    )['cnt'][0]

    # Average rating
    stats['avg_rating'] = pd.read_sql_query(
        "SELECT AVG(team_rating) as avg FROM teams WHERE season_id = (SELECT season_id FROM seasons WHERE season_name = 'S12')",
        conn
    )['avg'][0]

    return stats

@st.cache_data(ttl=300)
def load_player_lobby_performances():
    """Load raw player lobby performances for recalculation"""
    conn = get_database_connection()
    query = """
        SELECT
            plp.player_id,
            p.discord_name,
            plp.season_id,
            plp.day_number,
            plp.lobby_number,
            plp.score,
            plp.kills
        FROM player_lobby_performances plp
        JOIN players p ON plp.player_id = p.player_id
        WHERE plp.season_id IN (
            (SELECT season_id FROM seasons WHERE season_name = 'S12'),
            (SELECT season_id FROM seasons WHERE season_name = 'S11')
        )
        ORDER BY plp.player_id, plp.season_id, plp.day_number
    """
    df = pd.read_sql_query(query, conn)
    return df

def recalculate_player_ratings(lobby_performances_df, lobby_bonuses, season_weights):
    """Recalculate player ratings with new lobby bonuses and season weights"""
    # Group by player and season
    player_ratings = []

    for (player_id, discord_name, season_id), group in lobby_performances_df.groupby(['player_id', 'discord_name', 'season_id']):
        # Calculate base rating (average per day)
        days_played = group['day_number'].nunique()
        total_score = group['score'].sum() + group['kills'].sum()
        base_rating = total_score / days_played if days_played > 0 else 0

        # Calculate lobby bonus
        lobby_bonus_total = 0.0
        for _, row in group.iterrows():
            # Format lobby number to match dictionary keys (remove .0 if integer)
            lobby_val = float(row['lobby_number'])
            # Check if it's a whole number (e.g., 1.0, 2.0, 3.0)
            if lobby_val.is_integer():
                lobby_num = str(int(lobby_val))
            else:
                lobby_num = str(lobby_val)

            if lobby_num in lobby_bonuses:
                lobby_bonus_total += lobby_bonuses[lobby_num] / 100.0  # Convert percentage to decimal

        # Apply lobby bonus to base rating
        final_rating = base_rating * (1 + lobby_bonus_total)

        player_ratings.append({
            'player_id': player_id,
            'discord_name': discord_name,
            'season_id': season_id,
            'base_rating': base_rating,
            'lobby_bonus_total': lobby_bonus_total,
            'season_rating': final_rating,
            'days_played': days_played
        })

    ratings_df = pd.DataFrame(player_ratings)

    # Combine S12 and S11 ratings with weights
    # S12 = season_id 2, S11 = season_id 1 (from seasons table)
    s12_season_id = lobby_performances_df[lobby_performances_df['season_id'].isin([2])]['season_id'].iloc[0] if len(lobby_performances_df[lobby_performances_df['season_id'].isin([2])]) > 0 else 2
    s11_season_id = lobby_performances_df[lobby_performances_df['season_id'].isin([1])]['season_id'].iloc[0] if len(lobby_performances_df[lobby_performances_df['season_id'].isin([1])]) > 0 else 1

    # Pivot to get S12 and S11 ratings side by side
    combined_ratings = []
    for player_id in ratings_df['player_id'].unique():
        player_data = ratings_df[ratings_df['player_id'] == player_id]
        discord_name = player_data['discord_name'].iloc[0]

        s12_rating = player_data[player_data['season_id'] == s12_season_id]['season_rating'].iloc[0] if len(player_data[player_data['season_id'] == s12_season_id]) > 0 else 0
        s11_rating = player_data[player_data['season_id'] == s11_season_id]['season_rating'].iloc[0] if len(player_data[player_data['season_id'] == s11_season_id]) > 0 else 0

        # Apply season weights
        final_rating = (s12_rating * season_weights['S12'] / 100.0) + (s11_rating * season_weights['S11'] / 100.0)

        combined_ratings.append({
            'player_id': player_id,
            'discord_name': discord_name,
            'total_rating': final_rating,
            's12_rating': s12_rating,
            's11_rating': s11_rating
        })

    return pd.DataFrame(combined_ratings)

# Helper functions
def get_tier_color(tier):
    """Get color for tier"""
    tier_colors = {
        'S+': '#FFD700',
        'S': '#C0C0C0',
        'A+': '#CD7F32',
        'A': '#4169E1',
        'B+': '#32CD32',
        'B': '#228B22',
        'C+': '#FFA500',
        'C': '#FF8C00',
        'C-': '#FF6347',
        'D+': '#DC143C',
        'D': '#8B0000',
        'D-': '#800000'
    }
    return tier_colors.get(tier, '#FFFFFF')

def format_rank_change(change):
    """Format rank change with arrow"""
    if change > 0:
        return f'<span class="rank-up">↑{change}</span>'
    elif change < 0:
        return f'<span class="rank-down">↓{abs(change)}</span>'
    else:
        return '<span>=</span>'

# Main app
def main():
    st.title("🎮 VESA League S12 - Division Dashboard")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["📊 Dashboard", "🎯 Divisions", "👥 Teams", "🎮 Player Search", "📈 Analytics", "⚙️ Settings"]
    )

    # Load data
    divisions_df = load_divisions()
    teams_df = load_teams()
    players_df = load_players()
    rosters_df = load_team_rosters()
    stats = get_database_stats()

    # Dashboard page
    if page == "📊 Dashboard":
        st.header("Season Overview")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Teams", stats['total_teams'])
        with col2:
            st.metric("Total Players", stats['total_players'])
        with col3:
            st.metric("Divisions", stats['total_divisions'])
        with col4:
            st.metric("Avg Team Rating", f"{stats['avg_rating']:,.0f}")

        st.divider()

        # Tier distribution
        st.subheader("Tier Distribution")
        # Define tier order from highest to lowest
        tier_order = ['S+', 'S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'C-', 'D+', 'D', 'D-']

        # Get tier counts and reorder them properly
        tier_counts_series = teams_df['tier'].value_counts()
        tier_counts_series = tier_counts_series.reindex(tier_order, fill_value=0)
        tier_counts_series = tier_counts_series[tier_counts_series > 0]

        # Convert to dataframe for plotly
        tier_counts = tier_counts_series.reset_index()
        tier_counts.columns = ['tier', 'count']

        fig = px.bar(
            tier_counts,
            x='tier',
            y='count',
            title="Teams by Tier",
            color='tier',
            color_discrete_map={tier: get_tier_color(tier) for tier in tier_counts['tier']}
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Division overview
        st.subheader("Division Overview")
        div_stats = divisions_df.groupby('division_number').agg({
            'team_rating': ['count', 'mean', 'min', 'max'],
            'division_day': 'first'
        }).reset_index()
        div_stats.columns = ['Division', 'Teams', 'Avg Rating', 'Min Rating', 'Max Rating', 'Day']

        st.dataframe(
            div_stats.style.format({
                'Avg Rating': '{:,.2f}',
                'Min Rating': '{:,.2f}',
                'Max Rating': '{:,.2f}'
            }),
            use_container_width=True,
            hide_index=True
        )

    # Divisions page
    elif page == "🎯 Divisions":
        st.header("Division Assignments")

        # Division selector
        selected_div = st.selectbox(
            "Select Division",
            options=sorted(divisions_df['division_number'].unique()),
            format_func=lambda x: f"Division {x}"
        )

        # Filter for selected division
        div_teams = divisions_df[divisions_df['division_number'] == selected_div].copy()
        div_day = div_teams['division_day'].iloc[0]

        st.subheader(f"Division {selected_div} - {div_day}")
        st.caption(f"{len(div_teams)} teams | Avg Rating: {div_teams['team_rating'].mean():,.2f}")

        # Display teams
        display_cols = ['rank_in_division', 'team_name', 'team_rating', 'tier']
        div_teams_display = div_teams[display_cols].copy()
        div_teams_display.columns = ['Rank', 'Team', 'Rating', 'Tier']

        st.dataframe(
            div_teams_display.style.format({'Rating': '{:,.2f}'}),
            use_container_width=True,
            hide_index=True,
            height=600
        )

        # Export button
        if st.button("📥 Export Division to CSV"):
            csv = div_teams_display.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"division_{selected_div}_{div_day}.csv",
                mime="text/csv"
            )

    # Teams page
    elif page == "👥 Teams":
        st.header("Team Browser")

        # Search box
        search_term = st.text_input("🔍 Search teams", "")

        # Filter teams
        if search_term:
            filtered_teams = teams_df[teams_df['team_name'].str.contains(search_term, case=False, na=False)]
        else:
            filtered_teams = teams_df

        st.caption(f"Showing {len(filtered_teams)} teams")

        # Display teams
        for idx, team in filtered_teams.head(50).iterrows():
            with st.expander(f"**{team['team_name']}** - {team['tier']} - Rating: {team['team_rating']:,.2f}"):
                # Get team roster
                roster = rosters_df[rosters_df['team_name'] == team['team_name']]

                st.write("**Roster:**")
                for _, player in roster.iterrows():
                    st.write(f"  {player['position']}. {player['discord_name']} - Rating: {player['player_rating']:,.2f}")

                if len(roster) == 0:
                    st.write("*No roster data available*")

    # Player search page
    elif page == "🎮 Player Search":
        st.header("Player Search")

        # Search box
        player_search = st.text_input("🔍 Search player by name", "")

        if player_search:
            # Search players
            filtered_players = players_df[
                (players_df['discord_name'].str.contains(player_search, case=False, na=False)) |
                (players_df['canonical_name'].str.contains(player_search, case=False, na=False))
            ]

            st.caption(f"Found {len(filtered_players)} players")

            for _, player in filtered_players.head(20).iterrows():
                with st.expander(f"**{player['discord_name']}** - Rank #{player['rank']} - Rating: {player['total_rating']:,.2f}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Rating", f"{player['total_rating']:,.2f}")
                    with col2:
                        st.metric("Base Rating", f"{player['base_rating']:,.2f}")
                    with col3:
                        lobby_bonus_pct = player['lobby_bonus_total'] * 100
                        st.metric("Lobby Bonus", f"{lobby_bonus_pct:,.0f}%")

                    # Find team
                    team = rosters_df[rosters_df['discord_name'] == player['discord_name']]
                    if len(team) > 0:
                        st.write(f"**Team:** {team.iloc[0]['team_name']}")
        else:
            st.info("Enter a player name to search")

    # Analytics page
    elif page == "📈 Analytics":
        st.header("League Analytics")

        # Rating distribution
        st.subheader("Team Rating Distribution")
        fig = px.histogram(
            teams_df,
            x='team_rating',
            nbins=50,
            title="Distribution of Team Ratings",
            labels={'team_rating': 'Team Rating'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Division balance
        st.subheader("Division Balance")
        div_ratings = divisions_df.groupby('division_number')['team_rating'].agg(['mean', 'std']).reset_index()
        div_ratings.columns = ['Division', 'Avg Rating', 'Std Dev']

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=div_ratings['Division'],
            y=div_ratings['Avg Rating'],
            error_y=dict(type='data', array=div_ratings['Std Dev']),
            name='Avg Rating',
            marker_color='gold'
        ))
        fig.update_layout(
            title="Average Team Rating by Division (with std dev)",
            xaxis_title="Division",
            yaxis_title="Team Rating",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Top teams
        st.subheader("Top 10 Teams")
        top_teams = teams_df.head(10)[['team_name', 'team_rating', 'tier']]
        top_teams.columns = ['Team', 'Rating', 'Tier']
        st.dataframe(
            top_teams.style.format({'Rating': '{:,.2f}'}),
            use_container_width=True,
            hide_index=True
        )

    # Settings page
    elif page == "⚙️ Settings":
        st.header("Configuration & Settings")

        # Admin mode toggle
        admin_mode = st.sidebar.checkbox("🔓 Enable Admin Mode", value=False)

        if admin_mode:
            st.success("✅ Admin Mode Enabled - You can now adjust settings")
        else:
            st.info("ℹ️ Viewing current settings (Enable Admin Mode in sidebar to edit)")

        st.divider()

        # Tier Thresholds Section
        st.subheader("🏆 Tier Thresholds")

        if admin_mode:
            st.write("Adjust the minimum rating required for each tier:")

            # Initialize session state for tier thresholds if not exists
            if 'tier_thresholds' not in st.session_state:
                st.session_state.tier_thresholds = {
                    'S+': 15000.0,
                    'S': 8000.0,
                    'A+': 3000.0,
                    'A': 1200.0,
                    'B+': 500.0,
                    'B': 250.0,
                    'C+': 125.0,
                    'C': 75.0,
                    'C-': 40.0,
                    'D+': 25.0,
                    'D': 15.0,
                    'D-': 0.0
                }

            # Create columns for tier inputs
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Premium Tiers:**")
                st.session_state.tier_thresholds['S+'] = st.number_input(
                    "S+ Minimum",
                    value=float(st.session_state.tier_thresholds['S+']),
                    min_value=0.0,
                    step=100.0,
                    format="%.2f"
                )
                st.session_state.tier_thresholds['S'] = st.number_input(
                    "S Minimum",
                    value=float(st.session_state.tier_thresholds['S']),
                    min_value=0.0,
                    step=100.0,
                    format="%.2f"
                )
                st.session_state.tier_thresholds['A+'] = st.number_input(
                    "A+ Minimum",
                    value=float(st.session_state.tier_thresholds['A+']),
                    min_value=0.0,
                    step=100.0,
                    format="%.2f"
                )
                st.session_state.tier_thresholds['A'] = st.number_input(
                    "A Minimum",
                    value=float(st.session_state.tier_thresholds['A']),
                    min_value=0.0,
                    step=50.0,
                    format="%.2f"
                )

            with col2:
                st.write("**Mid Tiers:**")
                st.session_state.tier_thresholds['B+'] = st.number_input(
                    "B+ Minimum",
                    value=float(st.session_state.tier_thresholds['B+']),
                    min_value=0.0,
                    step=50.0,
                    format="%.2f"
                )
                st.session_state.tier_thresholds['B'] = st.number_input(
                    "B Minimum",
                    value=float(st.session_state.tier_thresholds['B']),
                    min_value=0.0,
                    step=25.0,
                    format="%.2f"
                )
                st.session_state.tier_thresholds['C+'] = st.number_input(
                    "C+ Minimum",
                    value=float(st.session_state.tier_thresholds['C+']),
                    min_value=0.0,
                    step=25.0,
                    format="%.2f"
                )
                st.session_state.tier_thresholds['C'] = st.number_input(
                    "C Minimum",
                    value=float(st.session_state.tier_thresholds['C']),
                    min_value=0.0,
                    step=10.0,
                    format="%.2f"
                )

            with col3:
                st.write("**Lower Tiers:**")
                st.session_state.tier_thresholds['C-'] = st.number_input(
                    "C- Minimum",
                    value=float(st.session_state.tier_thresholds['C-']),
                    min_value=0.0,
                    step=10.0,
                    format="%.2f"
                )
                st.session_state.tier_thresholds['D+'] = st.number_input(
                    "D+ Minimum",
                    value=float(st.session_state.tier_thresholds['D+']),
                    min_value=0.0,
                    step=5.0,
                    format="%.2f"
                )
                st.session_state.tier_thresholds['D'] = st.number_input(
                    "D Minimum",
                    value=float(st.session_state.tier_thresholds['D']),
                    min_value=0.0,
                    step=5.0,
                    format="%.2f"
                )
                st.session_state.tier_thresholds['D-'] = st.number_input(
                    "D- Minimum",
                    value=float(st.session_state.tier_thresholds['D-']),
                    min_value=0.0,
                    step=1.0,
                    format="%.2f"
                )

            st.divider()

            # Preview tier distribution with new thresholds
            st.subheader("Preview: New Tier Distribution")

            # Function to assign tier based on rating
            def assign_tier(rating, thresholds):
                if rating >= thresholds['S+']:
                    return 'S+'
                elif rating >= thresholds['S']:
                    return 'S'
                elif rating >= thresholds['A+']:
                    return 'A+'
                elif rating >= thresholds['A']:
                    return 'A'
                elif rating >= thresholds['B+']:
                    return 'B+'
                elif rating >= thresholds['B']:
                    return 'B'
                elif rating >= thresholds['C+']:
                    return 'C+'
                elif rating >= thresholds['C']:
                    return 'C'
                elif rating >= thresholds['C-']:
                    return 'C-'
                elif rating >= thresholds['D+']:
                    return 'D+'
                elif rating >= thresholds['D']:
                    return 'D'
                else:
                    return 'D-'

            # Calculate new tier distribution
            teams_with_new_tiers = teams_df.copy()
            teams_with_new_tiers['new_tier'] = teams_with_new_tiers['team_rating'].apply(
                lambda x: assign_tier(x, st.session_state.tier_thresholds)
            )

            # Show comparison
            col1, col2 = st.columns(2)

            # Define tier order from highest to lowest
            tier_order = ['S+', 'S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'C-', 'D+', 'D', 'D-']

            with col1:
                st.write("**Current Tiers:**")
                current_tier_counts = teams_df['tier'].value_counts()
                # Reindex with tier_order and fill missing with 0, then filter out zeros
                current_tier_counts = current_tier_counts.reindex(tier_order, fill_value=0)
                current_tier_counts = current_tier_counts[current_tier_counts > 0]
                st.dataframe(current_tier_counts.rename("Teams"), use_container_width=True)

            with col2:
                st.write("**New Tiers (Preview):**")
                new_tier_counts = teams_with_new_tiers['new_tier'].value_counts()
                # Reindex with tier_order and fill missing with 0, then filter out zeros
                new_tier_counts = new_tier_counts.reindex(tier_order, fill_value=0)
                new_tier_counts = new_tier_counts[new_tier_counts > 0]
                st.dataframe(new_tier_counts.rename("Teams"), use_container_width=True)

            # Reset and Apply buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reset to Defaults", type="secondary", use_container_width=True):
                    st.session_state.tier_thresholds = {
                        'S+': 15000.0,
                        'S': 8000.0,
                        'A+': 3000.0,
                        'A': 1200.0,
                        'B+': 500.0,
                        'B': 250.0,
                        'C+': 125.0,
                        'C': 75.0,
                        'C-': 40.0,
                        'D+': 25.0,
                        'D': 15.0,
                        'D-': 0.0
                    }
                    st.rerun()

            with col2:
                if st.button("✅ Apply New Thresholds", type="primary", use_container_width=True):
                    # Apply the new tier assignments
                    with st.spinner("Updating tier assignments in database..."):
                        try:
                            # Function to assign tier based on rating
                            def assign_tier(rating, thresholds):
                                if rating >= thresholds['S+']:
                                    return 'S+'
                                elif rating >= thresholds['S']:
                                    return 'S'
                                elif rating >= thresholds['A+']:
                                    return 'A+'
                                elif rating >= thresholds['A']:
                                    return 'A'
                                elif rating >= thresholds['B+']:
                                    return 'B+'
                                elif rating >= thresholds['B']:
                                    return 'B'
                                elif rating >= thresholds['C+']:
                                    return 'C+'
                                elif rating >= thresholds['C']:
                                    return 'C'
                                elif rating >= thresholds['C-']:
                                    return 'C-'
                                elif rating >= thresholds['D+']:
                                    return 'D+'
                                elif rating >= thresholds['D']:
                                    return 'D'
                                else:
                                    return 'D-'

                            # Get database connection
                            conn = get_database_connection()
                            cursor = conn.cursor()

                            # Get all S12 teams
                            cursor.execute("""
                                SELECT team_id, team_rating
                                FROM teams
                                WHERE season_id = (SELECT season_id FROM seasons WHERE season_name = 'S12')
                            """)
                            teams = cursor.fetchall()

                            # Update each team's tier in the database
                            teams_updated = 0
                            for team_id, team_rating in teams:
                                new_tier = assign_tier(team_rating, st.session_state.tier_thresholds)
                                cursor.execute("""
                                    UPDATE teams
                                    SET tier = ?
                                    WHERE team_id = ?
                                """, (new_tier, team_id))
                                teams_updated += 1

                            # Commit the changes
                            conn.commit()

                            # Clear cache to reload data with new tiers from database
                            load_teams.clear()
                            load_divisions.clear()

                            st.success(f"✅ Tier thresholds applied! {teams_updated} teams have been permanently reassigned to new tiers in the database.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error applying tier thresholds: {str(e)}")

        else:
            # Read-only view of current thresholds
            with st.expander("🏆 View Current Tier Thresholds", expanded=True):
                current_thresholds = {
                    'S+': 15000,
                    'S': 8000,
                    'A+': 3000,
                    'A': 1200,
                    'B+': 500,
                    'B': 250,
                    'C+': 125,
                    'C': 75,
                    'C-': 40,
                    'D+': 25,
                    'D': 15,
                    'D-': 0
                }

                for tier, threshold in current_thresholds.items():
                    st.text(f"{tier} Tier: {threshold:,.2f}+ points")

        st.divider()

        # Lobby Bonus Configuration
        st.subheader("🔢 Lobby Bonus Configuration")

        if admin_mode:
            st.write("Adjust lobby bonus percentages (applied additively per lobby appearance):")

            # Initialize session state for lobby bonuses
            if 'lobby_bonuses' not in st.session_state:
                st.session_state.lobby_bonuses = {
                    '1': 8192.0,
                    '1.5': 4096.0,
                    '2': 2048.0,
                    '2.5': 1024.0,
                    '3': 512.0,
                    '3.5': 256.0,
                    '4': 128.0,
                    '4.5': 64.0,
                    '5': 32.0,
                    '5.5': 16.0,
                    '6': 8.0,
                    '6.5': 4.0,
                    '7': 2.0
                }

            # Create 3 columns for lobby bonus inputs
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Top Lobbies:**")
                st.session_state.lobby_bonuses['1'] = st.number_input(
                    "Lobby 1 (%)", value=float(st.session_state.lobby_bonuses['1']),
                    min_value=0.0, step=10.0, format="%.2f"
                )
                st.session_state.lobby_bonuses['1.5'] = st.number_input(
                    "Lobby 1.5 (%)", value=float(st.session_state.lobby_bonuses['1.5']),
                    min_value=0.0, step=10.0, format="%.2f"
                )
                st.session_state.lobby_bonuses['2'] = st.number_input(
                    "Lobby 2 (%)", value=float(st.session_state.lobby_bonuses['2']),
                    min_value=0.0, step=10.0, format="%.2f"
                )
                st.session_state.lobby_bonuses['2.5'] = st.number_input(
                    "Lobby 2.5 (%)", value=float(st.session_state.lobby_bonuses['2.5']),
                    min_value=0.0, step=10.0, format="%.2f"
                )
                st.session_state.lobby_bonuses['3'] = st.number_input(
                    "Lobby 3 (%)", value=float(st.session_state.lobby_bonuses['3']),
                    min_value=0.0, step=5.0, format="%.2f"
                )

            with col2:
                st.write("**Mid Lobbies:**")
                st.session_state.lobby_bonuses['3.5'] = st.number_input(
                    "Lobby 3.5 (%)", value=float(st.session_state.lobby_bonuses['3.5']),
                    min_value=0.0, step=5.0, format="%.2f"
                )
                st.session_state.lobby_bonuses['4'] = st.number_input(
                    "Lobby 4 (%)", value=float(st.session_state.lobby_bonuses['4']),
                    min_value=0.0, step=5.0, format="%.2f"
                )
                st.session_state.lobby_bonuses['4.5'] = st.number_input(
                    "Lobby 4.5 (%)", value=float(st.session_state.lobby_bonuses['4.5']),
                    min_value=0.0, step=5.0, format="%.2f"
                )
                st.session_state.lobby_bonuses['5'] = st.number_input(
                    "Lobby 5 (%)", value=float(st.session_state.lobby_bonuses['5']),
                    min_value=0.0, step=5.0, format="%.2f"
                )

            with col3:
                st.write("**Lower Lobbies:**")
                st.session_state.lobby_bonuses['5.5'] = st.number_input(
                    "Lobby 5.5 (%)", value=float(st.session_state.lobby_bonuses['5.5']),
                    min_value=0.0, step=1.0, format="%.2f"
                )
                st.session_state.lobby_bonuses['6'] = st.number_input(
                    "Lobby 6 (%)", value=float(st.session_state.lobby_bonuses['6']),
                    min_value=0.0, step=1.0, format="%.2f"
                )
                st.session_state.lobby_bonuses['6.5'] = st.number_input(
                    "Lobby 6.5 (%)", value=float(st.session_state.lobby_bonuses['6.5']),
                    min_value=0.0, step=0.5, format="%.2f"
                )
                st.session_state.lobby_bonuses['7'] = st.number_input(
                    "Lobby 7 (%)", value=float(st.session_state.lobby_bonuses['7']),
                    min_value=0.0, step=0.5, format="%.2f"
                )

            # Reset button for lobby bonuses
            if st.button("🔄 Reset Lobby Bonuses to Defaults", type="secondary"):
                st.session_state.lobby_bonuses = {
                    '1': 8192.0, '1.5': 4096.0, '2': 2048.0, '2.5': 1024.0,
                    '3': 512.0, '3.5': 256.0, '4': 128.0, '4.5': 64.0,
                    '5': 32.0, '5.5': 16.0, '6': 8.0, '6.5': 4.0, '7': 2.0
                }
                st.rerun()

        else:
            # Read-only view
            with st.expander("🔢 View Current Lobby Bonuses", expanded=False):
                bonuses = {
                    'Lobby 1': '8192%', 'Lobby 1.5': '4096%', 'Lobby 2': '2048%',
                    'Lobby 2.5': '1024%', 'Lobby 3': '512%', 'Lobby 3.5': '256%',
                    'Lobby 4': '128%', 'Lobby 4.5': '64%', 'Lobby 5': '32%',
                    'Lobby 5.5': '16%', 'Lobby 6': '8%', 'Lobby 6.5': '4%', 'Lobby 7': '2%'
                }
                for lobby, bonus in bonuses.items():
                    st.text(f"{lobby}: {bonus}")

        st.divider()

        # Season Weighting Configuration
        st.subheader("⚖️ Season Weighting")

        if admin_mode:
            st.write("Adjust the weighting between seasons (must sum to 100%):")

            # Initialize session state for season weights
            if 'season_weights' not in st.session_state:
                st.session_state.season_weights = {'S12': 100.0, 'S11': 0.0}

            col1, col2 = st.columns(2)
            with col1:
                s12_weight = st.slider(
                    "S12 Weight (%)", min_value=0.0, max_value=100.0,
                    value=st.session_state.season_weights['S12'], step=5.0
                )
            with col2:
                s11_weight = 100.0 - s12_weight
                st.metric("S11 Weight (%)", f"{s11_weight:.0f}")

            st.session_state.season_weights = {'S12': s12_weight, 'S11': s11_weight}

            if s12_weight + s11_weight != 100.0:
                st.warning("⚠️ Weights must sum to 100%")

        else:
            with st.expander("⚖️ View Current Season Weights", expanded=False):
                st.text("S12: 100%")
                st.text("S11: 0%")

        st.divider()

        # Re-calculation Section (Admin only)
        if admin_mode:
            st.subheader("🔄 Re-calculate Ratings")
            st.write("Click below to recalculate all player and team ratings with the new settings above.")

            if st.button("⚡ Calculate Preview", type="primary", use_container_width=True):
                with st.spinner("Recalculating ratings..."):
                    # This will trigger the recalculation in the next section
                    st.session_state.recalculate = True
                    st.rerun()

            st.divider()

            # Show recalculation results if available
            if st.session_state.get('recalculate', False):
                st.subheader("📊 Recalculation Results")

                # Load lobby performances and recalculate
                try:
                    lobby_perfs = load_player_lobby_performances()

                    # Recalculate with new settings
                    new_player_ratings = recalculate_player_ratings(
                        lobby_perfs,
                        st.session_state.lobby_bonuses,
                        st.session_state.season_weights
                    )

                    # Load current players for comparison
                    current_players = load_players()

                    # Merge for comparison
                    comparison = pd.merge(
                        current_players[['discord_name', 'total_rating']],
                        new_player_ratings[['discord_name', 'total_rating']],
                        on='discord_name',
                        suffixes=('_current', '_new')
                    )

                    comparison['rating_change'] = comparison['total_rating_new'] - comparison['total_rating_current']
                    comparison['rating_change_pct'] = (comparison['rating_change'] / comparison['total_rating_current']) * 100

                    # Sort by absolute rating change
                    comparison = comparison.sort_values('rating_change', ascending=False, key=abs)

                    # Show stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Avg Rating (Current)",
                            f"{comparison['total_rating_current'].mean():,.0f}"
                        )
                    with col2:
                        st.metric(
                            "Avg Rating (New)",
                            f"{comparison['total_rating_new'].mean():,.0f}",
                            f"{comparison['rating_change'].mean():,.0f}"
                        )
                    with col3:
                        st.metric(
                            "Players Affected",
                            f"{len(comparison[comparison['rating_change'] != 0])}"
                        )

                    # Show top movers
                    st.subheader("Top 10 Rating Increases")
                    top_increases = comparison.nlargest(10, 'rating_change')[
                        ['discord_name', 'total_rating_current', 'total_rating_new', 'rating_change', 'rating_change_pct']
                    ]
                    top_increases.columns = ['Player', 'Current Rating', 'New Rating', 'Change', 'Change %']
                    st.dataframe(
                        top_increases.style.format({
                            'Current Rating': '{:,.2f}',
                            'New Rating': '{:,.2f}',
                            'Change': '{:+,.2f}',
                            'Change %': '{:+.1f}%'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

                    st.subheader("Top 10 Rating Decreases")
                    top_decreases = comparison.nsmallest(10, 'rating_change')[
                        ['discord_name', 'total_rating_current', 'total_rating_new', 'rating_change', 'rating_change_pct']
                    ]
                    top_decreases.columns = ['Player', 'Current Rating', 'New Rating', 'Change', 'Change %']
                    st.dataframe(
                        top_decreases.style.format({
                            'Current Rating': '{:,.2f}',
                            'New Rating': '{:,.2f}',
                            'Change': '{:+,.2f}',
                            'Change %': '{:+.1f}%'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

                    # Download buttons
                    st.divider()
                    col1, col2 = st.columns(2)

                    with col1:
                        csv_data = comparison.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Full Comparison (CSV)",
                            data=csv_data,
                            file_name="rating_comparison.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                    with col2:
                        if st.button("🔄 Run New Calculation", type="secondary", use_container_width=True):
                            st.session_state.recalculate = False
                            st.rerun()

                except Exception as e:
                    st.error(f"Error during recalculation: {str(e)}")
                    st.session_state.recalculate = False

if __name__ == "__main__":
    main()
