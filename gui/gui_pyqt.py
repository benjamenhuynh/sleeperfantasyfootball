import sys
from pathlib import Path

import requests

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QCompleter,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QListWidgetItem,
)
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from analysis import GetPositionMatchupHistory
from analytics import (
    CalculateFantasyPoints,
    CalculateUsageMetrics,
    SummarizeUsageMetrics,
)
from league import GetCurrentLeagueData, GetHistoricalMatchupData
from nfl_data import LoadSeasonPlayerUsage
from players import Players
from rosters import Rosters
from stats import FormatPlayerStats


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
        self.PlayerSearch = QLineEdit()
        self.PlayerSearch.setPlaceholderText("Search player by name")
        self.PlayerSearchButton = QPushButton("Find Player")
        self.CompareButton = QPushButton("Start / Sit Comparison")
        self.SearchResultLabel = QLabel("Search for a player to see their fantasy team.")
        self.SearchResultLabel.setWordWrap(True)
        self.WeekLabel = QLabel()
        self.StartersList = QListWidget()
        self.BenchList = QListWidget()
        self.StartersList.setIconSize(QSize(28, 28))
        self.BenchList.setIconSize(QSize(28, 28))

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Team:"))
        controls_layout.addWidget(self.TeamSelector, 1)
        controls_layout.addWidget(self.RefreshButton)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.PlayerSearch, 1)
        search_layout.addWidget(self.PlayerSearchButton)
        search_layout.addWidget(self.CompareButton)

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
        layout.addLayout(search_layout)
        layout.addWidget(self.SearchResultLabel)
        layout.addWidget(self.WeekLabel)
        layout.addLayout(rosters_layout)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.TeamSelector.currentIndexChanged.connect(self.DisplaySelectedRoster)
        self.RefreshButton.clicked.connect(self.LoadData)
        self.PlayerSearch.returnPressed.connect(self.SearchPlayer)
        self.PlayerSearchButton.clicked.connect(self.SearchPlayer)
        self.CompareButton.clicked.connect(self.OpenComparison)
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

        player_names = sorted({
            self.Players.GetPlayerName(player_id)
            for player_id in self.LeagueData["players"]
        })
        completer = QCompleter(player_names, self.PlayerSearch)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.PlayerSearch.setCompleter(completer)

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
        opponent = self.GetPlayerOpponent(player_id)
        if not opponent:
            return ""
        opponent_name = TEAM_NAMES.get(opponent.upper(), opponent)
        return f"vs {opponent_name}"

    def GetPlayerOpponent(self, player_id):
        player_id = str(player_id)
        player_stats = self.LeagueData["player_stats"].get(player_id, {})
        projections = self.LeagueData["player_projections"].get(player_id, {})
        return player_stats.get("opponent") or projections.get("opponent")

    def GetFantasyRoster(self, player_id):
        player_id = str(player_id)
        for roster in self.LeagueData["rosters"]:
            roster_players = {str(item) for item in roster.get("players", [])}
            if player_id not in roster_players:
                continue
            owner = self.RosterView.GetTeamName(roster["owner_id"])
            starters = {str(item) for item in roster.get("starters", [])}
            status = "starter" if player_id in starters else "bench"
            return f"{owner} ({status})"
        return "Free agent"

    def FindMatchingPlayers(self, query):
        query = query.strip().casefold()
        if not query:
            return []
        exact = []
        partial = []
        for player_id, player in self.LeagueData["players"].items():
            name = self.Players.GetPlayerName(player_id)
            if name.casefold() == query:
                exact.append((str(player_id), player, name))
            elif query in name.casefold():
                partial.append((str(player_id), player, name))
        return exact or partial

    def SearchPlayer(self):
        matches = self.FindMatchingPlayers(self.PlayerSearch.text())
        if not matches:
            self.SearchResultLabel.setText("No player found. Try another name.")
            return

        lines = []
        for player_id, player, name in matches[:8]:
            position = player.get("position", "?")
            nfl_team = player.get("team")
            nfl_label = TEAM_NAMES.get(nfl_team, nfl_team) if nfl_team else "NFL team unknown"
            lines.append(
                f"{name} ({position}, {nfl_label}) — Fantasy team: "
                f"{self.GetFantasyRoster(player_id)}"
            )
        if len(matches) > 8:
            lines.append(f"Showing 8 of {len(matches)} matches. Refine the search.")
        self.SearchResultLabel.setText("\n".join(lines))

    def OpenComparison(self):
        dialog = PlayerComparisonDialog(self)
        dialog.exec()


