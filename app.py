import os
import logging
import subprocess
import yt_dlp
import json
from typing import Any
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SAVE_PATH = os.path.join(BASE_DIR, 'downloads')
if not os.path.exists(DEFAULT_SAVE_PATH):
    os.makedirs(DEFAULT_SAVE_PATH)

YT_DLP_EXE = os.path.join(BASE_DIR, 'yt-dlp.exe')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
        'extract_flat': True,
    }
    # Point to the local exe if it exists
    if os.path.exists(YT_DLP_EXE):
        ydl_opts['ffmpeg_location'] = os.getcwd() # Often ffmpeg is bundled or near it
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            'title': info.get('title', 'Unknown Title'),
            'thumbnail': info.get('thumbnail', ''),
            'duration': f"{info.get('duration', 0) // 60}:{info.get('duration', 0) % 60:02d}",
            'url': url
        }

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
            ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best/best[height<={quality}]'
        else:
            ydl_opts['format'] = f'best[height<={quality}]/best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
        # Check if post-processor changed the name (e.g. to .mp3)
        if mode == 'audio' and HAS_FFMPEG:
            base = os.path.splitext(filename)[0]
            if os.path.exists(base + '.mp3'):
                return base + '.mp3'
        
        # Handle cases where filename extension doesn't match info['ext']
        if not os.path.exists(filename):
            base = os.path.splitext(filename)[0]
            for ext in ['mp4', 'mkv', 'webm', 'm4a', 'mp3']:
                alt_path = f"{base}.{ext}"
                if os.path.exists(alt_path):
                    return alt_path
                    
        return filename

# --- FLASK APP ---

app = Flask(__name__, template_folder='.')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

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
            os.startfile(path) # Windows only
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Path not found'}), 404

@app.route('/api/download_engine')
def download_engine():
    if os.path.exists(YT_DLP_EXE):
        return send_file(YT_DLP_EXE, as_attachment=True)
    return jsonify({'error': 'Engine file not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Server running on http://localhost:{port}")
    app.run(port=port, host='0.0.0.0', debug=False)
