import json

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
        "players": players,
        "users": users,
        "season": season,
        "week": week,
        "season_type": season_type,
        "player_stats": player_stats,
        "player_projections": player_projections,
    }
