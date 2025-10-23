"""
YT Downloader Dark Mode GUI - Auto FFmpeg Installer
Requirements:
    pip install yt-dlp pyperclip requests
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import urllib.request
import zipfile
import shutil

# ----------- Auto FFmpeg Setup -----------
def ensure_ffmpeg_installed():
    ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")

    if os.path.exists(ffmpeg_path):
        return ffmpeg_path  # ✅ موجود بالفعل

    print("🔄 FFmpeg غير مثبت - يتم تحميله الآن...")

    # رابط مباشر من الموقع الرسمي
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = "ffmpeg.zip"
    extract_dir = os.path.join(os.getcwd(), "ffmpeg_temp")

    try:
        urllib.request.urlretrieve(url, zip_path)
        print("✅ تم تحميل FFmpeg بنجاح")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # العثور على مجلد ffmpeg الرئيسي
        inner_dir = None
        for item in os.listdir(extract_dir):
            if item.lower().startswith("ffmpeg"):
                inner_dir = os.path.join(extract_dir, item)
                break

        if not inner_dir:
            raise RuntimeError("لم يتم العثور على مجلد FFmpeg داخل الملف المضغوط.")

        final_path = os.path.join(os.getcwd(), "ffmpeg")
        shutil.move(inner_dir, final_path)

        print("✅ تم تثبيت FFmpeg في:", final_path)

    except Exception as e:
        print("❌ خطأ أثناء تثبيت ffmpeg:", e)
        messagebox.showerror("FFmpeg Error", f"فشل تثبيت FFmpeg تلقائيًا.\nالرجاء تثبيته يدويًا.\n{e}")
    finally:
        # تنظيف الملفات المؤقتة
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)

    return ffmpeg_path if os.path.exists(ffmpeg_path) else None


# ----------- المكتبات الإضافية -----------
try:
    import pyperclip
    CLIP_AVAILABLE = True
except Exception:
    CLIP_AVAILABLE = False

from yt_dlp import YoutubeDL

# ---------- Progress hook ----------
def ytdl_progress_hook(d):
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

# ---------- GUI ----------
class YTDownloaderDarkGUI:
    def __init__(self, root):
        self.root = root
        root.title("YT Downloader Dark")
        root.geometry("640x360")
        root.resizable(False, False)
        root.configure(bg="#1E1E1E")

        # URL
        tk.Label(root, text="YouTube URL:", fg="white", bg="#1E1E1E", font=("Arial", 10, "bold")).place(x=10, y=10)
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(root, textvariable=self.url_var, width=55, font=("Arial", 10))
        self.url_entry.place(x=120, y=10)

        if CLIP_AVAILABLE:
            tk.Button(root, text="Paste", bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                      command=self.paste_clipboard).place(x=520, y=7)

        # Mode
        tk.Label(root, text="Mode:", fg="white", bg="#1E1E1E", font=("Arial", 10, "bold")).place(x=10, y=50)
        self.mode_var = tk.StringVar(value='video')
        tk.Radiobutton(root, text="Video", variable=self.mode_var, value='video', fg="white", bg="#1E1E1E",
                       selectcolor="#1E1E1E").place(x=100, y=50)
        tk.Radiobutton(root, text="Audio (mp3)", variable=self.mode_var, value='audio', fg="white", bg="#1E1E1E",
                       selectcolor="#1E1E1E").place(x=180, y=50)

        # Output folder
        tk.Label(root, text="Save to:", fg="white", bg="#1E1E1E", font=("Arial", 10, "bold")).place(x=10, y=120)
        self.out_var = tk.StringVar(value=os.getcwd())
        tk.Entry(root, textvariable=self.out_var, width=45, font=("Arial", 10)).place(x=100, y=120)
        tk.Button(root, text="Browse", bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                  command=self.browse_out).place(x=520, y=116)

        # Control buttons
        self.download_btn = tk.Button(root, text="Download", bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                      command=self.start_download_thread)
        self.download_btn.place(x=100, y=200)
        tk.Button(root, text="Clear URL", bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                  command=self.clear_url).place(x=240, y=200)
        tk.Button(root, text="Open Output Folder", bg="#FF9800", fg="white", font=("Arial", 10, "bold"),
                  command=self.open_out_folder).place(x=380, y=200)

        # Status
        tk.Label(root, text="Status:", fg="white", bg="#1E1E1E", font=("Arial", 10, "bold")).place(x=10, y=250)
        self.status_text = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status_text, anchor='w', width=70, relief='sunken', bg="#333333",
                 fg="white", font=("Arial", 10)).place(x=10, y=270)

    # ---------- GUI Methods ----------
    def paste_clipboard(self):
        try:
            text = pyperclip.paste()
            self.url_var.set(text)
            self.set_status("Pasted from clipboard.")
        except Exception:
            self.set_status("Clipboard paste failed.")

    def browse_out(self):
        folder = filedialog.askdirectory(initialdir=self.out_var.get() or os.getcwd())
        if folder:
            self.out_var.set(folder)

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
        def _update():
            self.status_text.set(text)
        self.root.after(0, _update)

    def start_download_thread(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Input required", "Please paste a YouTube URL first.")
            return
        self.download_btn.config(state='disabled')
        threading.Thread(target=self.download_worker, args=(url,), daemon=True).start()

    def download_worker(self, url):
        try:
            ffmpeg_exe = ensure_ffmpeg_installed()
            if not ffmpeg_exe:
                self.set_status("FFmpeg installation failed.")
                return

            outtmpl = os.path.join(self.out_var.get(), "%(title)s - %(id)s.%(ext)s")
            mode = self.mode_var.get()
            fmt = "bestvideo+bestaudio/best" if mode == 'video' else "bestaudio"

            ydl_opts = {
                'outtmpl': outtmpl,
                'format': fmt,
                'noplaylist': True,
                'progress_hooks': [ytdl_progress_hook],
                'quiet': False,
                'ffmpeg_location': os.path.dirname(ffmpeg_exe),
            }

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


# ---------- Run ----------
gui_instance = None
def main():
    global gui_instance
    root = tk.Tk()
    gui_instance = YTDownloaderDarkGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
