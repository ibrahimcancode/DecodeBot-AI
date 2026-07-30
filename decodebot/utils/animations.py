import sys
import time
import threading
import os

THINKING_FRAMES = ["|", "/", "-", "\\"]

REDUCED_MOTION_FRAMES = ["..."]


def _is_tty() -> bool:
    try:
        return os.isatty(sys.stdout.fileno())
    except Exception:
        return False


def animated_print(
    text: str,
    enabled: bool = True,
    speed: float = 0.015,
    end: str = "\n",
    flush: bool = True,
) -> None:
    if enabled and _is_tty() and speed > 0:
        for char in text:
            print(char, end="", flush=True)
            time.sleep(speed)
        print(end=end, flush=flush)
    else:
        print(text, end=end, flush=flush)


def show_thinking(
    enabled: bool = True,
    reduced: bool = False,
    interval: float = 0.15,
) -> threading.Event:
    done = threading.Event()

    if not enabled or not _is_tty():
        return done

    frames = REDUCED_MOTION_FRAMES if reduced else THINKING_FRAMES

    def _spin():
        idx = 0
        while not done.is_set():
            frame = frames[idx % len(frames)]
            sys.stdout.write(f"\r{frame} ")
            sys.stdout.flush()
            if done.wait(interval):
                break
            idx += 1
        sys.stdout.write("\r   \r")
        sys.stdout.flush()

    t = threading.Thread(target=_spin, daemon=True)
    t.start()
    return done
