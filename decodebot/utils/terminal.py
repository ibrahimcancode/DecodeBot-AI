import os
import shutil


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def get_terminal_width() -> int:
    try:
        width = shutil.get_terminal_size().columns
        return min(width, 80)
    except Exception:
        return 80


def supports_color() -> bool:
    if not os.isatty(1):
        return False
    if os.name == "nt":
        return True
    return "TERM" in os.environ and os.environ["TERM"] != "dumb"
