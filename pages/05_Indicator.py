from pathlib import Path
from src.ui.pages import render_indicator
ROOT=Path(__file__).resolve().parents[1]
render_indicator(str(ROOT))
