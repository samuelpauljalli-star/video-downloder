import os
import urllib.request
import zipfile
import shutil

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ZIP_NAME = "StreamGlide_Media_Downloader_Portable.zip"

TOOLS = {
    "yt-dlp.exe": "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
    "python-3.13.2-amd64.exe": "https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"
}

# Useless files/folders to exclude from zip
EXCLUDE = {
    ".git", "__pycache__", ".venv", ".node-version", ".npm-version", 
    ".pip-version", ".python-version", "Procfile", "package.json", 
    "installed-packages.txt", ZIP_NAME, "PREPARE_ZIP.py"
}

def download_file(url, filename):
    print(f"🚀 Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, os.path.join(BASE_DIR, filename))
        print(f"✅ Success: {filename}")
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")

def main():
    print("======================================================")
    print("   STREAMGLIDE AI - PORTABLE PACKAGE PREPARER")
    print("======================================================\n")

    # 1. Download Tools
    # Download yt-dlp first
    download_file(TOOLS["yt-dlp.exe"], "yt-dlp.exe")
    
    # Download Python installer after yt-dlp (as requested)
    download_file(TOOLS["python-3.13.2-amd64.exe"], "python-3.13.12-amd64.exe")
    
    # User also asked for a second one with (1)
    print("Creating copy for 'python-3.13.12-amd64 (1).exe'...")
    shutil.copy2(
        os.path.join(BASE_DIR, "python-3.13.12-amd64.exe"),
        os.path.join(BASE_DIR, "python-3.13.12-amd64 (1).exe")
    )

    # 2. Cleanup useless files in director (Double check)
    print("\n🧹 Cleaning up useless files...")
    for item in EXCLUDE:
        path = os.path.join(BASE_DIR, item)
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
            print(f"   Removed: {item}")

    # 3. Create Zip
    print(f"\n📦 Creating {ZIP_NAME}...")
    with zipfile.ZipFile(os.path.join(BASE_DIR, ZIP_NAME), 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE]
            
            for file in files:
                if file not in EXCLUDE:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, BASE_DIR)
                    zipf.write(file_path, arcname)
                    print(f"   Added: {arcname}")

    print("\n" + "="*50)
    print(f"✨ PORTABLE PACKAGE READY: {ZIP_NAME}")
    print("   Take this zip to another laptop, extract,")
    print("   install Python, and run START_ENGINE.bat!")
    print("="*50)

if __name__ == "__main__":
    main()
