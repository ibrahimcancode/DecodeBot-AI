import os
import shutil


def get_terminal_width() -> int:
    try:
        return min(shutil.get_terminal_size().columns, 80)
    except Exception:
        return 80


def box_text(lines: list[str], title: str = "") -> str:
    width = get_terminal_width()
    inner_width = width - 4
    if inner_width < 20:
        inner_width = 20
    top = "\u250c" + "\u2500" * (inner_width) + "\u2510"
    bottom = "\u2514" + "\u2500" * (inner_width) + "\u2518"
    result = [top]
    if title:
        title_line = "\u2502 " + title.ljust(inner_width - 1) + "\u2502"
        result.append(title_line)
        result.append("\u2502 " + "\u2500" * (inner_width - 1) + "\u2502")
    for line in lines:
        padded = line.ljust(inner_width - 1)
        result.append("\u2502 " + padded + "\u2502")
    result.append(bottom)
    return "\n".join(result)
