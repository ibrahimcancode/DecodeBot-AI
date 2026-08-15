"""Recognition tab for the Tkinter GUI (FR-260).

The tab calls the *identical* engine entry as the CLI (FR-260): the
``recognize_handler`` injected by ``app_gui`` routes through
``decodebot.recognition.app_recognition`` — the exact path the CLI dispatcher
uses — so the GUI status and text match the terminal output.

This module imports only stdlib ``tkinter`` and never imports
``cv2``/``numpy``/``pytesseract``/``decodebot.recognition`` directly (FR-229,
NFR-091 for GUI): the OCR engine is reached solely through the injected
handler callable, enforced by ``tests/test_gui_recognition.py``. When OCR
dependencies are missing the handler returns a friendly message (FR-255); the
tab stays responsive because the handler is run off the Tk event loop thread.
"""

import tkinter as tk
from tkinter import font as tkfont

BTN_STYLE = {"relief": tk.FLAT, "padx": 10, "pady": 3}

MISSING_IMAGE_MESSAGE = "Please choose an image file first."
"""Inline validation message for a missing image (FR-260 edge case)."""

SUPPORTED_FILTER = "Image files (*.png, *.jpg, *.jpeg)\nAll files (*)"


class RecognitionPanel(tk.Frame):
    """A ``Frame`` with an image path field bound to the CLI recognize function."""

    def __init__(
        self,
        master,
        recognize_handler,
        browse_handler,
        bot_name: str = "DecodeBot",
    ):
        super().__init__(master, bg="#f0f0f0")
        self.recognize_handler = recognize_handler
        self.browse_handler = browse_handler
        self.bot_name = bot_name
        self._build()

    def _build(self) -> None:
        self.font = tkfont.Font(family="Consolas", size=10)

        header = tk.Label(
            self,
            text=f"{self.bot_name} OCR Recognition",
            font=tkfont.Font(family="Consolas", size=11, weight="bold"),
            bg="#f0f0f0",
            fg="#333333",
        )
        header.pack(anchor="w", pady=(0, 6))

        entry_frame = tk.Frame(self, bg="#f0f0f0")
        entry_frame.pack(fill=tk.X, pady=(0, 8))

        label = tk.Label(entry_frame, text="Image:", bg="#f0f0f0")
        label.pack(side=tk.LEFT)

        self.image_entry = tk.Entry(entry_frame, font=self.font, relief=tk.SUNKEN, bd=2)
        self.image_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        self.image_entry.bind("<Return>", lambda _event: self._recognize())

        self.browse_btn = tk.Button(
            entry_frame,
            text="Browse",
            command=self._browse,
            bg="#1a73e8",
            fg="#ffffff",
            **BTN_STYLE,
        )
        self.browse_btn.pack(side=tk.LEFT, padx=(8, 0))

        psm_frame = tk.Frame(self, bg="#f0f0f0")
        psm_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(psm_frame, text="PSM:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.psm_var = tk.StringVar(value="6")
        self.psm_entry = tk.OptionMenu(psm_frame, self.psm_var, "6", "3", "7", "11")
        self.psm_entry.pack(side=tk.LEFT, padx=(6, 0))

        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=(0, 8))
        self.recognize_btn = tk.Button(
            button_frame,
            text="Recognize",
            command=self._recognize,
            bg="#1a73e8",
            fg="#ffffff",
            **BTN_STYLE,
        )
        self.recognize_btn.pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            button_frame,
            text="Save output",
            command=self._recognize_and_save,
            bg="#34a853",
            fg="#ffffff",
            **BTN_STYLE,
        ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(
            self,
            textvariable=self.status_var,
            bg="#f0f0f0",
            fg="#333333",
            font=tkfont.Font(family="Consolas", size=10, weight="bold"),
        )
        status_label.pack(anchor="w", pady=(0, 6))

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

    def _browse(self) -> None:
        path = self.browse_handler()
        if path:
            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, path)

    def _recognize(self, save: bool = False) -> None:
        image_path = self.image_entry.get().strip()
        if not image_path:
            self._append(MISSING_IMAGE_MESSAGE)
            return
        psm = self._parse_psm()
        self.status_var.set("Recognizing…")
        self.recognize_btn.config(state=tk.DISABLED)

        def _run():
            try:
                result = self.recognize_handler(image_path, psm=psm, save=save)
            except Exception as exc:  # GUI stays responsive on any failure (FR-260)
                result = f"Recognition error: {exc}"
            self._display(image_path, result)
            self.recognize_btn.config(state=tk.NORMAL)
            self.status_var.set("Ready")

        self.after(10, _run)

    def _recognize_and_save(self) -> None:
        self._recognize(save=True)

    def _parse_psm(self):
        value = self.psm_var.get()
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _display(self, image_path: str, result: str) -> None:
        # The handler returns the status prominently via the first line.
        self._append(f">>> recognize --image {image_path}")
        self._append(result)

    def _append(self, text: str) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)
