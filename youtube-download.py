import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp
import threading
import os

# ─── Dossiers de sortie (défauts) ────────────────────────────────────────────
DEFAULT_DIRS = {
    "mp4": os.path.join(os.path.expanduser("~"), "Downloads", "mp4"),
    "mp3": os.path.join(os.path.expanduser("~"), "Downloads", "mp3"),
}
for d in DEFAULT_DIRS.values():
    os.makedirs(d, exist_ok=True)

# ─── Palette de couleurs ──────────────────────────────────────────────────────
BG        = "#0f0f13"
SURFACE   = "#1a1a24"
CARD      = "#22222f"
ACCENT    = "#ff3b5c"
ACCENT2   = "#ff7a00"
TEXT      = "#f0f0f8"
SUBTEXT   = "#8888aa"
SUCCESS   = "#00e096"
ERROR     = "#ff4466"
BORDER    = "#2e2e42"

# ─── Options de qualité ───────────────────────────────────────────────────────
QUALITY_OPTIONS = {
    "MP4": {
        "🏆 Meilleure qualité"  : "bestvideo+bestaudio/best",
        "🎬 1080p (Full HD)"    : "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "📺 720p (HD)"          : "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "📱 480p"               : "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "🔋 360p (léger)"       : "bestvideo[height<=360]+bestaudio/best[height<=360]",
    },
    "MP3": {
        "🏆 320 kbps (max)"     : "320",
        "🎵 256 kbps"           : "256",
        "🎶 192 kbps"           : "192",
        "📻 128 kbps"           : "128",
        "🔋 96 kbps (léger)"    : "96",
    },
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YT Downloader")
        self.geometry("520x580")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.format_var  = tk.StringVar(value="MP4")
        self.quality_var = tk.StringVar()
        # Dossiers personnalisés (None = utiliser le défaut)
        self.custom_dirs = {"mp4": None, "mp3": None}

        self._build_ui()
        self._update_quality_options()

    # ── Construction de l'interface ───────────────────────────────────────────
    def _build_ui(self):
        # Header gradient bar
        header = tk.Frame(self, bg=ACCENT, height=4)
        header.pack(fill="x")

        # Logo / Titre
        title_frame = tk.Frame(self, bg=BG, pady=24)
        title_frame.pack(fill="x", padx=30)

        tk.Label(
            title_frame, text="▶  YT Downloader",
            font=("Georgia", 20, "bold"),
            fg=TEXT, bg=BG
        ).pack(side="left")

        tk.Label(
            title_frame, text="by yt-dlp",
            font=("Courier", 10),
            fg=SUBTEXT, bg=BG
        ).pack(side="left", padx=10, pady=6)

        # ── Card principale ───────────────────────────────────────────────────
        card = tk.Frame(self, bg=CARD, bd=0, padx=24, pady=24)
        card.pack(fill="both", padx=24, pady=4)

        # URL
        tk.Label(card, text="URL YouTube", font=("Courier", 9, "bold"),
                 fg=SUBTEXT, bg=CARD).pack(anchor="w")

        url_frame = tk.Frame(card, bg=BORDER, pady=1, padx=1)
        url_frame.pack(fill="x", pady=(4, 16))

        self.entry_url = tk.Entry(
            url_frame, font=("Courier", 11),
            bg=SURFACE, fg=TEXT, insertbackground=ACCENT,
            relief="flat", bd=8
        )
        self.entry_url.pack(fill="x")
        self.entry_url.insert(0, "https://www.youtube.com/watch?v=...")
        self.entry_url.bind("<FocusIn>",  self._clear_placeholder)
        self.entry_url.bind("<FocusOut>", self._restore_placeholder)

        # ── Format + Qualité côte à côte ──────────────────────────────────────
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(0, 16))

        # Format
        fmt_frame = tk.Frame(row, bg=CARD)
        fmt_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Label(fmt_frame, text="Format", font=("Courier", 9, "bold"),
                 fg=SUBTEXT, bg=CARD).pack(anchor="w")

        btn_row = tk.Frame(fmt_frame, bg=CARD)
        btn_row.pack(anchor="w", pady=(4, 0))

        self.btn_mp4 = self._format_btn(btn_row, "MP4", "left")
        self.btn_mp3 = self._format_btn(btn_row, "MP3", "left")
        self._highlight_format()

        # Qualité
        qual_frame = tk.Frame(row, bg=CARD)
        qual_frame.pack(side="left", fill="x", expand=True)

        tk.Label(qual_frame, text="Qualité", font=("Courier", 9, "bold"),
                 fg=SUBTEXT, bg=CARD).pack(anchor="w")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
            fieldbackground=SURFACE, background=SURFACE,
            foreground=TEXT, selectbackground=SURFACE,
            selectforeground=TEXT, arrowcolor=ACCENT,
            bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
        )
        style.map("Dark.TCombobox",
            fieldbackground=[("readonly", SURFACE)],
            selectbackground=[("readonly", SURFACE)],
        )

        self.combo_quality = ttk.Combobox(
            qual_frame, textvariable=self.quality_var,
            state="readonly", style="Dark.TCombobox",
            font=("Courier", 10)
        )
        self.combo_quality.pack(fill="x", pady=(4, 0))

        # ── Dossier de destination ────────────────────────────────────────────
        tk.Label(card, text="Dossier de destination", font=("Courier", 9, "bold"),
                 fg=SUBTEXT, bg=CARD).pack(anchor="w")

        dest_row = tk.Frame(card, bg=CARD)
        dest_row.pack(fill="x", pady=(4, 16))

        # Champ affichant le chemin (cliquable aussi)
        dest_inner = tk.Frame(dest_row, bg=BORDER, pady=1, padx=1)
        dest_inner.pack(side="left", fill="x", expand=True)

        self.dest_label = tk.Label(
            dest_inner, text="", font=("Courier", 9),
            fg=ACCENT2, bg=SURFACE, anchor="w",
            padx=8, pady=6
        )
        self.dest_label.pack(fill="x")

        # Bouton "Changer"
        self.btn_browse = tk.Button(
            dest_row, text="📂  Changer",
            font=("Courier", 9, "bold"),
            bg=SURFACE, fg=TEXT,
            activebackground=ACCENT2, activeforeground=TEXT,
            relief="flat", cursor="hand2", padx=10,
            command=self._browse_folder
        )
        self.btn_browse.pack(side="left", padx=(6, 0))

        # Bouton reset
        self.btn_reset = tk.Button(
            dest_row, text="↺",
            font=("Courier", 11, "bold"),
            bg=SURFACE, fg=SUBTEXT,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", cursor="hand2", padx=8,
            command=self._reset_folder
        )
        self.btn_reset.pack(side="left", padx=(4, 0))

        self._update_dest_label()

        # ── Bouton Télécharger ────────────────────────────────────────────────
        self.btn_dl = tk.Button(
            card, text="⬇  TÉLÉCHARGER",
            font=("Georgia", 13, "bold"),
            bg=ACCENT, fg=TEXT, activebackground=ACCENT2,
            activeforeground=TEXT, relief="flat", cursor="hand2",
            pady=12, command=self.telecharger
        )
        self.btn_dl.pack(fill="x", pady=(0, 4))

        # ── Barre de progression ──────────────────────────────────────────────
        style.configure("Accent.Horizontal.TProgressbar",
            troughcolor=SURFACE, background=ACCENT,
            bordercolor=SURFACE, lightcolor=ACCENT, darkcolor=ACCENT,
        )

        prog_header = tk.Frame(card, bg=CARD)
        prog_header.pack(fill="x", pady=(12, 2))

        tk.Label(prog_header, text="Progression", font=("Courier", 9, "bold"),
                 fg=SUBTEXT, bg=CARD).pack(side="left")

        self.pct_label = tk.Label(prog_header, text="0 %",
                                  font=("Courier", 9, "bold"),
                                  fg=ACCENT, bg=CARD)
        self.pct_label.pack(side="right")

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            card, orient="horizontal", length=400,
            mode="determinate", variable=self.progress_var,
            style="Accent.Horizontal.TProgressbar"
        )
        self.progress.pack(fill="x")

        # Vitesse + ETA
        self.info_var = tk.StringVar(value="")
        tk.Label(card, textvariable=self.info_var,
                 font=("Courier", 8), fg=SUBTEXT, bg=CARD
        ).pack(anchor="e", pady=(2, 0))

        # ── Status ────────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="En attente…")
        self.status_label = tk.Label(
            self, textvariable=self.status_var,
            font=("Courier", 10), fg=SUBTEXT, bg=BG
        )
        self.status_label.pack(pady=8)

        # ── Footer ────────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=BG)
        footer.pack(side="bottom", fill="x", padx=24, pady=12)
        tk.Label(footer, text="Fichiers sauvegardés dans le dossier de destination choisi",
                 font=("Courier", 8), fg=SUBTEXT, bg=BG).pack()

    # ── Helpers UI ────────────────────────────────────────────────────────────
    def _format_btn(self, parent, fmt, side):
        btn = tk.Button(
            parent, text=fmt, width=6,
            font=("Courier", 10, "bold"),
            relief="flat", cursor="hand2",
            command=lambda f=fmt: self._select_format(f)
        )
        btn.pack(side=side, padx=(0, 6))
        return btn

    def _select_format(self, fmt):
        self.format_var.set(fmt)
        self._highlight_format()
        self._update_quality_options()
        self._update_dest_label()

    def _highlight_format(self):
        sel = self.format_var.get()
        for btn, fmt in [(self.btn_mp4, "MP4"), (self.btn_mp3, "MP3")]:
            if fmt == sel:
                btn.config(bg=ACCENT, fg=TEXT)
            else:
                btn.config(bg=SURFACE, fg=SUBTEXT)

    def _update_quality_options(self):
        fmt = self.format_var.get()
        opts = list(QUALITY_OPTIONS[fmt].keys())
        self.combo_quality["values"] = opts
        self.combo_quality.set(opts[0])

    def _update_dest_label(self):
        fmt = self.format_var.get().lower()
        path = self.custom_dirs[fmt] or DEFAULT_DIRS[fmt]
        # Tronquer si trop long
        display = path if len(path) <= 50 else "…" + path[-48:]
        self.dest_label.config(text=f"📁  {display}")
        # Indiquer visuellement si c'est un dossier custom
        is_custom = self.custom_dirs[fmt] is not None
        self.dest_label.config(fg=SUCCESS if is_custom else ACCENT2)

    def _browse_folder(self):
        fmt = self.format_var.get().lower()
        current = self.custom_dirs[fmt] or DEFAULT_DIRS[fmt]
        chosen = filedialog.askdirectory(
            title=f"Choisir le dossier pour les {fmt.upper()}",
            initialdir=current,
            mustexist=True,
        )
        if chosen:
            self.custom_dirs[fmt] = chosen
            os.makedirs(chosen, exist_ok=True)
            self._update_dest_label()

    def _reset_folder(self):
        fmt = self.format_var.get().lower()
        self.custom_dirs[fmt] = None
        self._update_dest_label()

    def _get_out_dir(self):
        fmt = self.format_var.get().lower()
        return self.custom_dirs[fmt] or DEFAULT_DIRS[fmt]

    def _clear_placeholder(self, _):
        if self.entry_url.get().startswith("https://www.youtube.com/watch?v=..."):
            self.entry_url.delete(0, "end")
            self.entry_url.config(fg=TEXT)

    def _restore_placeholder(self, _):
        if not self.entry_url.get():
            self.entry_url.insert(0, "https://www.youtube.com/watch?v=...")
            self.entry_url.config(fg=SUBTEXT)

    # ── Téléchargement ────────────────────────────────────────────────────────
    def telecharger(self):
        url = self.entry_url.get().strip()
        if not url or url.startswith("https://www.youtube.com/watch?v=..."):
            messagebox.showwarning("Attention", "Veuillez coller une URL YouTube valide.")
            return
        threading.Thread(target=self._run, args=(url,), daemon=True).start()

    def _progress_hook(self, d):
        """Appelé par yt-dlp à chaque chunk téléchargé."""
        if d["status"] == "downloading":
            total   = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            speed   = d.get("speed") or 0
            eta     = d.get("eta") or 0

            pct = (downloaded / total * 100) if total else 0

            # Formatage vitesse
            if speed >= 1_048_576:
                speed_str = f"{speed/1_048_576:.1f} MB/s"
            elif speed >= 1024:
                speed_str = f"{speed/1024:.0f} KB/s"
            else:
                speed_str = f"{speed:.0f} B/s"

            # Formatage ETA
            if eta >= 60:
                eta_str = f"{eta//60}m {eta%60:02d}s"
            else:
                eta_str = f"{eta}s"

            info = f"⚡ {speed_str}   ⏱ {eta_str} restant"

            # Mise à jour thread-safe via after()
            self.after(0, self._update_progress, pct, info)

        elif d["status"] == "finished":
            self.after(0, self._update_progress, 100, "🔄  Conversion en cours…")

    def _update_progress(self, pct, info):
        self.progress_var.set(pct)
        self.pct_label.config(text=f"{pct:.0f} %")
        self.info_var.set(info)

    def _run(self, url):
        self.btn_dl.config(state="disabled")
        self._update_progress(0, "")

        fmt      = self.format_var.get()
        quality  = self.quality_var.get()
        q_value  = QUALITY_OPTIONS[fmt][quality]
        out_dir  = self._get_out_dir()

        if fmt == "MP4":
            ydl_opts = {
                "format"              : q_value,
                "outtmpl"             : os.path.join(out_dir, "%(title)s.%(ext)s"),
                "merge_output_format" : "mp4",
                "progress_hooks"      : [self._progress_hook],
            }
        else:  # MP3
            ydl_opts = {
                "format"          : "bestaudio/best",
                "outtmpl"         : os.path.join(out_dir, "%(title)s.%(ext)s"),
                "progress_hooks"  : [self._progress_hook],
                "postprocessors"  : [{
                    "key"             : "FFmpegExtractAudio",
                    "preferredcodec"  : "mp3",
                    "preferredquality": q_value,
                }],
            }

        self._set_status("⏳  Téléchargement en cours…", SUBTEXT)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, self._update_progress, 100, "✅  Terminé !")
            self._set_status(f"✅  Fichier {fmt} enregistré dans {out_dir}", SUCCESS)
            messagebox.showinfo("Terminé !", f"Téléchargement {fmt} terminé !\n\n📁 {out_dir}")
        except Exception as e:
            self._set_status(f"❌  Erreur : {e}", ERROR)
            messagebox.showerror("Erreur", str(e))
        finally:
            self.btn_dl.config(state="normal")
            self.entry_url.delete(0, "end")
            self._restore_placeholder(None)

    def _set_status(self, msg, color=SUBTEXT):
        self.status_var.set(msg)
        self.status_label.config(fg=color)

if __name__ == "__main__":
    app = App()
    app.mainloop()