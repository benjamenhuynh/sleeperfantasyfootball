from league import GetCurrentLeagueData
from players import Players
from rosters import Rosters

# ============================================================
# Function Name: main
#
# Parameters:
#   None.
#
# Return:
#   None. Retrieves current league data and prints each roster.
# ============================================================
def main():
    league_data = GetCurrentLeagueData()
    players = Players(league_data["players"])
    roster_printer = Rosters(
        players,
        league_data["users"],
        league_data["player_stats"],
        league_data["player_projections"],
    )

    print(
        f"NFL {league_data['season']} {league_data['season_type']} season, "
        f"week {league_data['week']}"
    )
    for roster in league_data["rosters"]:
        roster_printer.PrintRoster(roster)


if __name__ == "__main__":
    main()
