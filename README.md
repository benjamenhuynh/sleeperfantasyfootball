# Sleeper Fantasy Football

Python project using the Sleeper API to retrieve and analyze fantasy football league data.

## Project Structure

- `main.py` coordinates data retrieval and roster output.
- `api/sleeper_api.py` contains all HTTP requests to Sleeper.
- `config/config.py` stores league and API configuration.
- `players/players.py` provides player ID, name, and position lookups.
- `rosters/rosters.py` separates, sorts, and prints starters and bench players.
- `stats/stats.py` formats player statistics.
- `projections/projections.py` normalizes Sleeper projection responses.
- `analysis/analysis.py` is reserved for higher-level fantasy analysis.
- `data/players.json` stores the downloaded NFL player database.
- `config.env.example` shows the local configuration format; `config.env` stays local.

## Current Features

- Retrieve league rosters
- Retrieve NFL player information
- Convert Sleeper player IDs to player names
- Determine player positions
- Retrieve fantasy team names
- Separate starters and bench players
- Display weekly player stats for the current NFL week
- Fall back to weekly Sleeper projections when a player's stats are missing

Stats are displayed when available; otherwise, the app displays that player's
weekly projection. API requests are centralized in `api/sleeper_api.py`.

## Setup

Create a virtual environment:

python3 -m venv .venv

Activate it:

source .venv/bin/activate

Install the dependencies:

pip install -r requirements.txt

Create a local `config.env` file from the example:

cp config.env.example config.env

Edit `config.env` and replace the placeholder with your Sleeper league ID:

SLEEPER_LEAGUE_ID=your-sleeper-league-id

Run:

python main.py
