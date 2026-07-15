import streamlit as st
import os
import yt_dlp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Target Google Drive Folder ID
FOLDER_ID = "1irOJjYYCQPFDRWaEXjfl052d-Rpa2kGf"

# --- Custom Logger to catch hidden errors ---
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
        
        with st.spinner("Solving JavaScript ciphers and downloading..."):
            try:
                # 1. Write cookies text from secrets to a temporary runtime file
                if "youtube_cookies" in st.secrets:
                    with open(COOKIE_PATH, "w", encoding="utf-8") as f:
                        f.write(st.secrets["youtube_cookies"])

                # 2. Configure Web-Only parameters to accept cookies and utilize Node.js
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                    'outtmpl': 'cloud_target.%(ext)s',
                    'noplaylist': True,
                    'merge_output_format': 'mp4',
                    'logger': yt_logger,
                    'extractor_args': {
                        'youtube': {
                            # Must use web clients because mobile clients reject cookies entirely
                            'player_client': ['web', 'mweb'] 
                        }
                    },
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Origin': 'https://www.youtube.com',
                        'Referer': 'https://www.youtube.com/',
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
                st.warning("🔍 **Diagnostic Logs:**")
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
