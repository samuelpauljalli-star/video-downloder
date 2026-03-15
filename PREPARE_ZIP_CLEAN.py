import os
import zipfile
import shutil

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ZIP_NAME = "StreamGlide_Media_Downloader_Portable.zip"

FILES_TO_INCLUDE = [
    "app.py",
    "index.html",
    "yt-dlp.exe",
    "python-3.13.12-amd64.exe",
    "python-3.13.12-amd64 (1).exe",
    "requirements.txt",
    "START_ENGINE.bat"
]

FOLDERS_TO_INCLUDE = [
    "downloads",
]

# Create any missing folders
for folder in FOLDERS_TO_INCLUDE:
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def main():
    print("======================================================")
    print("   PACKAGING STREAMGLIDE AI PORTABLE VERSION")
    print("======================================================\n")

    # Double check tools are present
    missing = [f for f in FILES_TO_INCLUDE if not os.path.exists(os.path.join(BASE_DIR, f))]
    if missing:
        print("⚠️ Warning: The following files are missing and won't be in the zip:")
        for m in missing:
            print(f" - {m}")
        print()

    # 3. Create Zip
    zip_path = os.path.join(BASE_DIR, ZIP_NAME)
    print(f"📦 Creating {ZIP_NAME}...\n")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add required files
        for file in FILES_TO_INCLUDE:
            file_path = os.path.join(BASE_DIR, file)
            if os.path.exists(file_path):
                zipf.write(file_path, file)
                print(f"✅ Added file: {file}")
        
        # Add required folders
        for folder in FOLDERS_TO_INCLUDE:
            folder_path = os.path.join(BASE_DIR, folder)
            if os.path.exists(folder_path):
                # add empty folder itself
                zipf.write(folder_path, folder)
                print(f"✅ Added folder: {folder}/")

    print("\n" + "="*50)
    print(f"✨ PORTABLE PACKAGE READY: {ZIP_NAME}")
    print("   Transfer this zip to another laptop, extract it, ")
    print("   and run START_ENGINE.bat to set up automatically!")
    print("="*50)

if __name__ == "__main__":
    main()
