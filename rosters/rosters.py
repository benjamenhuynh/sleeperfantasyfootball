from analytics import CalculateFantasyPoints
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
    def __init__(self, players, users, player_stats, player_projections,
                 roster_positions=None):
        self.Players = players
        self.Users = users
        self.PlayerStats = player_stats
        self.PlayerProjections = player_projections
        self.RosterPositions = roster_positions or []

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
        entries = self.GetStarterEntries(roster)
        if entries:
            return [player_id for player_id, _ in entries]
        starters = [player_id for player_id in roster["players"]
                    if player_id in roster["starters"]]
        return self.SortStarters(starters)

    def GetStarterEntries(self, roster):
        roster_players = set(roster.get("players", []))
        starters = roster.get("starters", [])
        entries = []
        for index, player_id in enumerate(starters):
            if player_id in (None, "0", 0) or player_id not in roster_players:
                continue
            slot = (self.RosterPositions[index]
                    if index < len(self.RosterPositions) else "")
            entries.append((player_id, slot))
        return entries

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
    def FormatPlayerLine(
        self,
        player_id,
        lineup_slot=None,
        points_key="pts_ppr",
        points_label="PPR",
        scoring_settings=None,
    ):
        position = self.Players.GetPlayerPosition(player_id)
        stats = self.PlayerStats.get(str(player_id))
        if stats:
            display_stats = dict(stats)
            calculated_points = CalculateFantasyPoints(
                stats, scoring_settings, position=position
            )
            if calculated_points is not None:
                display_stats[points_key] = calculated_points
            stats_text = FormatPlayerStats(
                display_stats, points_key=points_key, points_label=points_label
            )
        else:
            projection = self.PlayerProjections.get(str(player_id))
            display_projection = dict(projection) if projection else None
            calculated_points = CalculateFantasyPoints(
                projection, scoring_settings, position=position
            )
            if calculated_points is not None:
                display_projection[points_key] = calculated_points
            stats_text = FormatPlayerStats(
                display_projection,
                label="Proj",
                points_key=points_key,
                points_label=points_label,
            )
        if lineup_slot and lineup_slot not in (position, "BN"):
            position = (f"FLEX ({position})" if lineup_slot in
                        ("FLEX", "REC_FLEX", "WRRB_FLEX") else lineup_slot)
        name = self.Players.GetPlayerName(player_id)
        line = f"{position} {name}"
        if not stats and stats_text == "Proj unavailable":
            player = self.Players.GetPlayer(player_id) or {}
            injury_status = player.get("injury_status")
            if injury_status:
                injury_detail = player.get("injury_body_part")
                injury_notes = player.get("injury_notes")
                injury_text = injury_status
                if injury_detail:
                    injury_text += f" ({injury_detail})"
                if injury_notes:
                    injury_text += f" — {injury_notes}"
                line += f" — Injury: {injury_text}"
        else:
            line += f" — {stats_text}"
        return line

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
