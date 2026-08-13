import time
import logging

import tkinter as tk

from decodebot.core.config import load_config
from decodebot.core.logger import setup_logging
from decodebot.core.dispatcher import dispatch
from decodebot.core.rule_engine import classify_intent
from decodebot.core.session import SessionState
from decodebot.core.intents import Intent
from decodebot.core.io_handler import print_response

logger = logging.getLogger(__name__)


def _has_display() -> bool:
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        return False


def run_gui() -> int:
    config = load_config()
    setup_logging(config)
    logger.info("GUI adapter started")
    if not _has_display():
        logger.warning("No display available, falling back to CLI")
        print_response("No display available for GUI — run without --gui for CLI mode.")
        from decodebot.core.loop import run_session

        return run_session()

    try:
        _tkinter_gui(config)
        return 0
    except Exception:
        logger.exception("Fatal GUI error")
        return 1


def _tkinter_gui(config: dict) -> None:
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import font as tkfont

    from decodebot import __version__

    session = SessionState()
    session.start_time = time.monotonic()
    session.config = config
    bot_name = config.get("bot_name", "DecodeBot")

    root = tk.Tk()
    root.title(f"{bot_name} AI")
    root.minsize(500, 400)
    root.geometry("650x500")

    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    chat_tab = tk.Frame(notebook, bg="#f0f0f0")
    ml_tab = tk.Frame(notebook, bg="#f0f0f0")
    rec_tab = tk.Frame(notebook, bg="#f0f0f0")
    notebook.add(chat_tab, text="Chat")
    notebook.add(ml_tab, text="Machine Learning")
    notebook.add(rec_tab, text="Career Recommender")

    chat_frame = tk.Frame(chat_tab, bg="#f0f0f0")
    chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    text_font = tkfont.Font(family="Consolas", size=10)

    chat_display = tk.Text(
        chat_frame,
        font=text_font,
        wrap=tk.WORD,
        state=tk.DISABLED,
        bg="#ffffff",
        fg="#000000",
        relief=tk.FLAT,
        padx=10,
        pady=10,
        spacing1=2,
        spacing3=2,
    )
    chat_display.tag_configure("user", justify=tk.RIGHT, foreground="#1a73e8")
    chat_display.tag_configure("bot", justify=tk.LEFT, foreground="#000000")
    chat_display.tag_configure("system", justify=tk.CENTER, foreground="#666666")
    chat_display.tag_configure(
        "title",
        justify=tk.CENTER,
        foreground="#333333",
        font=tkfont.Font(family="Consolas", size=11, weight="bold"),
    )

    scrollbar = tk.Scrollbar(chat_frame, command=chat_display.yview)
    chat_display.configure(yscrollcommand=scrollbar.set)

    chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    _append_text(chat_display, f" {bot_name} AI v{__version__} ", "title")
    _append_text(chat_display, "Rule-Based Conversational Agent", "title")
    _append_text(chat_display, "", "system")
    _append_text(chat_display, "Type 'help' to see what I can do.", "system")
    _append_text(chat_display, "", "system")

    input_frame = tk.Frame(chat_tab, bg="#f0f0f0")
    input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

    input_entry = tk.Entry(input_frame, font=text_font, relief=tk.SUNKEN, bd=2)
    input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

    def _send():
        raw = input_entry.get()
        input_entry.delete(0, tk.END)
        if not raw.strip():
            return
        _handle_input(root, chat_display, raw, session)

    input_entry.bind("<Return>", lambda e: _send())

    send_btn = tk.Button(
        input_frame, text="Send", command=_send, bg="#1a73e8", fg="#ffffff", relief=tk.FLAT, padx=15
    )
    send_btn.pack(side=tk.RIGHT)

    ml_panel = _build_ml_panel(ml_tab, session)
    ml_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    rec_panel = _build_recommender_panel(rec_tab, session)
    rec_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _on_close():
        summary = _build_gui_summary(session)
        if summary:
            _append_text(chat_display, summary, "bot")
        _append_text(chat_display, "Goodbye! Thanks for chatting.", "bot")
        chat_display.see(tk.END)
        root.after(1200, root.destroy)

    root.protocol("WM_DELETE_WINDOW", _on_close)
    input_entry.focus_set()
    root.mainloop()


