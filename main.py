"""DecodeBot AI — Entry Point (FR-001, FR-002).

Single executable entry point for the DecodeBot AI application.
Supports --gui flag for optional Tkinter GUI mode.
"""

import sys


def main():
    use_gui = "--gui" in sys.argv

    if use_gui:
        from decodebot.gui.app_gui import run_gui
        return run_gui()
    else:
        from decodebot.core.app import run
        return run()


if __name__ == "__main__":
    sys.exit(main())
