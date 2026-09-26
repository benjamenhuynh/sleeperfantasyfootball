"""Reusable fantasy scoring and player usage metrics."""


SCORING_STAT_SOURCES = {
    "pass_yd": ("pass_yd", "passing_yards", "pass_yards"),
    "pass_td": ("pass_td", "passing_tds", "pass_tds"),
    "pass_int": ("pass_int", "passing_interceptions", "interceptions"),
    "pass_2pt": ("pass_2pt", "passing_2pt_conversions"),
    "pass_att": ("pass_att", "attempts", "pass_attempts"),
    "pass_cmp": ("pass_cmp", "completions", "pass_completions"),
    "pass_inc": ("pass_inc", "incompletions"),
    "pass_sack": ("pass_sack", "sacks_suffered"),
    "pass_fd": ("pass_fd", "passing_first_downs"),
    "rush_yd": ("rush_yd", "rushing_yards", "rush_yards"),
    "rush_td": ("rush_td", "rushing_tds", "rush_tds"),
    "rush_2pt": ("rush_2pt", "rushing_2pt_conversions"),
    "rush_fd": ("rush_fd", "rushing_first_downs"),
    "rec": ("rec", "receptions"),
    "rec_yd": ("rec_yd", "receiving_yards", "rec_yards"),
    "rec_td": ("rec_td", "receiving_tds", "rec_tds"),
    "rec_2pt": ("rec_2pt", "receiving_2pt_conversions"),
    "rec_fd": ("rec_fd", "receiving_first_downs"),
    "fum_lost": ("fum_lost", "fumbles_lost"),
}

SCORING_BONUSES = {
    "bonus_pass_yd_300": ("pass_yd", 300, 400),
    "bonus_pass_yd_400": ("pass_yd", 400, None),
    "bonus_rush_yd_100": ("rush_yd", 100, 200),
    "bonus_rush_yd_200": ("rush_yd", 200, None),
    "bonus_rec_yd_100": ("rec_yd", 100, 200),
    "bonus_rec_yd_200": ("rec_yd", 200, None),
    "bonus_rush_rec_yd_100": ("rush_rec_yd", 100, 200),
    "bonus_rush_rec_yd_200": ("rush_rec_yd", 200, None),
}


def _number(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _stat_value(stats, scoring_stat):
    if scoring_stat == "rush_rec_yd":
        return _stat_value(stats, "rush_yd") + _stat_value(stats, "rec_yd")
    for source in SCORING_STAT_SOURCES[scoring_stat]:
        value = _number(stats.get(source))
        if value is not None:
            return value
    if scoring_stat == "fum_lost":
        fumble_fields = (
            "sack_fumbles_lost",
            "rushing_fumbles_lost",
            "receiving_fumbles_lost",
        )
        values = [_number(stats.get(field)) for field in fumble_fields]
        if any(value is not None for value in values):
            return sum(value or 0 for value in values)
    return 0.0


def CalculateFantasyPoints(player_stats, scoring_settings, position=None):
    """Score a stat line with Sleeper-style settings.

    Returns None when a nonzero scoring rule is missing from the supplied stat
    line and has no supported nflverse stat mapping.
    """
    if not player_stats or not scoring_settings:
        return None

    supported_settings = set(SCORING_STAT_SOURCES) | set(SCORING_BONUSES)
    unsupported = [
        key for key, value in scoring_settings.items()
        if key not in supported_settings
        and key != "bonus_rec_te"
        and key not in player_stats
        and _number(value) not in (None, 0.0)
        and not (
            position in {"QB", "RB", "WR", "TE"}
            and (
                key.startswith((
                    "fgm_", "fgmiss_", "xpm", "xpmiss", "def_", "idp_",
                    "pts_allow_", "st_",
                ))
                or key in {"sack", "safe", "blk_kick", "fum_rec"}
            )
        )
        and not (
            key == "bonus_rec_te"
            and position in {"QB", "RB", "WR", "K", "DEF", "DST"}
        )
    ]
    if unsupported:
        return None

    has_stats = any(
        source in player_stats
        for sources in SCORING_STAT_SOURCES.values()
        for source in sources
    )
    if not has_stats:
        return None

    points = 0.0
    for setting, points_per_stat in scoring_settings.items():
        points_per_stat = _number(points_per_stat) or 0.0
        if not points_per_stat:
            continue
        if setting in SCORING_STAT_SOURCES:
            stat_value = _stat_value(player_stats, setting)
        elif setting in SCORING_BONUSES:
            stat_key, lower_bound, upper_bound = SCORING_BONUSES[setting]
            metric_value = _stat_value(player_stats, stat_key)
            qualifies = metric_value >= lower_bound and (
                upper_bound is None or metric_value < upper_bound
            )
            stat_value = points_per_stat if qualifies else 0.0
            points_per_stat = 1.0
        elif setting == "bonus_rec_te":
            receptions = _number(player_stats.get("bonus_rec_te"))
            if receptions is None:
                receptions = _stat_value(player_stats, "rec") if position == "TE" else 0.0
            stat_value = receptions
        elif setting in player_stats:
            stat_value = _number(player_stats.get(setting)) or 0.0
        else:
            continue
        points += stat_value * points_per_stat
    return points


def CalculateUsageMetrics(game):
    """Calculate per-game usage rates from player stats and team totals."""
    if not game:
        return {}

    team_totals = game.get("team_totals") or {}
    carries = _number(game.get("carries"))
    targets = _number(game.get("targets"))
    receptions = _number(game.get("receptions"))
    rushing_yards = _number(game.get("rush_yards"))
    receiving_yards = _number(game.get("receiving_yards"))
    air_yards = _number(game.get("air_yards"))
    snaps = _number(game.get("offense_snaps"))
    snap_share = _number(game.get("offense_pct"))
    if snap_share is not None:
        snap_share = snap_share / 100 if snap_share > 1 else snap_share

    def divide(numerator, denominator):
        return numerator / denominator if numerator is not None and denominator else None

    return {
        "carries": carries,
        "targets": targets,
        "receptions": receptions,
        "touches": (carries or 0) + (receptions or 0),
        "offense_snaps": snaps,
        "rush_yards": rushing_yards,
        "receiving_yards": receiving_yards,
        "total_yards": (rushing_yards or 0) + (receiving_yards or 0),
        "air_yards": air_yards,
        "rush_share": divide(carries, _number(team_totals.get("carries"))),
        "target_share": divide(targets, _number(team_totals.get("targets"))),
        "air_yard_share": divide(
            air_yards, _number(team_totals.get("air_yards"))
        ),
        "snap_share": snap_share,
        "yards_per_carry": divide(rushing_yards, carries),
        "yards_per_target": divide(receiving_yards, targets),
        "yards_per_reception": divide(receiving_yards, receptions),
    }


def SummarizeUsageMetrics(games):
    """Return averages per game for a player's supplied game-log rows."""
    if not games:
        return {"games": 0, "averages": {}}

    metric_rows = [CalculateUsageMetrics(game) for game in games]
    averages = {}
    for key in metric_rows[0]:
        values = [row[key] for row in metric_rows if row.get(key) is not None]
        if values:
            averages[key] = sum(values) / len(values)
    return {"games": len(games), "averages": averages}
