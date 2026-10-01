from pathlib import Path
from src.ui.pages import render_data_health
ROOT=Path(__file__).resolve().parents[1]
render_data_health(str(ROOT))
