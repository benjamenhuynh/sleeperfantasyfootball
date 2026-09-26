import streamlit as st

from league import GetCurrentLeagueData
from players import Players
from rosters import Rosters


# ============================================================
# Function Name: LoadLeagueData
#
# Parameters:
#   None.
#
# Return:
#   Cached current league data for the Streamlit interface.
# ============================================================
@st.cache_data(ttl=900)
def LoadLeagueData():
    return GetCurrentLeagueData()


st.set_page_config(page_title="Fantasy Football", layout="wide")
st.title("Fantasy Football")

with st.spinner("Loading league data..."):
    league_data = LoadLeagueData()

players = Players(league_data["players"])
roster_view = Rosters(
    players,
    league_data["users"],
    league_data["player_stats"],
    league_data["player_projections"],
)

st.caption(
    f"NFL {league_data['season']} {league_data['season_type']} season, "
    f"week {league_data['week']}"
)

roster_index = st.selectbox(
    "Team",
    range(len(league_data["rosters"])),
    format_func=lambda index: roster_view.GetTeamName(
        league_data["rosters"][index]["owner_id"]
    ),
)
selected_roster = league_data["rosters"][roster_index]

starters_column, bench_column = st.columns(2)
with starters_column:
    st.subheader("Starters")
st.table(
        {
            "Player": [
                roster_view.FormatPlayerLine(player_id)
                for player_id in roster_view.GetStarters(selected_roster)
            ]
        }
    )

with bench_column:
    st.subheader("Bench")
    st.table(
        {
            "Player": [
                roster_view.FormatPlayerLine(player_id)
                for player_id in roster_view.GetBench(selected_roster)
            ]
        }
    )
