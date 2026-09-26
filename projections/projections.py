# ============================================================
# Function Name: NormalizeProjections
#
# Parameters:
#   projections: Sleeper weekly projection response.
#
# Return:
#   Projections keyed by Sleeper player ID.
# ============================================================
def NormalizeProjections(projections):
    if isinstance(projections, list):
        normalized = {}
        for item in projections:
            player_id = item.get("player_id")
            if player_id is None:
                continue
            player_stats = dict(item.get("stats", item))
            if item.get("opponent"):
                player_stats["opponent"] = item["opponent"]
            normalized[str(player_id)] = player_stats
        return normalized
    return projections
