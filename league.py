import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from api import SleeperAPI
from config import DATA_DIRECTORY, LEAGUE_ID
from projections import NormalizeProjections


# ============================================================
# Function Name: GetCurrentLeagueData
#
# Parameters:
#   None.
#
# Return:
#   Dictionary containing current league, player, stats, and projection data.
# ============================================================
def GetCurrentLeagueData():
    sleeper_api = SleeperAPI()
    league = sleeper_api.GetLeague(LEAGUE_ID)
    rosters = sleeper_api.GetLeagueRosters(LEAGUE_ID)
    players = sleeper_api.GetNFLPlayers()
    users = sleeper_api.GetLeagueUsers(LEAGUE_ID)
    nfl_state = sleeper_api.GetNFLState()

    season = nfl_state["season"]
    week = nfl_state["week"]
    season_type = nfl_state.get("season_type", "regular")
    player_stats = sleeper_api.GetWeeklyPlayerStats(season, week, season_type)
    player_projections = NormalizeProjections(
        sleeper_api.GetWeeklyPlayerProjections(season, week, season_type)
    )

    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (DATA_DIRECTORY / "players.json").open("w") as file:
        json.dump(players, file, indent=4)

    return {
        "rosters": rosters,
        "roster_positions": league.get("roster_positions", []),
        "scoring_settings": league.get("scoring_settings", {}),
        "players": players,
        "users": users,
        "season": season,
        "week": week,
        "season_type": season_type,
        "player_stats": player_stats,
        "player_projections": player_projections,
    }


def GetHistoricalMatchupData(season, through_week, season_type="regular"):
    """Load and cache weekly player stats and schedule for prior weeks."""
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stats_cache = DATA_DIRECTORY / f"historical_stats_{season}_{season_type}.json"
    schedule_cache = DATA_DIRECTORY / f"nfl_schedule_{season}_{season_type}.json"

    if stats_cache.exists():
        with stats_cache.open() as file:
            weekly_stats = json.load(file)
    else:
        weekly_stats = {}

    requested_weeks = range(1, max(1, int(through_week)))
    missing_weeks = [str(week) for week in requested_weeks if str(week) not in weekly_stats]
    if missing_weeks:
        sleeper_api = SleeperAPI()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(
                    sleeper_api.GetWeeklyPlayerStats,
                    season,
                    int(week),
                    season_type,
                ): week
                for week in missing_weeks
            }
            for future in as_completed(futures):
                week = futures[future]
                try:
                    weekly_stats[week] = future.result()
                except Exception:
                    # Keep any successfully loaded weeks; failed weeks can retry next time.
                    continue
        with stats_cache.open("w") as file:
            json.dump(weekly_stats, file)

    if schedule_cache.exists():
        with schedule_cache.open() as file:
            schedule = json.load(file)
    else:
        schedule = []

    if not schedule:
        try:
            schedule = SleeperAPI().GetNFLSeasonSchedule(season, season_type)
        except Exception:
            schedule = []
        if schedule:
            with schedule_cache.open("w") as file:
                json.dump(schedule, file)

    return {"weekly_stats": weekly_stats, "schedule": schedule}
