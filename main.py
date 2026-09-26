import json

from api import SleeperAPI
from config import DATA_DIRECTORY, LEAGUE_ID
from players import Players
from projections import NormalizeProjections
from rosters import Rosters

def main():
    sleeper_api = SleeperAPI()

    rosters = sleeper_api.GetLeagueRosters(LEAGUE_ID)
    players_data = sleeper_api.GetNFLPlayers()
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
        json.dump(players_data, file, indent=4)

    player_lookup = Players(players_data)
    roster_printer = Rosters(
        player_lookup, users, player_stats, player_projections
    )

    print(f"NFL {season} {season_type} season, week {week}")
    for roster in rosters:
        roster_printer.PrintRoster(roster)


if __name__ == "__main__":
    main()
