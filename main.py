"""DecodeBot AI — Entry Point (FR-001, FR-002).

Single executable entry point for the DecodeBot AI application.
Supports --gui flag for optional Tkinter GUI mode and --plain for
accessibility-friendly plain-text mode (FR-133).
"""

import sys


def main():
    args = sys.argv
    use_gui = "--gui" in args
    plain = "--plain" in args

    if use_gui:
        from decodebot.gui.app_gui import run_gui

        return run_gui()
    else:
        from decodebot.core.app import run

        overrides = {"plain_mode": True} if plain else None
        return run(config_overrides=overrides)


if __name__ == "__main__":
    sys.exit(main())
