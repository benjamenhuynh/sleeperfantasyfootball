class Players:

    # ============================================================
    # Function Name: __init__
    #
    # Parameters:
    #   players: NFL player database keyed by Sleeper player ID.
    #
    # Return:
    #   None. Stores player data for lookups.
    # ============================================================
    def __init__(self, players):
        self.PlayersData = players

    # ============================================================
    # Function Name: GetPlayer
    #
    # Parameters:
    #   player_id: Sleeper player ID.
    #
    # Return:
    #   Player record, or None when the player is not found.
    # ============================================================
    def GetPlayer(self, player_id):
        return self.PlayersData.get(str(player_id))

    # ============================================================
    # Function Name: GetPlayerName
    #
    # Parameters:
    #   player_id: Sleeper player ID.
    #
    # Return:
    #   Player's full name, or the player ID if the player is unknown.
    # ============================================================
    def GetPlayerName(self, player_id):
        player = self.GetPlayer(player_id)
        if not player:
            return str(player_id)
        return f"{player['first_name']} {player['last_name']}"

    # ============================================================
    # Function Name: GetPlayerPosition
    #
    # Parameters:
    #   player_id: Sleeper player ID.
    #
    # Return:
    #   Player position, or the player ID if the player is unknown.
    # ============================================================
    def GetPlayerPosition(self, player_id):
        player = self.GetPlayer(player_id)
        if not player:
            return str(player_id)
        return player["position"]