class PlayerComparisonDialog(QDialog):
    def __init__(self, fantasy_window):
        super().__init__(fantasy_window)
        self.FantasyWindow = fantasy_window
        self.setWindowTitle("Start / Sit Comparison")
        self.resize(900, 760)

        self.PlayerSelectors = []
        selectors_layout = QHBoxLayout()
        player_records = sorted(
            fantasy_window.LeagueData["players"].items(),
            key=lambda item: fantasy_window.Players.GetPlayerName(item[0]).casefold(),
        )
        for placeholder in ("Select first player", "Select second player"):
            selector = QComboBox()
            selector.setEditable(True)
            selector.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            selector.addItem(placeholder, None)
            for player_id, player in player_records:
                player_name = fantasy_window.Players.GetPlayerName(player_id)
                position = player.get("position", "?")
                selector.addItem(f"{player_name} ({position}) [{player_id}]", str(player_id))
            selector.setCurrentIndex(0)
            selector.lineEdit().setPlaceholderText(placeholder)
            selector.setMaxVisibleItems(15)
            completer = selector.completer()
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.PlayerSelectors.append(selector)
            selectors_layout.addWidget(selector)

        self.ProjectionScoringSelector = QComboBox()
        self.ProjectionScoringSelector.addItem("Full PPR", "pts_ppr")
        self.ProjectionScoringSelector.addItem("Half PPR", "pts_half_ppr")
        self.ProjectionSummary = QLabel("Select players to view their projections.")
        self.ProjectionSummary.setWordWrap(True)
        scoring_layout = QHBoxLayout()
        scoring_layout.addWidget(QLabel("Scoring format:"))
        scoring_layout.addWidget(self.ProjectionScoringSelector)
        scoring_layout.addStretch(1)

        self.CompareNowButton = QPushButton("Compare")
        self.UsageMetricSelector = QComboBox()
        self.UsageMetrics = {
            "Targets": lambda game: game.get("targets"),
            "Carries": lambda game: game.get("carries"),
            "Receptions": lambda game: game.get("receptions"),
            "Offensive snaps": lambda game: game.get("offense_snaps"),
            "Snap share (%)": lambda game: self.GetUsageMetric(
                game, "snap_share", True
            ),
            "Target share (%)": lambda game: self.GetUsageMetric(
                game, "target_share", True
            ),
            "Rush share (%)": lambda game: self.GetUsageMetric(
                game, "rush_share", True
            ),
            "Air yards": lambda game: game.get("air_yards"),
            "Air-yard share (%)": lambda game: self.GetUsageMetric(
                game, "air_yard_share", True
            ),
            "Yards per carry": lambda game: self.GetUsageMetric(
                game, "yards_per_carry"
            ),
            "Yards per target": lambda game: self.GetUsageMetric(
                game, "yards_per_target"
            ),
            "Yards per reception": lambda game: self.GetUsageMetric(
                game, "yards_per_reception"
            ),
            "Passing touchdowns": lambda game: game.get("pass_tds"),
            "Rushing touchdowns": lambda game: game.get("rush_tds"),
            "Receiving touchdowns": lambda game: game.get("receiving_tds"),
            "Receiving yards": lambda game: game.get("receiving_yards"),
            "Rushing yards": lambda game: game.get("rush_yards"),
            "Passing attempts": lambda game: game.get("pass_attempts"),
            "Rushing + receiving yards": lambda game: (game.get("rush_yards", 0) or 0)
            + (game.get("receiving_yards", 0) or 0),
            "Touches": lambda game: (game.get("carries", 0) or 0)
            + (game.get("receptions", 0) or 0),
        }
        self.UsageDescriptions = {
            "Targets": "How many passes were thrown to the player, including incomplete passes.",
            "Carries": "How many rushing attempts the player had.",
            "Receptions": "How many passes the player caught.",
            "Offensive snaps": "How many offensive plays the player was on the field for.",
            "Snap share (%)": "The player's share of their team's offensive snaps.",
            "Target share (%)": "The player's share of their team's targets.",
            "Rush share (%)": "The player's share of their team's rushing attempts.",
            "Air yards": "The total distance downfield of passes targeted at the player, before the catch.",
            "Air-yard share (%)": "The player's share of their team's receiving air yards.",
            "Yards per carry": "Rushing yards divided by rushing attempts.",
            "Yards per target": "Receiving yards divided by targets; includes incomplete targets in the denominator.",
            "Yards per reception": "Receiving yards divided by catches.",
            "Passing touchdowns": "Touchdowns thrown by the player.",
            "Rushing touchdowns": "Touchdowns scored on the player's rushing attempts.",
            "Receiving touchdowns": "Touchdowns scored on passes caught by the player.",
            "Receiving yards": "Yards gained on passes caught by the player.",
            "Rushing yards": "Yards gained on the player's rushing attempts.",
            "Passing attempts": "Passes thrown by the player; sacks are not pass attempts.",
            "Rushing + receiving yards": "The player's rushing yards plus receiving yards.",
            "Touches": "Carries plus receptions. It does not include targets that were not caught.",
        }
        self.UsageMetricSelector.addItems(self.UsageMetrics)
        self.UsageMetricDescription = QLabel()
        self.UsageMetricDescription.setWordWrap(True)
        self.UpdateUsageDescription(self.UsageMetricSelector.currentText())
        self.UsageChart = UsageTrendChart()
        self.UsageSeries = []
        self.CompareResult = QLabel("Choose two players to compare their current stats or projections.")
        self.CompareResult.setWordWrap(True)
        self.CompareResult.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.CompareDetails = QScrollArea()
        self.CompareDetails.setWidgetResizable(True)
        self.CompareDetails.setWidget(self.CompareResult)
        self.CompareDetails.setMinimumHeight(170)

        layout = QVBoxLayout()
        layout.addLayout(selectors_layout)
        layout.addLayout(scoring_layout)
        layout.addWidget(self.CompareNowButton)
        layout.addWidget(self.ProjectionSummary)
        layout.addWidget(QLabel("Recent usage trend (last five games):"))
        layout.addWidget(self.UsageMetricSelector)
        layout.addWidget(self.UsageMetricDescription)
        layout.addWidget(self.UsageChart)
        layout.addWidget(self.CompareDetails)
        self.setLayout(layout)
        self.CompareNowButton.clicked.connect(self.ComparePlayers)
        self.ProjectionScoringSelector.currentIndexChanged.connect(
            self.UpdateScoringDisplay
        )
        self.UsageMetricSelector.currentTextChanged.connect(self.UpdateUsageChart)
        self.UsageMetricSelector.currentTextChanged.connect(self.UpdateUsageDescription)
        self.LastComparedPlayerIds = []
        self.ComparisonContext = None

    @staticmethod
    def GetSnapShare(game):
        return PlayerComparisonDialog.GetUsageMetric(game, "snap_share", True)

    @staticmethod
    def GetUsageMetric(game, metric, as_percentage=False):
        value = CalculateUsageMetrics(game).get(metric)
        if value is not None and as_percentage:
            return value * 100
        return value

    def GetSelectedScoringSettings(self):
        settings = dict(
            self.FantasyWindow.LeagueData.get("scoring_settings") or {}
        )
        if not settings:
            return None
        settings["rec"] = (
            1.0
            if self.ProjectionScoringSelector.currentData() == "pts_ppr"
            else 0.5
        )
        return settings

    def UpdateUsageChart(self):
        metric = self.UsageMetricSelector.currentText()
        self.UsageChart.SetSeries(self.UsageSeries, self.UsageMetrics[metric], metric)

    def UpdateUsageDescription(self, metric):
        self.UsageMetricDescription.setText(self.UsageDescriptions.get(metric, ""))

    def UpdateProjectionSummary(self):
        if not self.LastComparedPlayerIds:
            return
        points_key = self.ProjectionScoringSelector.currentData()
        points_label = self.ProjectionScoringSelector.currentText()
        lines = []
        for player_id in self.LastComparedPlayerIds:
            name = self.FantasyWindow.Players.GetPlayerName(player_id)
            projection = self.FantasyWindow.LeagueData["player_projections"].get(
                str(player_id)
            )
            scored_points = projection.get(points_key) if projection else None
            if projection and scored_points is not None:
                display_projection = dict(projection)
                display_projection[points_key] = scored_points
                projection_text = FormatPlayerStats(
                    display_projection,
                    label="Proj",
                    points_key=points_key,
                    points_label=points_label,
                )
            else:
                projection_text = "Projection unavailable"
            lines.append(f"{name}: {projection_text}")
        self.ProjectionSummary.setText("\n".join(lines))

    def UpdateScoringDisplay(self):
        self.UpdateProjectionSummary()
        if self.ComparisonContext is not None:
            self.RenderComparisonText()

    def ComparePlayers(self):
        player_ids = [selector.currentData() for selector in self.PlayerSelectors]
        valid_selections = all(
            player_id and selector.currentIndex() >= 0
            and selector.currentText() == selector.itemText(selector.currentIndex())
            for selector, player_id in zip(self.PlayerSelectors, player_ids)
        )
        if not valid_selections:
            self.LastComparedPlayerIds = []
            self.ComparisonContext = None
            self.ProjectionSummary.setText("Select both players to view their projections.")
            self.CompareResult.setText("Select both players from the suggestion list.")
            return

        self.LastComparedPlayerIds = player_ids
        self.UpdateProjectionSummary()

        opponents = [
            self.FantasyWindow.GetPlayerOpponent(player_id)
            for player_id in player_ids
        ]
        history_data = None
        if any(opponents) and int(self.FantasyWindow.LeagueData["week"]) > 1:
            self.CompareResult.setText("Loading past matchup stats...")
            QApplication.processEvents()
            history_data = GetHistoricalMatchupData(
                self.FantasyWindow.LeagueData["season"],
                self.FantasyWindow.LeagueData["week"],
                self.FantasyWindow.LeagueData["season_type"],
            )

        self.CompareResult.setText("Loading recent NFL usage...")
        QApplication.processEvents()
        usage_data = LoadSeasonPlayerUsage(
            self.FantasyWindow.LeagueData["season"]
        )

        self.ComparisonContext = {
            "player_ids": player_ids,
            "opponents": opponents,
            "history_data": history_data,
            "usage_data": usage_data,
        }
        self.RenderComparisonText()

    def RenderComparisonText(self):
        context = self.ComparisonContext
        if context is None:
            return

        points_key = self.ProjectionScoringSelector.currentData()
        points_label = self.ProjectionScoringSelector.currentText()
        scoring_settings = self.GetSelectedScoringSettings()
        player_ids = context["player_ids"]
        history_data = context["history_data"]
        usage_data = context["usage_data"]
        lines = []
        self.UsageSeries = []
        for player_id, opponent in zip(player_ids, context["opponents"]):
            player = self.FantasyWindow.Players.GetPlayer(player_id) or {}
            line = self.FantasyWindow.RosterView.FormatPlayerLine(
                player_id,
                points_key=points_key,
                points_label=points_label,
                scoring_settings=scoring_settings,
            )
            nfl_team = player.get("team")
            if nfl_team:
                nfl_name = TEAM_NAMES.get(nfl_team, nfl_team)
                line += f"\nNFL team: {nfl_name}"
            line += f"\nFantasy team: {self.FantasyWindow.GetFantasyRoster(player_id)}"
            recent_usage = usage_data["players"].get(str(player_id), [])
            if recent_usage:
                player_name = self.FantasyWindow.Players.GetPlayerName(player_id)
                self.UsageSeries.append((player_name, recent_usage[-5:]))
                usage_summary = SummarizeUsageMetrics(recent_usage[-5:])["averages"]
                metric_labels = (
                    ("targets", "Targets"),
                    ("carries", "Carries"),
                    ("touches", "Touches"),
                    ("target_share", "Target share"),
                    ("rush_share", "Rush share"),
                    ("snap_share", "Snap share"),
                    ("air_yards", "Air yards"),
                    ("air_yard_share", "Air-yard share"),
                    ("yards_per_carry", "Yards/carry"),
                    ("yards_per_target", "Yards/target"),
                    ("yards_per_reception", "Yards/reception"),
                )
                summary_parts = []
                for key, label in metric_labels:
                    value = usage_summary.get(key)
                    if value is None:
                        continue
                    rendered = (
                        f"{value * 100:.0f}%"
                        if key.endswith("share")
                        else f"{value:.1f}"
                    )
                    summary_parts.append(f"{label} {rendered}")
                if summary_parts:
                    line += (
                        "\nUsage metrics (last five games, per-game avg): "
                        + ", ".join(summary_parts)
                    )
                line += "\nRecent usage: " + " | ".join(
                    self.FormatUsageGame(game)
                    for game in reversed(recent_usage[-5:])
                )
            elif not usage_data["error"]:
                line += "\nNo recent nflverse usage found for this player."
            matchup = self.FantasyWindow.GetPlayerMatchup(player_id, player)
            if matchup:
                line += f"\nMatchup: {matchup}"
            if history_data and opponent:
                history = GetPositionMatchupHistory(
                    player.get("position", ""),
                    opponent,
                    self.FantasyWindow.LeagueData["players"],
                    history_data["weekly_stats"],
                    history_data["schedule"],
                    points_key=points_key,
                    scoring_label=points_label,
                    scoring_settings=scoring_settings,
                )
                if history and history["count"]:
                    line += (
                        f"\nPast {history['position_name']} vs "
                        f"{TEAM_NAMES.get(opponent.upper(), opponent)}: "
                        f"{history['average_points']:.1f} {points_label} average "
                        f"across {history['count']} player-games"
                    )
                    recent = history["performances"][:5]
                    recent_lines = [
                        f"Week {game['week']}: {game['player']} "
                        f"{game['points']:.1f} {points_label}"
                        for game in recent
                    ]
                    line += "\nRecent: " + "; ".join(recent_lines)
                elif history:
                    line += (
                        f"\nNo past {history['position_name'].lower()} "
                        f"{points_label} results found vs "
                        f"{TEAM_NAMES.get(opponent.upper(), opponent)}."
                    )
            lines.append(line)

        self.UpdateUsageChart()

        header = (
            f"NFL {self.FantasyWindow.LeagueData['season']} week "
            f"{self.FantasyWindow.LeagueData['week']}"
        )
        if usage_data["error"]:
            header += f"\n{usage_data['error']}"
        self.CompareResult.setText(f"{header}\n\n" + "\n\n".join(lines))

    @staticmethod
    def FormatUsageGame(game):
        def display(value):
            number = float(value)
            return str(int(number)) if number.is_integer() else f"{number:.1f}"

        details = [f"Week {game['week']}"]
        if game.get("pass_attempts"):
            pass_line = (
                f"{display(game['pass_attempts'])} pass att, "
                f"{display(game.get('pass_yards', 0))} pass yds"
            )
            if game.get("pass_tds"):
                pass_line += f", {display(game['pass_tds'])} pass TD"
            details.append(pass_line)
        if game.get("carries"):
            rush_line = (
                f"{display(game['carries'])} carries, "
                f"{display(game.get('rush_yards', 0))} rush yds"
            )
            if game.get("rush_tds"):
                rush_line += f", {display(game['rush_tds'])} rush TD"
            details.append(rush_line)
        if game.get("targets"):
            receiving_line = (
                f"{display(game['targets'])} targets, "
                f"{display(game.get('receptions', 0))} rec, "
                f"{display(game.get('receiving_yards', 0))} rec yds"
            )
            if game.get("receiving_tds"):
                receiving_line += f", {display(game['receiving_tds'])} rec TD"
            details.append(receiving_line)
        if game.get("offense_snaps") is not None:
            snap_line = f"{display(game['offense_snaps'])} offensive snaps"
            snap_pct = game.get("offense_pct")
            if snap_pct is not None:
                snap_pct = float(snap_pct)
                snap_pct = snap_pct * 100 if snap_pct <= 1 else snap_pct
                snap_line += f" ({snap_pct:.0f}%)"
            details.append(snap_line)
        return ", ".join(details)