def _append_text(widget, text, tag=None):
    widget.configure(state=tk.NORMAL)
    if tag:
        widget.insert(tk.END, text + "\n", tag)
    else:
        widget.insert(tk.END, text + "\n")
    widget.see(tk.END)
    widget.configure(state=tk.DISABLED)


def _ml_handlers(session):
    """Bind the ML tab buttons to the exact CLI ML functions (FR-224).

    The import is lazy so startup never touches the ML dependencies
    (FR-232); only the first ML action pays the import cost.
    """
    from decodebot.ml import app_ml

    return {
        "train": lambda: app_ml.handle_train(session),
        "predict": lambda features=None: app_ml.handle_predict(session, features=features),
        "evaluate": lambda: app_ml.handle_evaluate(session),
        "explore": lambda: app_ml.handle_explore(session),
        "models": lambda: app_ml.handle_models(session),
        "compare": lambda: app_ml.handle_compare(session),
        "tune_k": lambda: app_ml.handle_tune_k(session),
    }


def _build_ml_panel(parent, session):
    from decodebot.gui.ml_panel import MLPanel

    bot_name = session.config.get("bot_name", "DecodeBot")
    return MLPanel(parent, handlers=_ml_handlers(session), bot_name=bot_name)


def _recommend_handlers(session):
    """Bind the Career Recommender tab to the exact CLI function (FR-246).

    The import is lazy so GUI startup never touches the recommender engine
    (FR-233); the first Recommend click pays the import cost. The handler
    builds the same ``recommend --skills "..."`` command the CLI dispatcher
    passes, so GUI output is byte-for-byte identical to the terminal.
    """
    from decodebot.recommender import app_recommender

    def recommend(skills):
        raw = f'recommend --skills "{skills}"'
        return app_recommender.handle_recommend(session.config, raw)

    return {"recommend": recommend}


def _build_recommender_panel(parent, session):
    from decodebot.gui.recommender_panel import RecommenderPanel

    bot_name = session.config.get("bot_name", "DecodeBot")
    return RecommenderPanel(
        parent,
        recommend_handler=_recommend_handlers(session)["recommend"],
        bot_name=bot_name,
    )


def _handle_input(root, chat_display, raw, session):
    _append_text(chat_display, f"You: {raw}", "user")

    session.last_input = raw
    intent = classify_intent(raw, session)

    if intent == Intent.EXIT:
        summary = _build_gui_summary(session)
        if summary:
            _append_text(chat_display, summary, "bot")
        _append_text(chat_display, "Bot: Goodbye! Thanks for chatting.", "bot")
        root.after(1200, root.destroy)
        return

    if intent == Intent.CLEAR:
        chat_display.configure(state=tk.NORMAL)
        chat_display.delete("1.0", tk.END)
        chat_display.configure(state=tk.DISABLED)
        _append_text(chat_display, "[screen cleared]", "system")
        session.record_turn(raw, intent, "[screen cleared]")
        return

    if intent == Intent.RESET:
        session.reset()
        session.start_time = time.monotonic()
        from decodebot.rules.help_about_version import get_reset_text

        resp = get_reset_text()
        _append_text(chat_display, f"Bot: {resp}", "bot")
        session.record_turn(raw, intent, resp)
        return

    response_text = dispatch(intent, session)
    _append_text(chat_display, f"Bot: {response_text}", "bot")
    session.record_turn(raw, intent, response_text)


def _build_gui_summary(session):
    if session.message_count == 0:
        return None
    from decodebot.core.stats import get_session_duration

    dur = get_session_duration(session)
    return f"Bot: We exchanged {session.message_count} messages over {dur}. Thanks for chatting!"
