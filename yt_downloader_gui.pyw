"""
yt_downloader_gui.py
A simple GUI YouTube downloader using yt-dlp and Tkinter.

Requirements:
    pip install yt-dlp pyperclip
Optional:
    ffmpeg in PATH (for audio conversion/extraction)
    pyinstaller (to create .exe): pip install pyinstaller
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
try:
    import pyperclip
    CLIP_AVAILABLE = True
except Exception:
    CLIP_AVAILABLE = False

from yt_dlp import YoutubeDL

# ---------- Helper: yt-dlp progress hook ----------
def ytdl_progress_hook(d):
    """
    d is a dict with keys like 'status', 'downloaded_bytes', 'total_bytes', 'speed', 'eta'
    We'll pass human-readable messages to the GUI via callback.
    """
    if gui_instance is None:
        return
    status = d.get('status')
    if status == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes', 0)
        percent = (downloaded / total * 100) if total else 0.0
        speed = d.get('speed')
        eta = d.get('eta')
        msg = f"Downloading... {percent:.1f}%"
        if speed:
            msg += f" | {bytes_to_human(speed)}/s"
        if eta:
            msg += f" | ETA {int(eta)}s"
        gui_instance.set_status(msg)
    elif status == 'finished':
        gui_instance.set_status("Merging/processing...")

# ---------- Utility ----------
def bytes_to_human(num):
    for unit in ['B','KB','MB','GB','TB']:
        if num < 1024.0:
            return f"{num:3.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}PB"

# ---------- GUI Class ----------
class YTDownloaderGUI:
    def __init__(self, root):
        self.root = root
        root.title("YT Downloader")
        root.geometry("620x320")
        root.resizable(False, False)

        # URL
        tk.Label(root, text="YouTube URL:").place(x=10, y=10)
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(root, textvariable=self.url_var, width=60)
        self.url_entry.place(x=100, y=10)

        if CLIP_AVAILABLE:
            tk.Button(root, text="Paste from clipboard", command=self.paste_clipboard).place(x=490, y=6)

        # Mode: video / audio
        tk.Label(root, text="Mode:").place(x=10, y=50)
        self.mode_var = tk.StringVar(value='video')
        tk.Radiobutton(root, text="Video", variable=self.mode_var, value='video').place(x=100, y=50)
        tk.Radiobutton(root, text="Audio (mp3)", variable=self.mode_var, value='audio').place(x=170, y=50)

        # Quality preset
        tk.Label(root, text="Quality:").place(x=10, y=85)
        self.quality_var = tk.StringVar(value='mp4')
        tk.OptionMenu(root, self.quality_var, 'mp4 (best mp4)', 'best', 'bestvideo+bestaudio').place(x=100,y=80)

        # Output folder
        tk.Label(root, text="Save to:").place(x=10, y=120)
        self.out_var = tk.StringVar(value=os.getcwd())
        tk.Entry(root, textvariable=self.out_var, width=45).place(x=100, y=120)
        tk.Button(root, text="Browse", command=self.browse_out).place(x=490, y=116)

        # Cookies
        tk.Label(root, text="Cookies (optional):").place(x=10, y=155)
        self.cookies_var = tk.StringVar(value="")
        tk.Entry(root, textvariable=self.cookies_var, width=45).place(x=140, y=155)
        tk.Button(root, text="Load cookies.txt", command=self.load_cookies).place(x=490, y=151)

        # Control buttons
        self.download_btn = tk.Button(root, text="Download", width=12, command=self.start_download_thread)
        self.download_btn.place(x=100, y=200)
        tk.Button(root, text="Clear URL", width=12, command=self.clear_url).place(x=240, y=200)
        tk.Button(root, text="Open Output Folder", width=18, command=self.open_out_folder).place(x=380, y=200)

        # Status / log
        tk.Label(root, text="Status:").place(x=10, y=250)
        self.status_text = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status_text, anchor='w', width=70, relief='sunken').place(x=10, y=270)

    def paste_clipboard(self):
        try:
            text = pyperclip.paste()
            self.url_var.set(text)
            self.set_status("Pasted from clipboard.")
        except Exception as e:
            self.set_status("Clipboard paste failed.")

    def browse_out(self):
        folder = filedialog.askdirectory(initialdir=self.out_var.get() or os.getcwd())
        if folder:
            self.out_var.set(folder)

    def load_cookies(self):
        path = filedialog.askopenfilename(filetypes=[("Cookies file","*.txt"),("All files","*.*")])
        if path:
            self.cookies_var.set(path)
            self.set_status(f"Cookies loaded: {os.path.basename(path)}")

    def clear_url(self):
        self.url_var.set("")
        self.set_status("URL cleared.")

    def open_out_folder(self):
        folder = self.out_var.get()
        if os.path.isdir(folder):
            os.startfile(folder)
        else:
            self.set_status("Output folder does not exist.")

    def set_status(self, text):
        # update GUI from any thread safely
        def _update():
            self.status_text.set(text)
        self.root.after(0, _update)

    def start_download_thread(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Input required", "Please paste a YouTube URL first.")
            return
        # Disable button to prevent reentry
        self.download_btn.config(state='disabled')
        threading.Thread(target=self.download_worker, args=(url,), daemon=True).start()

    def download_worker(self, url):
        try:
            outtmpl = os.path.join(self.out_var.get(), "%(title)s - %(id)s.%(ext)s")
            mode = self.mode_var.get()
            quality = self.quality_var.get()

            # format selection
            if mode == 'audio':
                fmt = 'bestaudio'
            else:
                if 'mp4' in quality:
                    fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                elif 'bestvideo' in quality:
                    fmt = "bestvideo+bestaudio/best"
                else:
                    fmt = "best"

            ydl_opts = {
                'outtmpl': outtmpl,
                'format': fmt,
                'noplaylist': True,
                'progress_hooks': [ytdl_progress_hook],
                'quiet': False,
                'noprogress': True,  # we use hooks to show progress
                'no_warnings': True,
            }

            # cookies
            cookies_path = self.cookies_var.get().strip()
            if cookies_path:
                ydl_opts['cookiefile'] = cookies_path

            # postprocessor if audio
            if mode == 'audio':
                ydl_opts.update({
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                })

            self.set_status("Starting download...")
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'unknown') if isinstance(info, dict) else str(info)
                self.set_status(f"Downloaded: {title}")
                messagebox.showinfo("Done", f"Downloaded: {title}\nSaved to: {self.out_var.get()}")
        except Exception as e:
            self.set_status(f"Error: {str(e)[:200]}")
            messagebox.showerror("Download error", f"{str(e)}")
        finally:
            self.download_btn.config(state='normal')

# ---------- Create GUI ----------
gui_instance = None

def main():
    global gui_instance
    root = tk.Tk()
    gui_instance = YTDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
