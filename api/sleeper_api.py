import requests

from config.config import (
    REQUEST_TIMEOUT,
    SLEEPER_API_BASE_URL,
    SLEEPER_PROJECTIONS_BASE_URL,
)


class SleeperAPI:

    # ============================================================
    # Function Name: __init__
    #
    # Parameters:
    #   None.
    #
    # Return:
    #   None. Initializes the Sleeper API client.
    # ============================================================
    def __init__(self):
        self.BaseURL = SLEEPER_API_BASE_URL
        self.ProjectionsBaseURL = SLEEPER_PROJECTIONS_BASE_URL

    # ============================================================
    # Function Name: Get
    #
    # Parameters:
    #   url: API endpoint URL.
    #   params: optional query parameters.
    #
    # Return:
    #   Decoded JSON response from Sleeper.
    # ============================================================
    def Get(self, url, params=None):
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    # ============================================================
    # Function Name: GetLeagueRosters
    #
    # Parameters:
    #   league_id: Sleeper league ID.
    #
    # Return:
    #   List of rosters in the league.
    # ============================================================
    def GetLeagueRosters(self, league_id):
        return self.Get(f"{self.BaseURL}/league/{league_id}/rosters")

    def GetLeague(self, league_id):
        return self.Get(f"{self.BaseURL}/league/{league_id}")

    # ============================================================
    # Function Name: GetNFLPlayers
    #
    # Parameters:
    #   None.
    #
    # Return:
    #   NFL player database keyed by Sleeper player ID.
    # ============================================================
    def GetNFLPlayers(self):
        return self.Get(f"{self.BaseURL}/players/nfl")

    # ============================================================
    # Function Name: GetLeagueUsers
    #
    # Parameters:
    #   league_id: Sleeper league ID.
    #
    # Return:
    #   List of users in the league.
    # ============================================================
    def GetLeagueUsers(self, league_id):
        return self.Get(f"{self.BaseURL}/league/{league_id}/users")

    # ============================================================
    # Function Name: GetNFLState
    #
    # Parameters:
    #   None.
    #
    # Return:
    #   Current NFL season and week information.
    # ============================================================
    def GetNFLState(self):
        return self.Get(f"{self.BaseURL}/state/nfl")

    # ============================================================
    # Function Name: GetWeeklyPlayerStats
    #
    # Parameters:
    #   season: NFL season year.
    #   week: NFL week number.
    #   season_type: season type such as regular or post.
    #
    # Return:
    #   Weekly player stats keyed by Sleeper player ID.
    # ============================================================
    def GetWeeklyPlayerStats(self, season, week, season_type="regular"):
        url = f"{self.BaseURL}/stats/nfl/{season_type}/{season}/{week}"
        return self.Get(url)

    def GetNFLSeasonSchedule(self, season, season_type="regular"):
        url = f"{self.ProjectionsBaseURL}/schedule/nfl/{season_type}/{season}"
        return self.Get(url)

    # ============================================================
    # Function Name: GetWeeklyPlayerProjections
    #
    # Parameters:
    #   season: NFL season year.
    #   week: NFL week number.
    #   season_type: season type such as regular or post.
    #
    # Return:
    #   Weekly player projections from Sleeper.
    # ============================================================
    def GetWeeklyPlayerProjections(self, season, week, season_type="regular"):
        url = f"{self.ProjectionsBaseURL}/projections/nfl/{season}/{week}"
        return self.Get(url, params={"season_type": season_type})
