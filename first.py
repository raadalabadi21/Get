# download_youtube.py
# Simple YouTube downloader script using yt-dlp
# Usage: python download_youtube.py

import sys
try:
    from yt_dlp import YoutubeDL
except Exception as e:
    print("yt-dlp is not installed. Install it with: pip install yt-dlp")
    sys.exit(1)

def download(url, audio_only=False, output_template="%(title)s.%(ext)s", format_choice="best"):
    """
    Download a video/audio using yt-dlp.
    - url: video URL (string)
    - audio_only: if True, extract audio (mp3/m4a) instead of video
    - output_template: output filename template
    - format_choice: yt-dlp format selector (e.g. 'bestvideo[ext=mp4]+bestaudio/best' or 'bestaudio')
    """
    ydl_opts = {
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': False,
        'no_warnings': True,
    }

    if audio_only:
        # extract audio and convert to mp3 if possible (ffmpeg required for conversion)
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # default: download best available video+audio mp4 if possible
        # you can change format_choice to suit your needs
        ydl_opts.update({'format': format_choice})

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info

def main():
    print("Simple YouTube downloader (yt-dlp)\n")
    url = input("Paste the YouTube video URL (or leave empty to exit): ").strip()
    if not url:
        print("No URL provided. Exiting.")
        return

    # Ask user preferences
    mode = input("Download (v)ideo or (a)udio only? [v/a] (default v): ").strip().lower()
    audio_only = (mode == 'a')

    # Optional: let user choose quality preset
    if not audio_only:
        print("\nQuality presets:")
        print("  1) Best compatible mp4 (video+audio if possible)")
        print("  2) Best video (may be separate streams)")
        print("  3) Best overall (default)")
        choice = input("Choose quality [1/2/3] (default 1): ").strip()
        if choice == '2':
            fmt = "bestvideo+bestaudio/best"
        elif choice == '3':
            fmt = "best"
        else:
            # try for mp4 compatible first
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    else:
        fmt = "bestaudio"

    # Output filename template (safe default)
    out_template = "%(title)s - %(id)s.%(ext)s"

    print("\nStarting download... (this may take a while depending on video size and connection)\n")
    try:
        info = download(url, audio_only=audio_only, output_template=out_template, format_choice=fmt)
        title = info.get('title') if isinstance(info, dict) else str(info)
        print("\nDownload finished. Title:", title)
        print("Saved as according to template:", out_template)
    except Exception as ex:
        print("Download failed:", ex)

    # Wait for Enter before exit so double-click runs are readable
    try:
        input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
