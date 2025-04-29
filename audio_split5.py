import streamlit as st
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime

# --- Folder paths ---
UPLOAD_DIR = "upload_audio"
OUTPUT_DIR = "split_my_audio"
ZIP_PATH = "split_audio_output.zip"

# --- Ensure clean state on each launch ---
def clear_folder(folder):
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)

clear_folder(UPLOAD_DIR)  # Requirement 12
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- UI Config ---
st.set_page_config(page_title="🎵 Audio Stem Splitter", layout="wide")
st.title("🎵 Demucs Audio Stem Splitter")

st.markdown("""
This tool allows you to:
- Upload an audio file (MP3, WAV, FLAC, etc.)
- Split it into **vocals, drums, bass, and other stems** using [Demucs](https://github.com/facebookresearch/demucs)
- Download the split stems as a ZIP
- Automatically clean up everything when done

**Just upload and click one button. We’ll handle the rest!**
""")

# --- Upload File ---
audio_file = st.file_uploader("📤 Upload your audio file", type=["mp3", "wav", "flac", "ogg", "m4a"])

if audio_file:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = Path(audio_file.name).suffix
    file_base = Path(audio_file.name).stem
    saved_filename = f"{timestamp}_{file_base}{file_ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(saved_path, "wb") as f:
        f.write(audio_file.read())

    file_size = os.path.getsize(saved_path) / (1024 * 1024)

    # --- Display uploaded file info ---
    st.success("✅ File uploaded successfully!")
    st.metric("📁 File Name", saved_filename)
    st.metric("💾 File Size", f"{file_size:.2f} MB")
    st.audio(saved_path)

    # --- Button: Split Audio ---
    if st.button("🔀 Split Audio"):
        st.info("Demucs is processing the file. Please wait...")

        with st.spinner("Splitting audio into stems..."):
            try:
                subprocess.run(
                    [
                        "python3", "-m", "demucs", "-n", "htdemucs",
                        "-o", OUTPUT_DIR, saved_path
                    ],
                    check=True, capture_output=True, text=True
                )
                st.success("✅ Audio successfully split!")

                # Locate output directory
                stem_folder = os.path.join(OUTPUT_DIR, "htdemucs", Path(saved_path).stem)
                if not os.path.exists(stem_folder):
                    st.error("❌ Couldn't locate split stems.")
                else:
                    # Zip the stems
                    with zipfile.ZipFile(ZIP_PATH, "w") as zipf:
                        for file in os.listdir(stem_folder):
                            full_path = os.path.join(stem_folder, file)
                            zipf.write(full_path, arcname=file)

                    # --- Download Button ---
                    with open(ZIP_PATH, "rb") as z:
                        st.download_button(
                            label="⬇️ Download Split Audio ZIP",
                            data=z,
                            file_name="split_audio_tracks.zip",
                            mime="application/zip"
                        )

                    st.balloons()
                    st.success("🎉 All audio files downloaded.")

                    # --- Final Cleanup ---
                    try:
                        clear_folder(UPLOAD_DIR)
                        clear_folder(OUTPUT_DIR)
                        if os.path.exists(ZIP_PATH):
                            os.remove(ZIP_PATH)
                        st.info("🧹 Cleanup completed. All files removed.")
                    except Exception as e:
                        st.warning(f"Cleanup encountered an issue: {e}")

            except subprocess.CalledProcessError as e:
                st.error("❌ Demucs splitting failed.")
                st.code(e.stderr or "No error message returned.")
