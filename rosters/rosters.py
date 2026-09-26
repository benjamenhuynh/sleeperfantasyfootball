from stats import FormatPlayerStats


class Rosters:

    # ============================================================
    # Function Name: __init__
    #
    # Parameters:
    #   players: Players lookup object.
    #   users: list containing league users.
    #   player_stats: weekly stats keyed by Sleeper player ID.
    #   player_projections: weekly projections keyed by Sleeper player ID.
    #
    # Return:
    #   None. Stores data required to process and print rosters.
    # ============================================================
    def __init__(self, players, users, player_stats, player_projections):
        self.Players = players
        self.Users = users
        self.PlayerStats = player_stats
        self.PlayerProjections = player_projections

    # ============================================================
    # Function Name: GetTeamName
    #
    # Parameters:
    #   owner_id: Sleeper user ID that owns the roster.
    #
    # Return:
    #   Fantasy team name, or owner ID if the user is unknown.
    # ============================================================
    def GetTeamName(self, owner_id):
        for user in self.Users:
            if user["user_id"] == owner_id:
                metadata = user.get("metadata", {})
                return metadata.get("team_name", user["display_name"])
        return owner_id

    # ============================================================
    # Function Name: GetStarters
    #
    # Parameters:
    #   roster: dictionary containing one Sleeper roster.
    #
    # Return:
    #   Starter player IDs sorted by position.
    # ============================================================
    def GetStarters(self, roster):
        starters = [
            player_id
            for player_id in roster["players"]
            if player_id in roster["starters"]
        ]
        return self.SortStarters(starters)

    # ============================================================
    # Function Name: GetBench
    #
    # Parameters:
    #   roster: dictionary containing one Sleeper roster.
    #
    # Return:
    #   Bench player IDs in the roster's original order.
    # ============================================================
    def GetBench(self, roster):
        return [
            player_id
            for player_id in roster["players"]
            if player_id not in roster["starters"]
        ]

    # ============================================================
    # Function Name: SortStarters
    #
    # Parameters:
    #   starters: player IDs in the starting lineup.
    #
    # Return:
    #   Starter player IDs ordered by position.
    # ============================================================
    def SortStarters(self, starters):
        position_order = {
            "QB": 0,
            "RB": 1,
            "WR": 2,
            "TE": 3,
            "K": 4,
            "DEF": 5,
            "DST": 5,
        }
        return sorted(
            starters,
            key=lambda player_id: position_order.get(
                self.Players.GetPlayerPosition(player_id), len(position_order)
            ),
        )

    # ============================================================
    # Function Name: FormatPlayerLine
    #
    # Parameters:
    #   player_id: Sleeper player ID.
    #
    # Return:
    #   Formatted player name, position, and available stats or projection.
    # ============================================================
    def FormatPlayerLine(self, player_id):
        stats = self.PlayerStats.get(str(player_id))
        if stats:
            stats_text = FormatPlayerStats(stats)
        else:
            stats_text = FormatPlayerStats(
                self.PlayerProjections.get(str(player_id)), label="Proj"
            )
        position = self.Players.GetPlayerPosition(player_id)
        name = self.Players.GetPlayerName(player_id)
        return f"{position} {name} — {stats_text}"

    # ============================================================
    # Function Name: PrintRoster
    #
    # Parameters:
    #   roster: dictionary containing one Sleeper roster.
    #
    # Return:
    #   None. Prints starters and bench players for the roster.
    # ============================================================
    def PrintRoster(self, roster):
        print("\n")
        print(self.GetTeamName(roster["owner_id"]))
        print("\nSTARTERS")
        for player_id in self.GetStarters(roster):
            print(self.FormatPlayerLine(player_id))

        print("\nBENCH")
        for player_id in self.GetBench(roster):
            print(self.FormatPlayerLine(player_id))
