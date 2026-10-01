from pathlib import Path
from src.ui.pages import render_category
ROOT=Path(__file__).resolve().parents[1]
render_category(str(ROOT),"coincident")
