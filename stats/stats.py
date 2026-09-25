"""Fetch and format weekly player stats from Sleeper."""

import requests


# ============================================================
# Function Name: get_weekly_player_stats
#
# Parameters:
#   season: NFL season year.
#   week: NFL week number.
#   season_type: season type such as regular or post.
#
# Return:
#   Dictionary of weekly player stats keyed by Sleeper player ID.
# ============================================================

def get_weekly_player_stats(season, week, season_type="regular"):
    """Return weekly NFL stats keyed by Sleeper player ID.

    Sleeper's stats endpoint is undocumented and may change independently of
    the supported Sleeper API.
    """
    url = (
        "https://api.sleeper.app/v1/stats/nfl/"
        f"{season_type}/{season}/{week}"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


# ============================================================
# Function Name: format_player_stats
#
# Parameters:
#   stats: dictionary of one player's stats, or None when unavailable.
#
# Return:
#   Readable summary of common passing, rushing, receiving, and PPR stats.
# ============================================================

def format_player_stats(stats):
    """Format common passing, rushing, receiving, and fantasy point stats."""
    if not stats:
        return "Stats unavailable"

    fields = (
        ("pass_yd", "Pass Yds"),
        ("pass_td", "Pass TD"),
        ("rush_yd", "Rush Yds"),
        ("rush_td", "Rush TD"),
        ("rec", "Rec"),
        ("rec_yd", "Rec Yds"),
        ("rec_td", "Rec TD"),
        ("pts_ppr", "PPR"),
    )
    parts = [f"{label} {stats[key]}" for key, label in fields if key in stats]
    return ", ".join(parts) if parts else "No stats recorded"
