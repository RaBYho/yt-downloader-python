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

# ─── Palette ──────────────────────────────────────────────────────────────────
BG      = "#0f0f13"
SURFACE = "#1a1a24"
CARD    = "#22222f"
ACCENT  = "#ff3b5c"
ACCENT2 = "#ff7a00"
TEXT    = "#f0f0f8"
SUBTEXT = "#8888aa"
SUCCESS = "#00e096"
ERROR   = "#ff4466"
BORDER  = "#2e2e42"

# ─── Options de qualité ───────────────────────────────────────────────────────
QUALITY_OPTIONS = {
    "MP4": {
        "🏆 Meilleure qualité" : "bestvideo+bestaudio/best",
        "🎬 1080p (Full HD)"   : "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "📺 720p (HD)"         : "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "📱 480p"              : "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "🔋 360p (léger)"      : "bestvideo[height<=360]+bestaudio/best[height<=360]",
    },
    "MP3": {
        "🏆 320 kbps (max)"    : "320",
        "🎵 256 kbps"          : "256",
        "🎶 192 kbps"          : "192",
        "📻 128 kbps"          : "128",
        "🔋 96 kbps (léger)"   : "96",
    },
}

PLACEHOLDER = "URL vidéo ou playlist YouTube…"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YT Downloader")
        self.geometry("540x700")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.format_var   = tk.StringVar(value="MP4")
        self.quality_var  = tk.StringVar()
        self.playlist_var = tk.BooleanVar(value=False)
        self.custom_dirs  = {"mp4": None, "mp3": None}

        self._pl_total = 0
        self._pl_done  = 0

        self._build_ui()
        self._update_quality_options()

    # =========================================================================
    # CONSTRUCTION UI
    # =========================================================================
    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        self._configure_styles(style)

        tk.Frame(self, bg=ACCENT, height=4).pack(fill="x")

        title_f = tk.Frame(self, bg=BG, pady=18)
        title_f.pack(fill="x", padx=30)
        tk.Label(title_f, text="▶  YT Downloader",
                 font=("Georgia", 20, "bold"), fg=TEXT, bg=BG).pack(side="left")
        tk.Label(title_f, text="by yt-dlp",
                 font=("Courier", 10), fg=SUBTEXT, bg=BG).pack(side="left", padx=10)

        card = tk.Frame(self, bg=CARD, padx=24, pady=20)
        card.pack(fill="both", padx=24, pady=4)

        # ── URL ───────────────────────────────────────────────────────────────
        tk.Label(card, text="URL YouTube / Playlist",
                 font=("Courier", 9, "bold"), fg=SUBTEXT, bg=CARD).pack(anchor="w")
        url_wrap = tk.Frame(card, bg=BORDER, pady=1, padx=1)
        url_wrap.pack(fill="x", pady=(4, 12))
        self.entry_url = tk.Entry(url_wrap, font=("Courier", 11),
                                  bg=SURFACE, fg=SUBTEXT,
                                  insertbackground=ACCENT, relief="flat", bd=8)
        self.entry_url.pack(fill="x")
        self.entry_url.insert(0, PLACEHOLDER)
        self.entry_url.bind("<FocusIn>",  self._clear_ph)
        self.entry_url.bind("<FocusOut>", self._restore_ph)

        # ── Mode Playlist ─────────────────────────────────────────────────────
        pl_frame = tk.Frame(card, bg=CARD)
        pl_frame.pack(fill="x", pady=(0, 12))

        self.pl_check = tk.Checkbutton(
            pl_frame, text="  🎵  Mode Playlist",
            variable=self.playlist_var,
            font=("Courier", 10, "bold"),
            fg=TEXT, bg=CARD, selectcolor=SURFACE,
            activebackground=CARD, activeforeground=ACCENT,
            cursor="hand2", command=self._on_playlist_toggle
        )
        self.pl_check.pack(side="left")

        self.pl_info_label = tk.Label(pl_frame, text="",
                                      font=("Courier", 9), fg=SUBTEXT, bg=CARD)
        self.pl_info_label.pack(side="left", padx=(12, 0))

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(0, 12))

        # ── Format + Qualité ──────────────────────────────────────────────────
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(0, 12))

        fmt_f = tk.Frame(row, bg=CARD)
        fmt_f.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(fmt_f, text="Format", font=("Courier", 9, "bold"),
                 fg=SUBTEXT, bg=CARD).pack(anchor="w")
        btn_row = tk.Frame(fmt_f, bg=CARD)
        btn_row.pack(anchor="w", pady=(4, 0))
        self.btn_mp4 = self._fmt_btn(btn_row, "MP4")
        self.btn_mp3 = self._fmt_btn(btn_row, "MP3")
        self._highlight_format()

        qual_f = tk.Frame(row, bg=CARD)
        qual_f.pack(side="left", fill="x", expand=True)
        tk.Label(qual_f, text="Qualité", font=("Courier", 9, "bold"),
                 fg=SUBTEXT, bg=CARD).pack(anchor="w")
        self.combo_quality = ttk.Combobox(
            qual_f, textvariable=self.quality_var,
            state="readonly", style="Dark.TCombobox", font=("Courier", 10)
        )
        self.combo_quality.pack(fill="x", pady=(4, 0))

        # ── Dossier ───────────────────────────────────────────────────────────
        tk.Label(card, text="Dossier de destination",
                 font=("Courier", 9, "bold"), fg=SUBTEXT, bg=CARD).pack(anchor="w")
        dest_row = tk.Frame(card, bg=CARD)
        dest_row.pack(fill="x", pady=(4, 12))
        dest_inner = tk.Frame(dest_row, bg=BORDER, pady=1, padx=1)
        dest_inner.pack(side="left", fill="x", expand=True)
        self.dest_label = tk.Label(dest_inner, text="",
                                   font=("Courier", 9), fg=ACCENT2,
                                   bg=SURFACE, anchor="w", padx=8, pady=6)
        self.dest_label.pack(fill="x")
        tk.Button(dest_row, text="📂  Changer",
                  font=("Courier", 9, "bold"), bg=SURFACE, fg=TEXT,
                  activebackground=ACCENT2, activeforeground=TEXT,
                  relief="flat", cursor="hand2", padx=10,
                  command=self._browse_folder).pack(side="left", padx=(6, 0))
        tk.Button(dest_row, text="↺",
                  font=("Courier", 11, "bold"), bg=SURFACE, fg=SUBTEXT,
                  activebackground=BORDER, activeforeground=TEXT,
                  relief="flat", cursor="hand2", padx=8,
                  command=self._reset_folder).pack(side="left", padx=(4, 0))
        self._update_dest_label()

        # ── Bouton Télécharger ────────────────────────────────────────────────
        self.btn_dl = tk.Button(
            card, text="⬇  TÉLÉCHARGER",
            font=("Georgia", 13, "bold"),
            bg=ACCENT, fg=TEXT, activebackground=ACCENT2, activeforeground=TEXT,
            relief="flat", cursor="hand2", pady=12, command=self.telecharger
        )
        self.btn_dl.pack(fill="x", pady=(0, 4))

        # ── Progression vidéo courante ────────────────────────────────────────
        ph = tk.Frame(card, bg=CARD)
        ph.pack(fill="x", pady=(12, 2))
        self.prog_title_label = tk.Label(ph, text="Progression vidéo",
                                         font=("Courier", 9, "bold"),
                                         fg=SUBTEXT, bg=CARD)
        self.prog_title_label.pack(side="left")
        self.pct_label = tk.Label(ph, text="0 %",
                                  font=("Courier", 9, "bold"), fg=ACCENT, bg=CARD)
        self.pct_label.pack(side="right")

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            card, orient="horizontal", mode="determinate",
            variable=self.progress_var, style="Accent.Horizontal.TProgressbar"
        )
        self.progress.pack(fill="x")

        self.info_var = tk.StringVar(value="")
        tk.Label(card, textvariable=self.info_var,
                 font=("Courier", 8), fg=SUBTEXT, bg=CARD).pack(anchor="e", pady=(2, 0))

        # ── Progression globale playlist ──────────────────────────────────────
        self.pl_prog_frame = tk.Frame(card, bg=CARD)
        # caché par défaut — affiché uniquement en mode playlist

        pl_ph = tk.Frame(self.pl_prog_frame, bg=CARD)
        pl_ph.pack(fill="x", pady=(6, 2))
        tk.Label(pl_ph, text="Playlist globale",
                 font=("Courier", 9, "bold"), fg=SUBTEXT, bg=CARD).pack(side="left")
        self.pl_pct_label = tk.Label(pl_ph, text="0 / 0",
                                     font=("Courier", 9, "bold"), fg=ACCENT2, bg=CARD)
        self.pl_pct_label.pack(side="right")

        self.pl_progress_var = tk.DoubleVar(value=0)
        self.pl_progress = ttk.Progressbar(
            self.pl_prog_frame, orient="horizontal", mode="determinate",
            variable=self.pl_progress_var, style="Playlist.Horizontal.TProgressbar"
        )
        self.pl_progress.pack(fill="x")

        self.pl_current_label = tk.Label(
            self.pl_prog_frame, text="",
            font=("Courier", 8), fg=SUBTEXT, bg=CARD,
            wraplength=460, justify="left"
        )
        self.pl_current_label.pack(anchor="w", pady=(2, 0))

        # ── Status ────────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="En attente…")
        self.status_label = tk.Label(
            self, textvariable=self.status_var,
            font=("Courier", 10), fg=SUBTEXT, bg=BG
        )
        self.status_label.pack(pady=6)

        # ── Footer ────────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=BG)
        footer.pack(side="bottom", fill="x", padx=24, pady=8)
        tk.Label(footer, text="Fichiers sauvegardés dans le dossier de destination choisi",
                 font=("Courier", 8), fg=SUBTEXT, bg=BG).pack()

    def _configure_styles(self, style):
        style.configure("Dark.TCombobox",
            fieldbackground=SURFACE, background=SURFACE,
            foreground=TEXT, selectbackground=SURFACE, selectforeground=TEXT,
            arrowcolor=ACCENT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
        style.map("Dark.TCombobox",
            fieldbackground=[("readonly", SURFACE)],
            selectbackground=[("readonly", SURFACE)])
        style.configure("Accent.Horizontal.TProgressbar",
            troughcolor=SURFACE, background=ACCENT,
            bordercolor=SURFACE, lightcolor=ACCENT, darkcolor=ACCENT)
        style.configure("Playlist.Horizontal.TProgressbar",
            troughcolor=SURFACE, background=ACCENT2,
            bordercolor=SURFACE, lightcolor=ACCENT2, darkcolor=ACCENT2)

    # ── Format ────────────────────────────────────────────────────────────────
    def _fmt_btn(self, parent, fmt):
        btn = tk.Button(parent, text=fmt, width=6,
                        font=("Courier", 10, "bold"), relief="flat", cursor="hand2",
                        command=lambda f=fmt: self._select_format(f))
        btn.pack(side="left", padx=(0, 6))
        return btn

    def _select_format(self, fmt):
        self.format_var.set(fmt)
        self._highlight_format()
        self._update_quality_options()
        self._update_dest_label()

    def _highlight_format(self):
        sel = self.format_var.get()
        for btn, fmt in [(self.btn_mp4, "MP4"), (self.btn_mp3, "MP3")]:
            btn.config(bg=ACCENT if fmt == sel else SURFACE,
                       fg=TEXT   if fmt == sel else SUBTEXT)

    def _update_quality_options(self):
        opts = list(QUALITY_OPTIONS[self.format_var.get()].keys())
        self.combo_quality["values"] = opts
        self.combo_quality.set(opts[0])

    # ── Dossier ───────────────────────────────────────────────────────────────
    def _update_dest_label(self):
        fmt  = self.format_var.get().lower()
        path = self.custom_dirs[fmt] or DEFAULT_DIRS[fmt]
        display = path if len(path) <= 50 else "…" + path[-48:]
        self.dest_label.config(text=f"📁  {display}",
                               fg=SUCCESS if self.custom_dirs[fmt] else ACCENT2)

    def _browse_folder(self):
        fmt = self.format_var.get().lower()
        chosen = filedialog.askdirectory(
            title=f"Choisir le dossier pour les {fmt.upper()}",
            initialdir=self.custom_dirs[fmt] or DEFAULT_DIRS[fmt],
            mustexist=True)
        if chosen:
            self.custom_dirs[fmt] = chosen
            os.makedirs(chosen, exist_ok=True)
            self._update_dest_label()

    def _reset_folder(self):
        self.custom_dirs[self.format_var.get().lower()] = None
        self._update_dest_label()

    def _get_out_dir(self):
        fmt = self.format_var.get().lower()
        return self.custom_dirs[fmt] or DEFAULT_DIRS[fmt]

    # ── Placeholder ───────────────────────────────────────────────────────────
    def _clear_ph(self, _):
        if self.entry_url.get() == PLACEHOLDER:
            self.entry_url.delete(0, "end")
            self.entry_url.config(fg=TEXT)

    def _restore_ph(self, _):
        if not self.entry_url.get():
            self.entry_url.insert(0, PLACEHOLDER)
            self.entry_url.config(fg=SUBTEXT)

    # ── Playlist toggle ───────────────────────────────────────────────────────
    def _on_playlist_toggle(self):
        if self.playlist_var.get():
            self.pl_info_label.config(
                text="Toutes les vidéos seront téléchargées dans un sous-dossier",
                fg=ACCENT2)
            self.pl_prog_frame.pack(fill="x")
        else:
            self.pl_info_label.config(text="")
            self.pl_prog_frame.pack_forget()

    # =========================================================================
    # TÉLÉCHARGEMENT
    # =========================================================================
    def telecharger(self):
        url = self.entry_url.get().strip()
        if not url or url == PLACEHOLDER:
            messagebox.showwarning("Attention", "Veuillez coller une URL YouTube valide.")
            return
        threading.Thread(target=self._run, args=(url,), daemon=True).start()

    # ── Hook vidéo courante ───────────────────────────────────────────────────
    def _progress_hook(self, d):
        if d["status"] == "downloading":
            total      = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            speed      = d.get("speed") or 0
            eta        = d.get("eta") or 0
            pct        = (downloaded / total * 100) if total else 0

            speed_str = (f"{speed/1_048_576:.1f} MB/s" if speed >= 1_048_576
                         else f"{speed/1024:.0f} KB/s" if speed >= 1024
                         else f"{speed:.0f} B/s")
            eta_str   = f"{eta//60}m {eta%60:02d}s" if eta >= 60 else f"{eta}s"

            self.after(0, self._update_progress, pct,
                       f"⚡ {speed_str}   ⏱ {eta_str} restant")

            # Mise à jour compteur playlist depuis les métadonnées du hook
            idx   = d.get("playlist_index")
            count = d.get("playlist_count")
            if idx and count:
                self._pl_total = count
                pl_pct = ((idx - 1) / count * 100)
                title  = d.get("info_dict", {}).get("title", "")
                self.after(0, self._update_pl_progress,
                           idx - 1, count, pl_pct, title)

        elif d["status"] == "finished":
            self.after(0, self._update_progress, 100, "🔄  Finalisation…")
            # Incrémenter compteur playlist
            if self._pl_total:
                self._pl_done = min(self._pl_done + 1, self._pl_total)
                pl_pct = (self._pl_done / self._pl_total * 100)
                self.after(0, self._update_pl_progress,
                           self._pl_done, self._pl_total, pl_pct, "")

    def _update_progress(self, pct, info):
        self.progress_var.set(pct)
        self.pct_label.config(text=f"{pct:.0f} %")
        self.info_var.set(info)

    def _update_pl_progress(self, done, total, pct, title):
        self.pl_progress_var.set(pct)
        self.pl_pct_label.config(text=f"{done} / {total}")
        if title:
            short = title[:62] + "…" if len(title) > 62 else title
            self.pl_current_label.config(text=f"▶  {short}")

    # ── Cœur ──────────────────────────────────────────────────────────────────
    def _run(self, url):
        self.btn_dl.config(state="disabled")
        self.after(0, self._update_progress, 0, "")

        fmt     = self.format_var.get()
        quality = self.quality_var.get()
        q_value = QUALITY_OPTIONS[fmt][quality]
        out_dir = self._get_out_dir()
        is_pl   = self.playlist_var.get()

        self._pl_total = 0
        self._pl_done  = 0

        # En mode playlist : sous-dossier portant le nom de la playlist
        outtmpl = (
            os.path.join(out_dir,
                         "%(playlist_title)s",
                         "%(playlist_index)s - %(title)s.%(ext)s")
            if is_pl else
            os.path.join(out_dir, "%(title)s.%(ext)s")
        )

        base_opts = {
            "outtmpl"        : outtmpl,
            "progress_hooks" : [self._progress_hook],
            "noplaylist"     : not is_pl,
        }

        if fmt == "MP4":
            ydl_opts = {**base_opts,
                        "format"              : q_value,
                        "merge_output_format" : "mp4"}
        else:
            ydl_opts = {**base_opts,
                        "format"        : "bestaudio/best",
                        "postprocessors": [{
                            "key"             : "FFmpegExtractAudio",
                            "preferredcodec"  : "mp3",
                            "preferredquality": q_value,
                        }]}

        label = "playlist" if is_pl else fmt
        self._set_status(f"⏳  Téléchargement {label} en cours…", SUBTEXT)

        # Récupérer d'abord le nombre de vidéos de la playlist
        if is_pl:
            try:
                with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": False,
                                        "extract_flat": True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    entries = info.get("entries", [])
                    self._pl_total = len(entries)
                    self.after(0, self._update_pl_progress,
                               0, self._pl_total, 0,
                               f"Playlist : {info.get('title','?')}  ({self._pl_total} vidéos)")
            except Exception:
                pass

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, self._update_progress, 100, "✅  Terminé !")
            if is_pl and self._pl_total:
                self.after(0, self._update_pl_progress,
                           self._pl_total, self._pl_total, 100, "✅  Playlist complète !")
            self._set_status(f"✅  Enregistré dans {out_dir}", SUCCESS)
            messagebox.showinfo("Terminé !",
                                f"Téléchargement terminé !\n\n📁 {out_dir}")
        except Exception as e:
            self._set_status(f"❌  Erreur : {e}", ERROR)
            messagebox.showerror("Erreur", str(e))
        finally:
            self.btn_dl.config(state="normal")
            self.entry_url.delete(0, "end")
            self._restore_ph(None)

    def _set_status(self, msg, color=SUBTEXT):
        self.status_var.set(msg)
        self.status_label.config(fg=color)


if __name__ == "__main__":
    app = App()
    app.mainloop()