"""Machine Learning tab for the Tkinter GUI (FR-224, FR-225).

The tab runs the *identical* ML command functions as the CLI (FR-224) via a
``handlers`` mapping injected by ``app_gui``. The predict form collects four
feature values and forwards them as a float list — the same validation and
classification path a ``predict`` CLI command uses (FR-225).

This module imports only stdlib ``tkinter``; no ML library is imported here
(FR-229, NFR-072) — the handlers it calls live behind the lazy bridge in
``decodebot/ml/app_ml.py``.
"""

import tkinter as tk
from tkinter import font as tkfont

BTN_STYLE = {"relief": tk.FLAT, "padx": 10, "pady": 3}


class MLPanel(tk.Frame):
    """A ``Frame`` with buttons and a predict form bound to ML handlers."""

    def __init__(self, master, handlers: dict, bot_name: str = "DecodeBot"):
        super().__init__(master, bg="#f0f0f0")
        self.handlers = handlers
        self.bot_name = bot_name
        self._build()

    def _build(self) -> None:
        self.font = tkfont.Font(family="Consolas", size=10)

        header = tk.Label(
            self,
            text=f"{self.bot_name} Machine Learning Engine",
            font=tkfont.Font(family="Consolas", size=11, weight="bold"),
            bg="#f0f0f0",
            fg="#333333",
        )
        header.pack(anchor="w", pady=(0, 6))

        buttons = tk.Frame(self, bg="#f0f0f0")
        buttons.pack(fill=tk.X, pady=(0, 8))

        action_specs = (
            ("Train", "train"),
            ("Evaluate", "evaluate"),
            ("Compare", "compare"),
            ("Tune-K", "tune_k"),
            ("Explore", "explore"),
            ("List Models", "models"),
        )
        for label, key in action_specs:
            btn = tk.Button(
                buttons,
                text=label,
                command=lambda k=key: self._run(k),
                bg="#1a73e8",
                fg="#ffffff",
                **BTN_STYLE,
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))

        predict_frame = tk.Frame(self, bg="#f0f0f0")
        predict_frame.pack(fill=tk.X, pady=(0, 8))

        label = tk.Label(predict_frame, text="Feature values:", bg="#f0f0f0")
        label.pack(side=tk.LEFT)

        self.entries = []
        for _ in range(4):
            entry = tk.Entry(predict_frame, font=self.font, relief=tk.SUNKEN, bd=2, width=8)
            entry.pack(side=tk.LEFT, padx=(4, 0))
            self.entries.append(entry)

        classify = tk.Button(
            predict_frame,
            text="Classify",
            command=self._classify,
            bg="#1a73e8",
            fg="#ffffff",
            **BTN_STYLE,
        )
        classify.pack(side=tk.LEFT, padx=(8, 0))

        output_frame = tk.Frame(self, bg="#f0f0f0")
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.output = tk.Text(
            output_frame,
            font=self.font,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#ffffff",
            fg="#000000",
            relief=tk.FLAT,
            padx=8,
            pady=8,
        )
        scrollbar = tk.Scrollbar(output_frame, command=self.output.yview)
        self.output.configure(yscrollcommand=scrollbar.set)
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._append("Ready. Train a model, then classify 4 feature values.")

    def _run(self, key: str) -> None:
        handler = self.handlers.get(key)
        if handler is None:
            self._append(f"[{key}] no handler wired.")
            return
        self._append(f">>> {key.upper()}")
        self._append(handler())

    def _classify(self) -> None:
        try:
            values = [float(entry.get().strip()) for entry in self.entries]
        except ValueError:
            self._append("Please enter numeric values in all 4 feature fields.")
            return
        handler = self.handlers.get("predict")
        if handler is None:
            self._append("[predict] no handler wired.")
            return
        self._append(f">>> predict {', '.join(str(v) for v in values)}")
        self._append(handler(values))

    def _append(self, text: str) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)
