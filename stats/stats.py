# ============================================================
# Function Name: FormatPlayerStats
#
# Parameters:
#   stats: dictionary of one player's stats, or None when unavailable.
#
# Return:
#   Readable summary of common passing, rushing, receiving, and PPR stats.
# ============================================================
def FormatPlayerStats(stats, label=None):
    if not stats:
        return "Stats unavailable" if label is None else f"{label} unavailable"

    fields = (
        ("pass_yd", "Pass Yds"),
        ("pass_td", "Pass TD"),
        ("rush_yd", "Rush Yds"),
        ("rush_td", "Rush TD"),
        ("rec", "Rec"),
        ("rec_yd", "Rec Yds"),
        ("rec_td", "Rec TD"),
        ("pts_ppr", "PPR"),
    )
    parts = [f"{field_label} {stats[key]}" for key, field_label in fields if key in stats]
    if not parts:
        return "No stats recorded" if label is None else f"{label} unavailable"
    summary = ", ".join(parts)
    return f"{label}: {summary}" if label else summary
