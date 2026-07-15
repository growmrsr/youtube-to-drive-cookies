import streamlit as st
import os
import yt_dlp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Target Google Drive Folder ID
FOLDER_ID = "1irOJjYYCQPFDRWaEXjfl052d-Rpa2kGf"

# --- Custom X-Ray Logger to catch hidden YouTube blocks ---
class MyLogger(object):
    def __init__(self):
        self.logs = []
    def debug(self, msg):
        pass
    def warning(self, msg):
        self.logs.append(msg)
    def error(self, msg):
        self.logs.append(msg)

def get_drive_service():
    """Authenticates with Google Drive using secrets."""
    oauth_info = st.secrets["gcp_oauth"]
    creds = Credentials(
        token=None,
        refresh_token=oauth_info["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=oauth_info["client_id"],
        client_secret=oauth_info["client_secret"]
    )
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(file_path, file_name):
    """Uploads the downloaded file to the specified Google Drive folder."""
    service = get_drive_service()
    file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

# --- Streamlit UI Layout ---
st.set_page_config(page_title="Cookie Downloader", page_icon="🍪", layout="centered")

st.title("🍪 Dedicated Cookie Downloader")
st.write("Logged-in cloud pipeline. Paste a YouTube link to upload it directly to Google Drive.")

if "youtube_cookies" not in st.secrets:
    st.warning("⚠️ YouTube cookies are missing from your Streamlit Secrets configuration.")

video_url = st.text_input("Enter YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🚀 Run Cloud Download", use_container_width=True):
    if video_url:
        COOKIE_PATH = "runtime_cookies.txt"
        yt_logger = MyLogger()
        
        with st.spinner("Authenticating and running deep diagnostics..."):
            try:
                # 1. Write cookies text from secrets to a temporary runtime file
                if "youtube_cookies" in st.secrets:
                    with open(COOKIE_PATH, "w", encoding="utf-8") as f:
                        f.write(st.secrets["youtube_cookies"])

                # 2. Configure Diagnostic parameters
                ydl_opts = {
                    'format': 'best',             # Forces a pre-merged file to rule out FFmpeg issues completely
                    'outtmpl': 'cloud_target.%(ext)s',
                    'noplaylist': True,
                    'geo_bypass': True,           # Attempts to fix the Cookie Timezone vs Server IP location mismatch
                    'logger': yt_logger,          # Catches the hidden YouTube security warnings
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['web', 'android', 'ios'] 
                        }
                    }
                }
                
                if os.path.exists(COOKIE_PATH):
                    ydl_opts['cookiefile'] = COOKIE_PATH
                
                # 3. Extract and Download from YouTube
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=True)
                    video_title = info_dict.get('title', 'Video')
                    ext = info_dict.get('ext', 'mp4')
                    
                    downloaded_file = f"cloud_target.{ext}"
                    clean_name = f"{video_title}.{ext}".replace("/", "_").replace("\\", "_")
                
                # 4. Seamlessly push to Google Drive and clear server storage
                if os.path.exists(downloaded_file):
                    st.info("⚡ File pulled successfully. Transporting to Google Drive...")
                    upload_to_drive(downloaded_file, clean_name)
                    os.remove(downloaded_file)
                    st.success(f"🎉 Success! '{clean_name}' is safely inside your Drive folder.")
                else:
                    st.error("Error: Downloaded asset file could not be verified on the server.")
                    
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")
                # This will print the secret YouTube warnings on the screen!
                st.warning("🔍 **Deep Diagnostic Logs Found:**")
                for log in yt_logger.logs:
                    st.code(log)
            finally:
                # Clean up cookie footprints from the container runtime
                if os.path.exists(COOKIE_PATH):
                    try:
                        os.remove(COOKIE_PATH)
                    except:
                        pass
    else:
        st.warning("Please input a valid URL first.")