class UsageTrendChart(QWidget):
    COLORS = (QColor("#55aaff"), QColor("#ffb454"))

    def __init__(self, parent=None):
        super().__init__(parent)
        self.Series = []
        self.ValueForGame = lambda game: None
        self.MetricName = "Usage"
        self.setMinimumHeight(250)

    def SetSeries(self, series, value_for_game, metric_name):
        self.Series = series
        self.ValueForGame = value_for_game
        self.MetricName = metric_name
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        text_color = self.palette().color(self.foregroundRole())
        painter.setPen(text_color)
        painter.drawText(12, 20, f"{self.MetricName} by game")

        if not any(games for _, games in self.Series):
            painter.drawText(12, 52, "Compare two players to graph their recent usage.")
            return

        weeks = sorted({
            game["week"]
            for _, games in self.Series
            for game in games
            if isinstance(game.get("week"), int)
        })
        values = []
        for _, games in self.Series:
            for game in games:
                value = self.ValueForGame(game)
                if value is not None:
                    values.append(float(value))
        if not weeks or not values:
            painter.drawText(12, 52, f"No {self.MetricName.lower()} data available for these players.")
            return

        left, top, right, bottom = 58, 40, self.width() - 20, self.height() - 36
        plot_width = max(1, right - left)
        plot_height = max(1, bottom - top)
        max_value = max(values)
        y_max = max(1.0, max_value * 1.15)
        painter.setPen(QPen(QColor("#777777"), 1))
        for tick in range(5):
            y = bottom - plot_height * tick / 4
            tick_value = y_max * tick / 4
            painter.drawLine(left, round(y), right, round(y))
            painter.setPen(text_color)
            painter.drawText(4, round(y) + 4, f"{tick_value:.0f}")
            painter.setPen(QPen(QColor("#777777"), 1))

        x_positions = {}
        for index, week in enumerate(weeks):
            x = left + plot_width * index / max(1, len(weeks) - 1)
            x_positions[week] = x
            painter.setPen(text_color)
            painter.drawText(round(x) - 14, self.height() - 8, f"W{week}")

        for series_index, (name, games) in enumerate(self.Series[:2]):
            color = self.COLORS[series_index]
            values_by_week = {}
            for game in games:
                week = game.get("week")
                value = self.ValueForGame(game)
                if week in x_positions and value is not None:
                    values_by_week[week] = float(value)
            ordered_points = [
                (x_positions[week], bottom - plot_height * value / y_max)
                for week, value in sorted(values_by_week.items())
            ]
            painter.setPen(QPen(color, 2))
            for first, second in zip(ordered_points, ordered_points[1:]):
                painter.drawLine(round(first[0]), round(first[1]), round(second[0]), round(second[1]))
            for x, y in ordered_points:
                painter.setBrush(color)
                painter.drawEllipse(round(x) - 4, round(y) - 4, 8, 8)

            legend_x = left + series_index * min(230, max(140, plot_width // 2))
            painter.setPen(QPen(color, 3))
            painter.drawLine(legend_x, 30, legend_x + 18, 30)
            painter.setPen(text_color)
            painter.drawText(legend_x + 24, 34, name[:24])


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
