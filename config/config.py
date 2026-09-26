import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
DATA_DIRECTORY = PROJECT_DIRECTORY / "data"
load_dotenv(PROJECT_DIRECTORY / "config.env")

LEAGUE_ID = os.environ.get("SLEEPER_LEAGUE_ID")
if not LEAGUE_ID:
    raise ValueError(
        "SLEEPER_LEAGUE_ID is not set. Set it to your Sleeper league ID "
        "before running the app."
    )
SLEEPER_API_BASE_URL = "https://api.sleeper.app/v1"
SLEEPER_PROJECTIONS_BASE_URL = "https://api.sleeper.com"
REQUEST_TIMEOUT = 30
