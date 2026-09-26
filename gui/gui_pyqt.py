import sys
from pathlib import Path

import requests

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QListWidgetItem,
)
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon, QPixmap
from league import GetCurrentLeagueData
from players import Players
from rosters import Rosters


LOGO_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "team_logos"
TEAM_ABBREVIATIONS = {
    "ARI": "ari", "ATL": "atl", "BAL": "bal", "BUF": "buf",
    "CAR": "car", "CHI": "chi", "CIN": "cin", "CLE": "cle",
    "DAL": "dal", "DEN": "den", "DET": "det", "GB": "gb",
    "HOU": "hou", "IND": "ind", "JAX": "jax", "KC": "kc",
    "LAC": "lac", "LAR": "lar", "LV": "lv", "MIA": "mia",
    "MIN": "min", "NE": "ne", "NO": "no", "NYG": "nyg",
    "NYJ": "nyj", "PHI": "phi", "PIT": "pit", "SF": "sf",
    "SEA": "sea", "TB": "tb", "TEN": "ten", "WAS": "was",
}
TEAM_NAMES = {
    "ARI": "Arizona", "ATL": "Atlanta", "BAL": "Baltimore", "BUF": "Buffalo",
    "CAR": "Carolina", "CHI": "Chicago", "CIN": "Cincinnati", "CLE": "Cleveland",
    "DAL": "Dallas", "DEN": "Denver", "DET": "Detroit", "GB": "Green Bay",
    "HOU": "Houston", "IND": "Indianapolis", "JAX": "Jacksonville", "KC": "Kansas City",
    "LAC": "LA Chargers", "LAR": "LA Rams", "LV": "Las Vegas", "MIA": "Miami",
    "MIN": "Minnesota", "NE": "New England", "NO": "New Orleans", "NYG": "NY Giants",
    "NYJ": "NY Jets", "PHI": "Philadelphia", "PIT": "Pittsburgh", "SF": "San Francisco",
    "SEA": "Seattle", "TB": "Tampa Bay", "TEN": "Tennessee", "WAS": "Washington",
}


def GetTeamLogo(team):
    abbreviation = (team or "").upper()
    logo_key = TEAM_ABBREVIATIONS.get(abbreviation)
    if not logo_key:
        return None

    LOGO_DIRECTORY.mkdir(parents=True, exist_ok=True)
    logo_path = LOGO_DIRECTORY / f"{logo_key}.png"
    if not logo_path.exists():
        try:
            response = requests.get(
                f"https://a.espncdn.com/i/teamlogos/nfl/500/{logo_key}.png",
                timeout=5,
            )
            response.raise_for_status()
            logo_path.write_bytes(response.content)
        except requests.RequestException:
            return None

    pixmap = QPixmap(str(logo_path))
    return QIcon(pixmap) if not pixmap.isNull() else None


class FantasyFootballWindow(QMainWindow):

    # ============================================================
    # Function Name: __init__
    #
    # Parameters:
    #   None.
    #
    # Return:
    #   None. Initializes the desktop roster window.
    # ============================================================
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fantasy Football")
        self.resize(1000, 650)

        self.TeamSelector = QComboBox()
        self.RefreshButton = QPushButton("Refresh")
        self.WeekLabel = QLabel()
        self.StartersList = QListWidget()
        self.BenchList = QListWidget()
        self.StartersList.setIconSize(QSize(28, 28))
        self.BenchList.setIconSize(QSize(28, 28))

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Team:"))
        controls_layout.addWidget(self.TeamSelector, 1)
        controls_layout.addWidget(self.RefreshButton)

        rosters_layout = QHBoxLayout()
        starters_layout = QVBoxLayout()
        starters_layout.addWidget(QLabel("Starters"))
        starters_layout.addWidget(self.StartersList)
        bench_layout = QVBoxLayout()
        bench_layout.addWidget(QLabel("Bench"))
        bench_layout.addWidget(self.BenchList)
        rosters_layout.addLayout(starters_layout)
        rosters_layout.addLayout(bench_layout)

        layout = QVBoxLayout()
        layout.addLayout(controls_layout)
        layout.addWidget(self.WeekLabel)
        layout.addLayout(rosters_layout)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.TeamSelector.currentIndexChanged.connect(self.DisplaySelectedRoster)
        self.RefreshButton.clicked.connect(self.LoadData)
        self.LoadData()

    # ============================================================
    # Function Name: LoadData
    #
    # Parameters:
    #   None.
    #
    # Return:
    #   None. Fetches current league data and populates the team selector.
    # ============================================================
    def LoadData(self):
        self.WeekLabel.setText("Loading league data...")
        QApplication.processEvents()
        self.LeagueData = GetCurrentLeagueData()
        self.Players = Players(self.LeagueData["players"])
        self.RosterView = Rosters(
            self.Players,
            self.LeagueData["users"],
            self.LeagueData["player_stats"],
            self.LeagueData["player_projections"],
            self.LeagueData.get("roster_positions"),
        )

        self.TeamSelector.blockSignals(True)
        self.TeamSelector.clear()
        for roster in self.LeagueData["rosters"]:
            self.TeamSelector.addItem(
                self.RosterView.GetTeamName(roster["owner_id"])
            )
        self.TeamSelector.blockSignals(False)

        self.WeekLabel.setText(
            f"NFL {self.LeagueData['season']} "
            f"{self.LeagueData['season_type']} season, "
            f"week {self.LeagueData['week']}"
        )
        self.DisplaySelectedRoster()

    # ============================================================
    # Function Name: DisplaySelectedRoster
    #
    # Parameters:
    #   None.
    #
    # Return:
    #   None. Displays the selected team's starters and bench.
    # ============================================================
    def DisplaySelectedRoster(self):
        index = self.TeamSelector.currentIndex()
        if index < 0 or not hasattr(self, "LeagueData"):
            return

        roster = self.LeagueData["rosters"][index]
        self.StartersList.clear()
        self.BenchList.clear()
        for player_id, lineup_slot in self.RosterView.GetStarterEntries(roster):
            self.AddPlayerItem(self.StartersList, player_id, lineup_slot)
        for player_id in self.RosterView.GetBench(roster):
            self.AddPlayerItem(self.BenchList, player_id)

    def AddPlayerItem(self, player_list, player_id, lineup_slot=None):
        player = self.Players.GetPlayer(player_id) or {}
        matchup = self.GetPlayerMatchup(player_id, player)
        line = self.RosterView.FormatPlayerLine(player_id, lineup_slot)
        if matchup:
            line = f"{line}  |  {matchup}"
        item = QListWidgetItem(line)
        logo = GetTeamLogo(player.get("team"))
        if logo:
            item.setIcon(logo)
        player_list.addItem(item)

    def GetPlayerMatchup(self, player_id, player):
        player_id = str(player_id)
        player_stats = self.LeagueData["player_stats"].get(player_id, {})
        projections = self.LeagueData["player_projections"].get(player_id, {})
        opponent = player_stats.get("opponent") or projections.get("opponent")
        if not opponent:
            return ""

        opponent_name = TEAM_NAMES.get(opponent.upper(), opponent)
        return f"vs {opponent_name}"


# ============================================================
# Function Name: main
#
# Parameters:
#   None.
#
# Return:
#   None. Starts the PyQt desktop application.
# ============================================================
def main():
    app = QApplication(sys.argv)
    window = FantasyFootballWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
