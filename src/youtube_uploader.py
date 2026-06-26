"""
youtube_uploader.py
YouTube Data API v3 se video upload karta hai (Official API)
"""
import os
import pickle
import json
import logging
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:
    def __init__(self, client_secret_file: str = "config/client_secret.json",
                 token_file: str = "config/youtube_token.json"):
        """Initialize YouTube Uploader with OAuth credentials"""
        self.client_secret_file = client_secret_file
        self.token_file = token_file
        self.youtube = self._authenticate()
        logger.info("✅ YouTubeUploader initialized")
    
    def _authenticate(self):
        """Authenticate with YouTube API"""
        creds = None
        
        # Check if token file exists
        if os.path.exists(self.token_file):
            try:
                # Try to load as pickle
                with open(self.token_file, "rb") as f:
                    creds = pickle.load(f)
                logger.info("✅ Credentials loaded from pickle")
            except:
                try:
                    # Try to load as JSON
                    with open(self.token_file, "r") as f:
                        creds_data = json.load(f)
                        creds = Credentials.from_authorized_user_info(creds_data)
                    logger.info("✅ Credentials loaded from JSON")
                except Exception as e:
                    logger.warning(f"Could not load credentials: {e}")
                    creds = None
        
        # If credentials are invalid or expired, refresh or get new
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                logger.info("Getting new credentials...")
                if not os.path.exists(self.client_secret_file):
                    raise FileNotFoundError(
                        f"❌ Client secret file not found: {self.client_secret_file}\n"
                        "Download from Google Cloud Console -> APIs & Services -> Credentials"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("✅ New credentials obtained")
            
            # Save credentials
            try:
                with open(self.token_file, "wb") as f:
                    pickle.dump(creds, f)
                logger.info(f"✅ Credentials saved to {self.token_file}")
            except:
                # Fallback to JSON
                with open(self.token_file, "w") as f:
                    creds_dict = {
                        "token": creds.token,
                        "refresh_token": creds.refresh_token,
                        "token_uri": creds.token_uri,
                        "client_id": creds.client_id,
                        "client_secret": creds.client_secret,
                        "scopes": creds.scopes
                    }
                    json.dump(creds_dict, f)
                logger.info(f"✅ Credentials saved to {self.token_file} (JSON)")
        
        # Build YouTube service
        return build("youtube", "v3", credentials=creds)
    
    def upload(self, video_path: str, title: str, description: str,
               tags: list = None, category_id: str = "28", 
               privacy: str = "public", thumbnail_path: str = None) -> str:
        """
        Upload video to YouTube
        
        Args:
            video_path: Path to video file
            title: Video title (max 100 chars)
            description: Video description
            tags: List of tags
            category_id: YouTube category ID (28 = Science & Technology)
            privacy: public, unlisted, private
            thumbnail_path: Path to thumbnail image
        
        Returns:
            Video ID
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"❌ Video not found: {video_path}")
        
        # Prepare body
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or ["SKILLOR", "AI Tools", "Tech", "Urdu"],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }
        
        logger.info(f"📤 Uploading video: {title[:50]}...")
        logger.info(f"   Privacy: {privacy}")
        logger.info(f"   Category: {category_id}")
        
        # Upload video
        media = MediaFileUpload(
            video_path, 
            chunksize=-1,  # Auto chunks
            resumable=True,
            mimetype="video/mp4"
        )
        
        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        # Execute upload with progress
        response = None
        try:
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"   Upload progress: {progress}%", end="\r")
            
            print()  # New line after progress
            video_id = response["id"]
            logger.info(f"✅ Video uploaded! Video ID: {video_id}")
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            raise
        
        # Upload thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                logger.info("📸 Uploading thumbnail...")
                self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                logger.info("✅ Thumbnail uploaded!")
            except Exception as e:
                logger.warning(f"⚠️ Thumbnail upload failed: {e}")
        
        return video_id
    
    def update_video_details(self, video_id: str, title: str = None, 
                            description: str = None, tags: list = None):
        """Update video metadata"""
        body = {}
        
        if title or description or tags:
            body["snippet"] = {}
            if title:
                body["snippet"]["title"] = title[:100]
            if description:
                body["snippet"]["description"] = description[:5000]
            if tags:
                body["snippet"]["tags"] = tags
        
        if body:
            body["id"] = video_id
            self.youtube.videos().update(
                part="snippet",
                body=body
            ).execute()
            logger.info(f"✅ Video details updated: {video_id}")
    
    def get_video_status(self, video_id: str) -> dict:
        """Get video status and details"""
        response = self.youtube.videos().list(
            part="snippet,status",
            id=video_id
        ).execute()
        
        if response.get("items"):
            return response["items"][0]
        return None


if __name__ == "__main__":
    # Test YouTube uploader
    from dotenv import load_dotenv
    load_dotenv("config/.env")
    
    uploader = YouTubeUploader()
    print("✅ YouTubeUploader ready")
    print(f"   Client secret: {uploader.client_secret_file}")
    print(f"   Token file: {uploader.token_file}")
