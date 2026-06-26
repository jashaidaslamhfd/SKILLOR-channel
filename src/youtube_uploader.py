"""
youtube_uploader.py
Official YouTube Data API v3 ke zariye video upload karta hai
(yeh Selenium se zyada reliable aur ToS-compliant hai).
"""
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:
    def __init__(self, client_secret_file: str = "config/client_secret.json",
                 token_file: str = "config/youtube_token.json"):
        self.client_secret_file = client_secret_file
        self.token_file = token_file
        self.youtube = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, "wb") as f:
                pickle.dump(creds, f)

        return build("youtube", "v3", credentials=creds)

    def upload(self, video_path: str, title: str, description: str,
               tags: list = None, category_id: str = "28", privacy: str = "public"):
        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags or ["AI", "Tech", "SKILLOR", "AI Tools", "Urdu"],
                "categoryId": category_id,
            },
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
        request = self.youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")

        print(f"✅ Uploaded! Video ID: {response['id']}")
        return response["id"]
