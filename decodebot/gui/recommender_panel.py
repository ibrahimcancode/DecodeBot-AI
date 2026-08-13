"""Career Recommender tab for the Tkinter GUI (FR-246).

The tab calls the *identical* engine function as the CLI (FR-246): the handler
injected by ``app_gui`` builds the same ``recommend --skills "..."`` command
line and routes it through ``decodebot/recommender/app_recommender.py`` — the
exact path the CLI dispatcher uses — so the GUI ranked list matches the
terminal output, including ``plain_mode`` rendering.

This module imports only stdlib ``tkinter`` and never imports
``decodebot.recommender`` directly (FR-233): the recommender is reached solely
through the handler callable injected by the wiring file ``app_gui.py``,
enforced by ``tests/test_wave3_isolation.py``.
"""

import tkinter as tk
from tkinter import font as tkfont

BTN_STYLE = {"relief": tk.FLAT, "padx": 10, "pady": 3}

EMPTY_SKILLS_MESSAGE = 'Please enter some skills, e.g. "Python, SQL, Machine Learning".'
"""Inline validation message for an empty skills field (FR-246)."""


def validate_skills(skills: str) -> str | None:
    """Return a friendly validation message for an empty entry (FR-246).

    Args:
        skills: The raw skills text from the input field.

    Returns:
        :data:`EMPTY_SKILLS_MESSAGE` when the entry is blank/whitespace-only,
        otherwise ``None`` so the recommendation proceeds.

    Reference: SPEC.md Part III — FR-246 (empty entry → inline validation).
    """
    if not skills or not skills.strip():
        return EMPTY_SKILLS_MESSAGE
    return None


class RecommenderPanel(tk.Frame):
    """A ``Frame`` with a skills entry bound to the CLI recommend function."""

    def __init__(
        self,
        master,
        recommend_handler,
        bot_name: str = "DecodeBot",
    ):
        super().__init__(master, bg="#f0f0f0")
        self.recommend_handler = recommend_handler
        self.bot_name = bot_name
        self._build()

    def _build(self) -> None:
        self.font = tkfont.Font(family="Consolas", size=10)

        header = tk.Label(
            self,
            text=f"{self.bot_name} Career Recommender",
            font=tkfont.Font(family="Consolas", size=11, weight="bold"),
            bg="#f0f0f0",
            fg="#333333",
        )
        header.pack(anchor="w", pady=(0, 6))

        entry_frame = tk.Frame(self, bg="#f0f0f0")
        entry_frame.pack(fill=tk.X, pady=(0, 8))

        label = tk.Label(entry_frame, text="Skills:", bg="#f0f0f0")
        label.pack(side=tk.LEFT)

        self.skills_entry = tk.Entry(entry_frame, font=self.font, relief=tk.SUNKEN, bd=2)
        self.skills_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        self.skills_entry.bind("<Return>", lambda _event: self._recommend())

        recommend = tk.Button(
            entry_frame,
            text="Recommend",
            command=self._recommend,
            bg="#1a73e8",
            fg="#ffffff",
            **BTN_STYLE,
        )
        recommend.pack(side=tk.LEFT, padx=(8, 0))

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

        self._append("Enter your skills (comma-separated) to get career recommendations.")

    def _recommend(self) -> None:
        skills = self.skills_entry.get()
        message = validate_skills(skills)
        if message:
            self._append(message)
            return
        skills = skills.strip()
        self._append(f'>>> recommend --skills "{skills}"')
        try:
            result = self.recommend_handler(skills)
        except Exception as exc:  # GUI stays responsive on any failure (FR-247)
            result = f"Recommendation error: {exc}"
        self._append(result)

    def _append(self, text: str) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)
