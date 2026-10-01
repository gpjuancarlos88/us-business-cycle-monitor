from pathlib import Path
from src.ui.pages import render_overview
ROOT=Path(__file__).resolve().parents[1]
render_overview(str(ROOT))
