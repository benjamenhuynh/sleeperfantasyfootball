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
        return {
            str(item["player_id"]): item.get("stats", item)
            for item in projections
            if item.get("player_id") is not None
        }
    return projections
