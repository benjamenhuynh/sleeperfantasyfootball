"""Higher-level fantasy analysis utilities."""

from analytics import CalculateFantasyPoints


POSITION_NAMES = {
    "QB": "Quarterbacks",
    "RB": "Running backs",
    "WR": "Wide receivers",
    "TE": "Tight ends",
    "K": "Kickers",
    "DEF": "Defenses",
    "DST": "Defenses",
}


def GetPositionMatchupHistory(
    position,
    opponent,
    players,
    weekly_stats,
    schedule,
    points_key="pts_ppr",
    scoring_label="PPR",
    scoring_settings=None,
):
    """Summarize fantasy scores for a position against one NFL defense."""
    opponent = str(opponent or "").upper()
    if not opponent:
        return None

    schedule_opponents = {}
    for game in schedule or []:
        if game.get("status") == "canceled":
            continue
        try:
            week = str(game["week"])
        except (KeyError, TypeError):
            continue
        home = game.get("home")
        away = game.get("away")
        if home and away:
            schedule_opponents[(week, home.upper())] = away.upper()
            schedule_opponents[(week, away.upper())] = home.upper()

    performances = []
    for week, stats_by_player in weekly_stats.items():
        for player_id, stats in stats_by_player.items():
            player = players.get(str(player_id), {})
            if player.get("position") != position:
                continue
            player_team = (player.get("team") or "").upper()
            player_opponent = stats.get("opponent") or schedule_opponents.get(
                (str(week), player_team)
            )
            points = CalculateFantasyPoints(
                stats, scoring_settings, position=position
            )
            if points is None:
                points = stats.get(points_key)
            if (not player_opponent
                    or str(player_opponent).upper() != opponent
                    or points is None):
                continue
            try:
                points = float(points)
            except (TypeError, ValueError):
                continue
            performances.append({
                "week": int(week),
                "player": player.get("full_name") or
                          f"{player.get('first_name', '')} {player.get('last_name', '')}".strip(),
                "points": points,
            })

    performances.sort(key=lambda item: item["week"], reverse=True)
    if not performances:
        return {
            "position_name": POSITION_NAMES.get(position, position),
            "opponent": opponent,
            "count": 0,
            "average_ppr": None,
            "average_points": None,
            "scoring_label": scoring_label,
            "performances": [],
        }

    average_points = sum(item["points"] for item in performances) / len(performances)
    return {
        "position_name": POSITION_NAMES.get(position, position),
        "opponent": opponent,
        "count": len(performances),
        "average_ppr": average_points,
        "average_points": average_points,
        "scoring_label": scoring_label,
        "performances": performances,
    }
