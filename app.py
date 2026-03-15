import os
import logging
import subprocess
import yt_dlp
import json
import webbrowser
import tkinter as tk
from tkinter import filedialog
from threading import Timer
from typing import Any
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SAVE_PATH = os.path.join(BASE_DIR, 'downloads')
if not os.path.exists(DEFAULT_SAVE_PATH):
    os.makedirs(DEFAULT_SAVE_PATH)

YT_DLP_EXE = os.path.join(BASE_DIR, 'yt-dlp.exe') if os.name == 'nt' else None

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("StreamGlide")

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

HAS_FFMPEG = check_ffmpeg()

# --- DOWNLOADING LOGIC ---

def get_video_info(url):
    ydl_opts: dict[str, Any] = {
        'quiet': True, 
        'noplaylist': True,
        'no_warnings': True,
        'format': 'best', # Ensure we can find basic info
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise Exception("Could not extract video information. Please check if the URL is valid.")
            
            return {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': f"{info.get('duration', 0) // 60}:{info.get('duration', 0) % 60:02d}",
                'url': url
            }
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise Exception(f"YT-DLP Error: {str(e)}")

def download_media(url, mode, quality, custom_path=None):
    save_path = custom_path if custom_path and os.path.exists(custom_path) else DEFAULT_SAVE_PATH
    
    ydl_opts: dict[str, Any] = {
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    if mode == 'audio':
        if HAS_FFMPEG:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
            })
        else:
            ydl_opts['format'] = 'bestaudio/best'
    else:
        if HAS_FFMPEG:
            # Try to get best video + best audio, or best single file
            ydl_opts['format'] = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]/best'
        else:
            # If no FFmpeg, we MUST get a single file (usually limited to 720p or 360p)
            ydl_opts['format'] = f'best[height<={quality}][ext=mp4]/best[ext=mp4]/best'

    logger.info(f"🚀 Starting {mode} download: {url} (Quality: {quality})")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Check if post-processor changed the name (e.g. to .mp3)
            if mode == 'audio' and HAS_FFMPEG:
                base = os.path.splitext(filename)[0]
                if os.path.exists(base + '.mp3'):
                    filename = base + '.mp3'
            
            # Handle cases where filename extension doesn't match info['ext']
            if not os.path.exists(filename):
                base = os.path.splitext(filename)[0]
                found = False
                for ext in ['mp4', 'mkv', 'webm', 'm4a', 'mp3', 'm4v']:
                    alt_path = f"{base}.{ext}"
                    if os.path.exists(alt_path):
                        filename = alt_path
                        found = True
                        break
                if not found:
                    raise Exception(f"Download finished but file not found: {filename}")
            
            logger.info(f"✅ Download complete: {filename}")
            return filename
    except Exception as e:
        logger.error(f"❌ Download failed: {str(e)}")
        raise e

# --- FLASK APP ---

app = Flask(__name__, template_folder='.')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:filename>')
def root_files(filename):
    if filename.endswith(('.exe', '.bat', '.txt')):
        return send_from_directory(BASE_DIR, filename)
    return "Not allowed", 403

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    if not url: return jsonify({'error': 'No URL'}), 400
    try:
        return jsonify(get_video_info(url))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/download', methods=['POST'])
def web_download():
    data = request.json
    mode = data.get('mode')
    quality = data.get('quality')
    url = data.get('url')
    custom_path = data.get('path')
    
    try:
        file_path = download_media(url, mode, quality, custom_path)
        # Store metadata for history if needed, but for now we just list the directory
        return jsonify({'status': 'success', 'file': os.path.basename(file_path), 'path': file_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    custom_path = request.args.get('path')
    target_path = custom_path if custom_path and os.path.exists(custom_path) else DEFAULT_SAVE_PATH
    
    files = []
    if os.path.exists(target_path):
        for f in os.listdir(target_path):
            full_p = os.path.join(target_path, f)
            if os.path.isfile(full_p):
                files.append({
                    'name': f,
                    'size': os.path.getsize(full_p),
                    'path': full_p
                })
    return jsonify(files)

@app.route('/api/serve/<path:filename>')
def serve_file(filename):
    custom_path = request.args.get('path')
    target_path = custom_path if custom_path and os.path.exists(custom_path) else DEFAULT_SAVE_PATH
    return send_from_directory(target_path, filename)

@app.route('/api/open_folder', methods=['POST'])
def open_folder():
    path = request.json.get('path', DEFAULT_SAVE_PATH)
    if os.path.exists(path):
        try:
            if os.name == 'nt':
                os.startfile(path) # Windows
            else:
                # Linux/Mac handles this differently or ignores for web
                return jsonify({'error': 'Folder opening is only supported on local Windows machines'}), 400
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Path not found'}), 404

@app.route('/api/pick_folder', methods=['POST'])
def pick_folder():
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askdirectory()
        root.destroy()
        return jsonify({'path': path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/env')
def get_env():
    return jsonify({
        'is_local': os.name == 'nt' or 'localhost' in request.host,
        'has_ffmpeg': HAS_FFMPEG,
        'os': os.name
    })

def open_browser():
    webbrowser.open_new("http://localhost:5000")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "="*50)
    print(f"🚀 StreamGlide Engine is starting...")
    print(f"🔗 Local URL: http://localhost:{port}")
    print("="*50)
    
    # Open browser after 1.5 seconds to ensure server is ready
    Timer(1.5, open_browser).start()
    
    app.run(port=port, host='0.0.0.0', debug=False)
