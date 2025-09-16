from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import subprocess
import uuid

app = Flask(__name__)

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def download_tiktok(url, format_choice, upscale=False):
    file_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOADS_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestaudio/best' if format_choice == 'mp3' else 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4' if format_choice != 'mp3' else 'mp3'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded_file = ydl.prepare_filename(info)

    # Convert to MP3 if requested
    if format_choice == "mp3":
        mp3_path = downloaded_file.replace(".mp4", ".mp3")
        subprocess.run([
            "ffmpeg", "-y", "-i", downloaded_file, "-vn", "-ab", "192k", mp3_path
        ])
        os.remove(downloaded_file)
        return mp3_path

    # HD upscale
    if upscale and format_choice in ["mp4", "mp4hd"]:
        upscaled_path = downloaded_file.replace(".mp4", "_upscaled.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-i", downloaded_file,
            "-vf", "scale=1920:1080:flags=lanczos",
            upscaled_path
        ])
        return upscaled_path

    return downloaded_file


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    format_choice = request.form.get("format")
    upscale = request.form.get("upscale") == "true"

    try:
        file_path = download_tiktok(url, format_choice, upscale)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
