import requests
import json
from stats import get_weekly_player_stats, format_player_stats

# ============================================================
# Function Name: GetPlayerName
#
# Parameters:
#   player_id: string containing the Sleeper player ID
#   players: dictionary containing all NFL player information
#
# Return:
#   If successful, returns the player's first and last name.
#   Otherwise, returns the original player_id.
# ============================================================

def GetPlayerName(player_id, players):

    player = players.get(player_id)

    if not player:
        return player_id

    return f"{player['first_name']} {player['last_name']}"

# ============================================================
# Function Name: GetPlayerPosition
#
# Parameters:
#   player_id: string containing the Sleeper player ID
#   players: dictionary containing all NFL player information
#
# Return:
#   If successful, returns a string containing the player's position.
#   Otherwise, returns the original player_id.
# ============================================================

def GetPlayerPosition(player_id, players):

    player = players.get(player_id)

    if not player:

        return player_id

    return player["position"]

# ============================================================
# Function Name: PrintRoster
#
# Parameters:
#   roster: dictionary containing information for one Sleeper roster
#   players: dictionary containing all NFL player information
#   users: list containing all users in the league
#   player_stats: dictionary containing weekly stats by player ID
#
# Return:
#   None. Prints the roster's players with their positions and weekly stats.
# ============================================================

def PrintRoster(roster, players, users, player_stats):

    StartersArr = []
    BenchArr = []

    print("\n")
    print(GetTeamName(roster["owner_id"], users))

    for playerID in roster["players"]:

        if playerID in roster["starters"]:
            StartersArr.append(playerID)
        else:
            BenchArr.append(playerID)

    print("\nSTARTERS")

    for playerID in StartersArr:
        stats = format_player_stats(player_stats.get(playerID))
        print(GetPlayerPosition(playerID, players) + " " +
              GetPlayerName(playerID, players) + " — " + stats)

    print("\nBENCH")

    for playerID in BenchArr:
        stats = format_player_stats(player_stats.get(playerID))
        print(GetPlayerPosition(playerID, players) + " " +
              GetPlayerName(playerID, players) + " — " + stats)
    
# ============================================================
# Function Name: GetTeamName
#
# Parameters:
#   owner_id: string containing the Sleeper user ID that owns the roster
#   users: list containing all users in the league
#
# Return:
#   If successful, returns a string containing the fantasy team name.
#   Otherwise, returns the original owner_id.
# ============================================================

def GetTeamName(owner_id, users):

    for user in users:

        if user["user_id"] == owner_id:

            #print(user)

            metadata = user.get("metadata", {})

            return metadata.get("team_name", user["display_name"])

    return owner_id

def main():

    leagueID = "1389386643680559106"

    url = f"https://api.sleeper.app/v1/league/{leagueID}/rosters"

    response = requests.get(url)
    response.raise_for_status()

    rosters = response.json()

    url = "https://api.sleeper.app/v1/players/nfl"

    response = requests.get(url)
    response.raise_for_status()

    players = response.json()

    with open("players.json", "w") as file:
        json.dump(players, file, indent=4)

    url = f"https://api.sleeper.app/v1/league/{leagueID}/users"
    response = requests.get(url)
    response.raise_for_status()
    users = response.json()

    response = requests.get("https://api.sleeper.app/v1/state/nfl")
    response.raise_for_status()
    nfl_state = response.json()
    season = nfl_state["season"]
    week = nfl_state["week"]
    season_type = nfl_state.get("season_type", "regular")
    player_stats = get_weekly_player_stats(season, week, season_type)

    print(f"NFL {season} {season_type} season, week {week}")
    for roster in rosters:
        PrintRoster(roster, players, users, player_stats)


if __name__ == "__main__":
    main()
