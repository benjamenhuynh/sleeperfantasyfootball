"""Load and normalize nflverse player usage for the desktop comparison view."""

import json
import time
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"
CACHE_TTL_SECONDS = 6 * 60 * 60

STAT_FIELDS = {
    "attempts": "pass_attempts",
    "passing_yards": "pass_yards",
    "passing_tds": "pass_tds",
    "interceptions": "interceptions",
    "carries": "carries",
    "rushing_yards": "rush_yards",
    "rushing_tds": "rush_tds",
    "targets": "targets",
    "receptions": "receptions",
    "receiving_air_yards": "air_yards",
    "receiving_yards": "receiving_yards",
    "receiving_tds": "receiving_tds",
    "sack_fumbles_lost": "sack_fumbles_lost",
    "rushing_fumbles_lost": "rushing_fumbles_lost",
    "receiving_fumbles_lost": "receiving_fumbles_lost",
}


def _clean_id(value):
    if value is None:
        return None
    value = str(value).strip()
    return None if not value or value.upper() in {"NA", "NAN", "NONE"} else value


def _game_type(value):
    value = str(value or "REG").upper()
    if value in {"REGULAR", "REG"}:
        return "REG"
    if value in {"POSTSEASON", "POST"}:
        return "POST"
    return value


def _read_cache(cache_path):
    try:
        with cache_path.open() as cache_file:
            cached = json.load(cache_file)
        if time.time() - cache_path.stat().st_mtime < CACHE_TTL_SECONDS:
            return cached.get("players", {})
    except (OSError, ValueError, AttributeError):
        pass
    return None


def _normalize_usage(stats_rows, snap_rows, id_rows, season):
    sleeper_by_gsis = {}
    pfr_by_sleeper = {}
    for row in id_rows:
        sleeper_id = _clean_id(row.get("sleeper_id"))
        if not sleeper_id:
            continue
        gsis_id = _clean_id(row.get("gsis_id"))
        pfr_id = _clean_id(row.get("pfr_id"))
        if gsis_id:
            sleeper_by_gsis[gsis_id] = sleeper_id
        if pfr_id:
            pfr_by_sleeper[sleeper_id] = pfr_id

    snap_lookup = {}
    for row in snap_rows:
        pfr_id = _clean_id(row.get("pfr_player_id"))
        if not pfr_id:
            continue
        key = (
            pfr_id,
            str(row.get("week", "")),
            _game_type(row.get("game_type")),
        )
        snap_lookup[key] = row

    team_week_totals = {}
    team_total_fields = {
        "carries": "carries",
        "targets": "targets",
        "receiving_air_yards": "air_yards",
    }
    for row in stats_rows:
        if row.get("season") is not None and int(row["season"]) != int(season):
            continue
        team = _clean_id(row.get("team"))
        if not team:
            continue
        key = (
            team.upper(),
            str(row.get("week", "")),
            _game_type(row.get("season_type")),
        )
        totals = team_week_totals.setdefault(key, {})
        for source_field, target_field in team_total_fields.items():
            value = row.get(source_field)
            if value is not None:
                totals[target_field] = totals.get(target_field, 0) + value

    usage_by_player = {}
    for row in stats_rows:
        if row.get("season") is not None and int(row["season"]) != int(season):
            continue
        sleeper_id = sleeper_by_gsis.get(_clean_id(row.get("player_id")))
        if not sleeper_id:
            continue

        week = str(row.get("week", ""))
        game_type = _game_type(row.get("season_type"))
        pfr_id = pfr_by_sleeper.get(sleeper_id)
        snap_row = snap_lookup.get((pfr_id, week, game_type)) if pfr_id else None

        game = {
            "week": int(week) if week.isdigit() else week,
            "team": row.get("team"),
            "opponent": row.get("opponent_team"),
        }
        for source_field, target_field in STAT_FIELDS.items():
            value = row.get(source_field)
            if value is not None:
                game[target_field] = value
        if snap_row:
            game["offense_snaps"] = snap_row.get("offense_snaps")
            game["offense_pct"] = snap_row.get("offense_pct")
        game["team_totals"] = team_week_totals.get(
            ((row.get("team") or "").upper(), week, game_type), {}
        )

        usage_by_player.setdefault(sleeper_id, []).append(game)

    for games in usage_by_player.values():
        games.sort(key=lambda game: game["week"] if isinstance(game["week"], int) else 0)
    return usage_by_player


def LoadSeasonPlayerUsage(season):
    """Return current-season game logs keyed by Sleeper player ID.

    nflreadpy is optional. Downloaded data is cached locally for six hours.
    """
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    cache_path = DATA_DIRECTORY / f"nflverse_usage_v2_{season}.json"
    cached = _read_cache(cache_path)
    if cached is not None:
        return {"players": cached, "error": None}

    try:
        import nflreadpy as nfl
    except ImportError:
        return {
            "players": {},
            "error": "Install optional NFL data support with "
                     "pip install -r requirements-nfl-data.txt.",
        }

    try:
        stats_rows = nfl.load_player_stats(seasons=[int(season)]).to_dicts()
        snap_rows = nfl.load_snap_counts(seasons=[int(season)]).to_dicts()
        id_rows = nfl.load_ff_playerids().to_dicts()
        players = _normalize_usage(stats_rows, snap_rows, id_rows, season)
        with cache_path.open("w") as cache_file:
            json.dump({"players": players}, cache_file)
        return {"players": players, "error": None}
    except Exception as error:
        return {"players": {}, "error": f"Could not load nflverse data: {error}"}
