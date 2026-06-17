"""Cyan / white / purple polished-dark theme for ReaperSniff."""

BG_0 = "#0A0C12"   # app background
BG_1 = "#10131C"   # panel
BG_2 = "#161B26"   # card
BG_3 = "#1C2230"   # raised
BORDER = "#222B3A"

CYAN = "#22D3EE"
CYAN_HI = "#3DE0F2"
PURPLE = "#A855F7"
PURPLE_HI = "#C084FC"
WHITE = "#F4F7FB"
MUTED = "#8694A8"
AMBER = "#F59E0B"
GREEN = "#34D399"
RED = "#F87171"

CAT_COLORS = {
    "Torrent P2P": PURPLE,
    "Game P2P": CYAN,
    "Generic P2P": AMBER,
}


def build_stylesheet() -> str:
    return f"""
    QWidget {{
        background: {BG_0};
        color: {WHITE};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 13px;
    }}
    QMainWindow, #root {{ background: {BG_0}; }}

    #header {{ background: {BG_1}; border-bottom: 1px solid {BORDER}; }}
    #title {{ font-size: 22px; font-weight: 800; color: {WHITE}; }}
    #title #accent {{ color: {CYAN}; }}
    #subtitle {{ color: {MUTED}; font-size: 12px; }}

    QFrame#card {{
        background: {BG_2};
        border: 1px solid {BORDER};
        border-radius: 14px;
    }}
    #cardTitle {{
        color: {MUTED}; font-size: 11px; font-weight: 700;
        letter-spacing: 1px;
    }}
    #cardValue {{
        font-size: 24px; font-weight: 800;
        font-family: 'Consolas', 'JetBrains Mono', monospace;
    }}
    #cardSub {{ color: {MUTED}; font-size: 11px; }}
    #sectionTitle {{ font-size: 14px; font-weight: 800; color: {WHITE}; }}
    #hint {{ color: {MUTED}; font-size: 11px; }}

    QTabWidget::pane {{
        border: 1px solid {BORDER}; border-radius: 12px;
        background: {BG_1}; top: -1px;
    }}
    QTabBar::tab {{
        background: transparent; color: {MUTED};
        padding: 9px 20px; margin-right: 4px;
        border: 1px solid transparent; border-radius: 9px; font-weight: 700;
    }}
    QTabBar::tab:selected {{ color: {CYAN}; background: {BG_2}; border: 1px solid {BORDER}; }}
    QTabBar::tab:hover {{ color: {WHITE}; }}

    QPushButton {{
        background: {CYAN}; color: #06121A; border: none;
        border-radius: 9px; padding: 9px 18px; font-weight: 700;
    }}
    QPushButton:hover {{ background: {CYAN_HI}; }}
    QPushButton#ghost {{ background: transparent; color: {CYAN}; border: 1px solid {CYAN}; }}
    QPushButton#ghost:hover {{ background: rgba(34,211,238,0.12); }}
    QPushButton#danger {{ background: {RED}; color: #1A0606; }}
    QPushButton#danger:hover {{ background: #FF9090; }}

    QLineEdit {{
        background: {BG_0}; border: 1px solid {BORDER};
        border-radius: 8px; padding: 7px 10px; color: {WHITE};
    }}
    QLineEdit:focus {{ border: 1px solid {CYAN}; }}
    QCheckBox {{ color: {MUTED}; spacing: 6px; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px;
        border: 1px solid {BORDER}; background: {BG_0}; }}
    QCheckBox::indicator:checked {{ background: {CYAN}; border: 1px solid {CYAN}; }}

    QTableWidget {{ background: {BG_1}; border: none; gridline-color: {BG_2};
        selection-background-color: {BG_3}; selection-color: {WHITE}; }}
    QHeaderView::section {{
        background: {BG_2}; color: {MUTED}; border: none;
        border-bottom: 1px solid {BORDER}; padding: 8px; font-weight: 700;
    }}
    QTableWidget::item {{ padding: 6px; border-bottom: 1px solid {BG_2}; }}

    QListWidget {{ background: {BG_1}; border: 1px solid {BORDER}; border-radius: 10px; padding: 4px; }}
    QListWidget::item {{ padding: 6px 8px; border-radius: 6px; }}

    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {CYAN}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QScrollBar:horizontal {{ height: 0; }}

    #badge {{ border-radius: 10px; padding: 4px 12px; font-weight: 800; font-size: 11px; }}

    QProgressBar {{ background: {BG_0}; border: none; border-radius: 5px;
        height: 8px; text-align: center; color: transparent; }}
    QProgressBar::chunk {{ border-radius: 5px; background: {CYAN}; }}
    """
