"""
Get Downloader - YouTube Downloader (Dark Blue & White UI)
Requirements:
    pip install yt-dlp requests pyperclip pillow
"""

import os
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request, zipfile, shutil
from yt_dlp import YoutubeDL
from PIL import Image, ImageTk

# ---------- Utility ----------
def bytes_to_human(num):
    for unit in ['B','KB','MB','GB','TB']:
        if num < 1024.0:
            return f"{num:3.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}PB"


# ---------- Auto FFmpeg Setup ----------
def ensure_ffmpeg_installed():
    ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
    if os.path.exists(ffmpeg_path):
        return ffmpeg_path

    messagebox.showinfo("FFmpeg", "FFmpeg not found. Downloading automatically...")

    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = "ffmpeg.zip"
    extract_dir = os.path.join(os.getcwd(), "ffmpeg_temp")

    try:
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        inner_dir = None
        for item in os.listdir(extract_dir):
            if item.lower().startswith("ffmpeg"):
                inner_dir = os.path.join(extract_dir, item)
                break

        final_path = os.path.join(os.getcwd(), "ffmpeg")
        shutil.move(inner_dir, final_path)
    except Exception as e:
        messagebox.showerror("FFmpeg Error", f"Failed to install FFmpeg: {e}")
    finally:
        if os.path.exists(zip_path): os.remove(zip_path)
        if os.path.exists(extract_dir): shutil.rmtree(extract_dir, ignore_errors=True)

    return ffmpeg_path if os.path.exists(ffmpeg_path) else None


# ---------- Progress Hook ----------
def ytdl_progress_hook(d, gui=None, url=None):
    if d['status'] == 'downloading' and gui:
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes', 0)
        percent = (downloaded / total * 100) if total else 0.0
        speed = d.get('speed')
        eta = d.get('eta')
        gui.update_progress(url, percent, speed, eta)
    elif d['status'] == 'finished' and gui:
        gui.update_progress(url, 100)
        gui.set_status("Processing...")


