"""
Baixador - estilo aTube Catcher (yt-dlp + FFmpeg + Tkinter)

Requisitos:
    pip install yt-dlp
    FFmpeg instalado e no PATH (https://ffmpeg.org/download.html)

Executar:
    python baixador.py

Use apenas para conteúdo que você tem direito de baixar
(seus próprios vídeos, licenças livres/Creative Commons, domínio público, etc.).
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import yt_dlp

FORMATOS_AUDIO = {"MP3": "mp3", "M4A": "m4a", "WAV": "wav", "OPUS": "opus", "FLAC": "flac"}
FORMATOS_VIDEO = {"MP4": "mp4", "MKV": "mkv", "WEBM": "webm"}
QUALIDADES_VIDEO = ["Melhor", "1080p", "720p", "480p", "360p"]
QUALIDADES_AUDIO = ["320", "192", "128"]


class Cancelado(Exception):
    pass


class LogYDL:
    def __init__(self, fila):
        self.fila = fila

    def debug(self, msg):
        if not msg.startswith("[debug]"):
            pass

    def info(self, msg):
        self.fila.put(("log", msg))

    def warning(self, msg):
        self.fila.put(("log", f"AVISO: {msg}"))

    def error(self, msg):
        self.fila.put(("log", f"ERRO: {msg}"))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Baixador de Músicas e Vídeos")
        self.geometry("720x620")
        self.minsize(640, 560)

        self.fila = queue.Queue()
        self.cancelar = threading.Event()
        self.thread = None

        self.pasta = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.formato = tk.StringVar(value="MP3")
        self.qualidade = tk.StringVar(value="192")
        self.playlist = tk.BooleanVar(value=True)
        self.legenda = tk.BooleanVar(value=False)
        self.miniatura = tk.BooleanVar(value=False)

        self._montar_ui()
        self._atualizar_qualidades()
        self.after(100, self._processar_fila)

    # ---------- Interface ----------
    def _montar_ui(self):
        pad = {"padx": 10, "pady": 4}

        ttk.Label(self, text="Links (um por linha: vídeos ou playlists):").pack(anchor="w", **pad)
        self.txt_urls = tk.Text(self, height=6, wrap="none")
        self.txt_urls.pack(fill="x", **pad)

        # Opções
        frm = ttk.LabelFrame(self, text="Opções")
        frm.pack(fill="x", **pad)

        ttk.Label(frm, text="Formato:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        formatos = list(FORMATOS_AUDIO) + list(FORMATOS_VIDEO)
        cb_fmt = ttk.Combobox(frm, textvariable=self.formato, values=formatos,
                              state="readonly", width=10)
        cb_fmt.grid(row=0, column=1, padx=4)
        cb_fmt.bind("<<ComboboxSelected>>", lambda e: self._atualizar_qualidades())

        self.lbl_q = ttk.Label(frm, text="Qualidade:")
        self.lbl_q.grid(row=0, column=2, sticky="w", padx=(16, 4))
        self.cb_q = ttk.Combobox(frm, textvariable=self.qualidade, state="readonly", width=10)
        self.cb_q.grid(row=0, column=3, padx=4)

        ttk.Checkbutton(frm, text="Baixar playlist inteira", variable=self.playlist)\
            .grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        ttk.Checkbutton(frm, text="Legendas", variable=self.legenda)\
            .grid(row=1, column=2, sticky="w", padx=8)
        ttk.Checkbutton(frm, text="Miniatura", variable=self.miniatura)\
            .grid(row=1, column=3, sticky="w", padx=8)

        # Pasta
        frm2 = ttk.Frame(self)
        frm2.pack(fill="x", **pad)
        ttk.Label(frm2, text="Salvar em:").pack(side="left")
        ttk.Entry(frm2, textvariable=self.pasta).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(frm2, text="Escolher...", command=self._escolher_pasta).pack(side="left")

        # Botões
        frm3 = ttk.Frame(self)
        frm3.pack(fill="x", **pad)
        self.btn_baixar = ttk.Button(frm3, text="Baixar", command=self._iniciar)
        self.btn_baixar.pack(side="left")
        self.btn_cancelar = ttk.Button(frm3, text="Cancelar", command=self._cancelar,
                                       state="disabled")
        self.btn_cancelar.pack(side="left", padx=6)

        # Progresso
        self.barra = ttk.Progressbar(self, maximum=100)
        self.barra.pack(fill="x", **pad)
        self.lbl_status = ttk.Label(self, text="Pronto.")
        self.lbl_status.pack(anchor="w", padx=10)

        # Log
        self.log = tk.Text(self, height=12, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True, **pad)

    def _atualizar_qualidades(self):
        if self.formato.get() in FORMATOS_AUDIO:
            self.lbl_q.config(text="Bitrate (kbps):")
            self.cb_q["values"] = QUALIDADES_AUDIO
            self.qualidade.set("192")
        else:
            self.lbl_q.config(text="Resolução:")
            self.cb_q["values"] = QUALIDADES_VIDEO
            self.qualidade.set("Melhor")

    def _escolher_pasta(self):
        p = filedialog.askdirectory(initialdir=self.pasta.get())
        if p:
            self.pasta.set(p)

    def _escrever_log(self, texto):
        self.log.config(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    # ---------- Download ----------
    def _iniciar(self):
        urls = [u.strip() for u in self.txt_urls.get("1.0", "end").splitlines() if u.strip()]
        if not urls:
            messagebox.showwarning("Atenção", "Cole pelo menos um link.")
            return
        pasta = self.pasta.get()
        os.makedirs(pasta, exist_ok=True)

        self.cancelar.clear()
        self.btn_baixar.config(state="disabled")
        self.btn_cancelar.config(state="normal")
        self.barra["value"] = 0
        self.thread = threading.Thread(target=self._baixar, args=(urls, pasta), daemon=True)
        self.thread.start()

    def _cancelar(self):
        self.cancelar.set()
        self.lbl_status.config(text="Cancelando...")

    def _opcoes(self, pasta):
        fmt = self.formato.get()
        q = self.qualidade.get()
        modelo = "%(playlist_title|Avulsos)s/%(title)s.%(ext)s" if self.playlist.get() \
            else "%(title)s.%(ext)s"

        opts = {
            "outtmpl": os.path.join(pasta, modelo),
            "noplaylist": not self.playlist.get(),
            "ignoreerrors": True,
            "restrictfilenames": False,
            "windowsfilenames": True,
            "logger": LogYDL(self.fila),
            "progress_hooks": [self._hook],
            "writesubtitles": self.legenda.get(),
            "writeautomaticsub": False,
            "subtitleslangs": ["pt", "pt-BR", "en"],
            "writethumbnail": self.miniatura.get(),
            "postprocessors": [],
        }

        if fmt in FORMATOS_AUDIO:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"].append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": FORMATOS_AUDIO[fmt],
                "preferredquality": q,
            })
            opts["postprocessors"].append({"key": "FFmpegMetadata"})
            opts["postprocessors"].append({"key": "EmbedThumbnail"}) \
                if self.miniatura.get() and fmt in ("MP3", "M4A", "FLAC") else None
            opts["postprocessors"] = [p for p in opts["postprocessors"] if p]
        else:
            altura = "" if q == "Melhor" else f"[height<={q[:-1]}]"
            opts["format"] = f"bestvideo{altura}+bestaudio/best{altura}"
            opts["merge_output_format"] = FORMATOS_VIDEO[fmt]
            opts["postprocessors"].append({"key": "FFmpegMetadata"})
        return opts

    def _hook(self, d):
        if self.cancelar.is_set():
            raise Cancelado()
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            baixado = d.get("downloaded_bytes", 0)
            pct = (baixado / total * 100) if total else 0
            vel = d.get("_speed_str", "").strip()
            eta = d.get("_eta_str", "").strip()
            nome = os.path.basename(d.get("filename", ""))
            self.fila.put(("progresso", pct, f"{nome}  |  {pct:.1f}%  |  {vel}  |  ETA {eta}"))
        elif d["status"] == "finished":
            self.fila.put(("progresso", 100, "Convertendo/finalizando..."))

    def _baixar(self, urls, pasta):
        try:
            with yt_dlp.YoutubeDL(self._opcoes(pasta)) as ydl:
                ydl.download(urls)
            self.fila.put(("fim", "Concluído!"))
        except Cancelado:
            self.fila.put(("fim", "Download cancelado."))
        except yt_dlp.utils.DownloadError as e:
            if self.cancelar.is_set():
                self.fila.put(("fim", "Download cancelado."))
            else:
                self.fila.put(("fim", f"Erro: {e}"))
        except Exception as e:  # noqa: BLE001
            self.fila.put(("fim", f"Erro inesperado: {e}"))

    def _processar_fila(self):
        try:
            while True:
                item = self.fila.get_nowait()
                if item[0] == "log":
                    self._escrever_log(item[1])
                elif item[0] == "progresso":
                    self.barra["value"] = item[1]
                    self.lbl_status.config(text=item[2])
                elif item[0] == "fim":
                    self.lbl_status.config(text=item[1])
                    self._escrever_log(item[1])
                    self.btn_baixar.config(state="normal")
                    self.btn_cancelar.config(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self._processar_fila)


if __name__ == "__main__":
    App().mainloop()
