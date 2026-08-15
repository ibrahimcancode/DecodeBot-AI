"""DecodeBot AI — Entry Point (FR-001, FR-002).

Single executable entry point for the DecodeBot AI application.
Supports --gui flag for optional Tkinter GUI mode and --plain for
accessibility-friendly plain-text mode (FR-133). Top-level optional
commands (FR-259) such as ``recognize`` dispatch to their isolated engine
modules lazily, so the default chatbot REPL is unaffected (FR-249).
"""

import sys

_CLI_COMMANDS = {
    "recognize": "decodebot.recognition.app_recognition",
}


def _dispatch_command(argv):
    """Route an optional top-level command (e.g. ``recognize``) to its engine.

    Each command module is imported lazily so the base chatbot never pays the
    (optional, heavy) import cost at startup (FR-249, FR-250).
    """
    command = argv[0]
    module = _CLI_COMMANDS.get(command)
    if module is None:
        return None
    from importlib import import_module

    engine = import_module(module)
    return engine.main(argv[1:])


def main():
    args = [arg for arg in sys.argv[1:] if arg not in ("--gui", "--plain")]
    use_gui = "--gui" in sys.argv
    plain = "--plain" in sys.argv

    if args:
        result = _dispatch_command(args)
        if result is not None:
            return result

    if use_gui:
        from decodebot.gui.app_gui import run_gui

        return run_gui()
    else:
        from decodebot.core.app import run

        overrides = {"plain_mode": True} if plain else None
        return run(config_overrides=overrides)


if __name__ == "__main__":
    sys.exit(main())