# ---------- GUI ----------
class GetDownloaderGUI:
    def __init__(self, root):
        self.root = root
        root.title("Get Downloader")
        root.geometry("950x600")
        root.configure(bg="#FFFFFF")
        root.minsize(850, 550)

        self.download_list = []
        self.progress_bars = {}
        self.labels = {}
        self.history_file = "download_history.json"
        self.history = self.load_history()

        # ---------- Top Bar ----------
        top_frame = tk.Frame(root, bg="#0D47A1", height=60)
        top_frame.pack(fill='x')

        # إضافة الصورة الصغيرة (logo)
        try:
            logo_img = Image.open("logo.png")
            logo_img = logo_img.resize((40, 40), Image.ANTIALIAS)  # حجم صغير
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            tk.Label(top_frame, image=self.logo_photo, bg="#0D47A1").pack(side="left", padx=10, pady=10)
        except Exception as e:
            print("Logo not loaded:", e)

        tk.Label(top_frame, text="🎧  Get Downloader", bg="#0D47A1", fg="white",
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=10, pady=10)

        tk.Button(top_frame, text="About", bg="white", fg="#0D47A1", font=("Segoe UI", 10, "bold"),
                  relief='ridge', command=self.show_about).pack(side="right", padx=10, pady=10)

        # ---------- Input Area ----------
        input_frame = tk.Frame(root, bg="#FFFFFF", padx=20, pady=15)
        input_frame.pack(fill='x')

        tk.Label(input_frame, text="YouTube URL:", bg="#FFFFFF", fg="#0D47A1",
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', pady=5)
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(input_frame, textvariable=self.url_var, font=("Segoe UI", 10), width=60)
        self.url_entry.grid(row=0, column=1, padx=10, sticky='w')

        tk.Button(input_frame, text="Paste", bg="#2196F3", fg="white", font=("Segoe UI", 9, "bold"),
                  command=self.paste_clipboard).grid(row=0, column=2, padx=5)

        tk.Button(input_frame, text="Add to Download", bg="#43A047", fg="white", font=("Segoe UI", 9, "bold"),
                  command=self.add_to_download).grid(row=0, column=3, padx=5)

        # ---------- Settings ----------
        settings_frame = tk.LabelFrame(root, text="Settings", bg="#FFFFFF", fg="#0D47A1", font=("Segoe UI", 10, "bold"),
                                       padx=20, pady=10)
        settings_frame.pack(fill='x', padx=20)

        self.mode_var = tk.StringVar(value='video')
        tk.Radiobutton(settings_frame, text="Video", variable=self.mode_var, value='video',
                       bg="#FFFFFF", fg="#0D47A1", selectcolor="#E3F2FD").grid(row=0, column=0, padx=10)
        tk.Radiobutton(settings_frame, text="Audio (MP3)", variable=self.mode_var, value='audio',
                       bg="#FFFFFF", fg="#0D47A1", selectcolor="#E3F2FD").grid(row=0, column=1, padx=10)

        tk.Label(settings_frame, text="Quality:", bg="#FFFFFF", fg="#0D47A1",
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=5)
        self.quality_var = tk.StringVar(value="1080")
        ttk.Combobox(settings_frame, textvariable=self.quality_var, values=["1080", "720", "480", "360"],
                     width=6).grid(row=0, column=3, padx=5)

        tk.Label(settings_frame, text="Save to:", bg="#FFFFFF", fg="#0D47A1",
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, pady=8, sticky='w')
        self.out_var = tk.StringVar(value=os.getcwd())
        tk.Entry(settings_frame, textvariable=self.out_var, width=50).grid(row=1, column=1, columnspan=2, sticky='w')
        tk.Button(settings_frame, text="Browse", bg="#2196F3", fg="white",
                  command=self.browse_out).grid(row=1, column=3, padx=5)

        # ---------- Download List ----------
        list_frame = tk.LabelFrame(root, text="Download List", bg="#FFFFFF", fg="#0D47A1",
                                   font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)

        canvas = tk.Canvas(list_frame, bg="#FFFFFF", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        self.scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # ---------- Control Buttons ----------
        controls = tk.Frame(root, bg="#FFFFFF", pady=10)
        controls.pack(fill='x')
        tk.Button(controls, text="Start Download", bg="#0D47A1", fg="white", font=("Segoe UI", 10, "bold"),
                  command=self.start_downloads).pack(side="left", padx=20)
        tk.Button(controls, text="Clear List", bg="#f44336", fg="white", font=("Segoe UI", 10, "bold"),
                  command=self.clear_list).pack(side="left")

        # ---------- Status Bar ----------
        status_bar = tk.Frame(root, bg="#0D47A1", height=25)
        status_bar.pack(fill='x', side='bottom')
        self.status_text = tk.StringVar(value="Ready")
        tk.Label(status_bar, textvariable=self.status_text, bg="#0D47A1", fg="white",
                 anchor='w', font=("Segoe UI", 9)).pack(fill='x', padx=10)

    # ---------- Functions ----------
    def show_about(self):
        messagebox.showinfo("About Get", "Get Downloader\nVersion 2.0\nBlue-White UI\nCreated by Raad ✨")

    def set_status(self, text):
        self.status_text.set(text)

    def paste_clipboard(self):
        try:
            import pyperclip
            self.url_var.set(pyperclip.paste())
            self.set_status("Pasted from clipboard.")
        except Exception:
            self.set_status("Clipboard not available.")

    def browse_out(self):
        folder = filedialog.askdirectory(initialdir=self.out_var.get() or os.getcwd())
        if folder:
            self.out_var.set(folder)

    def add_to_download(self):
        url = self.url_var.get().strip()
        if not url:
            self.set_status("Please enter a URL.")
            return
        if url in self.download_list:
            self.set_status("URL already added.")
            return

        self.download_list.append(url)
        frame = tk.Frame(self.scrollable_frame, bg="#E3F2FD", bd=1, relief='solid')
        frame.pack(fill='x', pady=4, padx=2)
        label = tk.Label(frame, text=url, bg="#E3F2FD", anchor='w', fg="#0D47A1", font=("Segoe UI", 9))
        label.pack(fill='x', padx=5, pady=2)
        pb = ttk.Progressbar(frame, orient='horizontal', length=400, mode='determinate')
        pb.pack(fill='x', padx=10, pady=5)
        self.labels[url] = label
        self.progress_bars[url] = pb
        self.set_status(f"Added: {url}")
        self.url_var.set("")

    def clear_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.download_list.clear()
        self.progress_bars.clear()
        self.labels.clear()
        self.set_status("Download list cleared.")

    def start_downloads(self):
        if not self.download_list:
            self.set_status("No URLs to download.")
            return
        for url in self.download_list:
            threading.Thread(target=self.download_worker, args=(url,), daemon=True).start()

    def update_progress(self, url, percent, speed=None, eta=None):
        if url in self.progress_bars:
            self.progress_bars[url]['value'] = percent
        msg = f"{percent:.1f}%"
        if speed: msg += f" | {bytes_to_human(speed)}/s"
        if eta: msg += f" | ETA {int(eta)}s"
        self.set_status(msg)

    def download_worker(self, url):
        try:
            ffmpeg_exe = ensure_ffmpeg_installed()
            outtmpl = os.path.join(self.out_var.get(), "%(title)s.%(ext)s")
            mode = self.mode_var.get()
            quality = self.quality_var.get()
            fmt = f"bestvideo[height<={quality}]+bestaudio/best" if mode == 'video' else "bestaudio"

            ydl_opts = {
                'outtmpl': outtmpl,
                'format': fmt,
                'noplaylist': True,
                'progress_hooks': [lambda d: ytdl_progress_hook(d, gui=self, url=url)],
                'quiet': True,
                'ffmpeg_location': os.path.dirname(ffmpeg_exe)
            }

            if mode == 'audio':
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'unknown')
                self.set_status(f"✅ Done: {title}")
        except Exception as e:
            messagebox.showerror("Download Error", str(e))
            self.set_status("Error occurred")

    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()

    # تعيين أيقونة البرنامج
    try:
        root.iconbitmap("icon.ico")
    except Exception as e:
        print("Icon not loaded:", e)

    app = GetDownloaderGUI(root)
    root.mainloop()
