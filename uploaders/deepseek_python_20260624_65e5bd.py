"""
Instagram Reels Uploader - Production Grade
Features:
1. Connection pooling with Session
2. Smart HEAD/GET validation
3. Async support with aiohttp
4. Configurable polling from settings
5. Queue integration ready
6. Advanced error classification
7. Metrics collection
"""

import os
import time
import json
import asyncio
import logging
from typing import Dict, List, Optional, Union, Callable
from urllib.parse import urlparse
from datetime import datetime
from dataclasses import dataclass, field

import requests
from config.settings import API_KEYS, PLATFORM_CONFIG

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class UploadMetrics:
    """Track upload performance metrics"""
    attempts: int = 0
    retries: int = 0
    start_time: float = 0
    end_time: float = 0
    container_creation_time: float = 0
    poll_time: float = 0
    publish_time: float = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def total_duration(self) -> float:
        return self.end_time - self.start_time if self.end_time > 0 else 0


class InstagramUploader:
    def __init__(self):
        self.access_token = API_KEYS.INSTAGRAM_ACCESS_TOKEN
        self.ig_user_id = API_KEYS.INSTAGRAM_USER_ID
        
        # FIX: Version from settings with fallback
        self.api_version = getattr(PLATFORM_CONFIG, 'INSTAGRAM_API_VERSION', 'v19.0')
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        # FIX: Retry settings from config
        self.max_retries = getattr(PLATFORM_CONFIG, 'INSTAGRAM_MAX_RETRIES', 3)
        self.retry_delay = getattr(PLATFORM_CONFIG, 'INSTAGRAM_RETRY_DELAY', 5)
        self.max_delay = getattr(PLATFORM_CONFIG, 'INSTAGRAM_MAX_DELAY', 60)
        
        # FIX: Polling settings from config
        self.max_poll_attempts = getattr(PLATFORM_CONFIG, 'INSTAGRAM_MAX_POLL', 30)
        self.poll_interval = getattr(PLATFORM_CONFIG, 'INSTAGRAM_POLL_INTERVAL', 3)
        
        # FIX: Better headers with encoding
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Compatible; InstagramUploader/2.0)',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Accept': 'application/json',
        })
        
        # Queue support
        self._upload_queue = []
        self._is_processing = False

    # ============================================================
    # FIX 1: Better URL Validation
    # ============================================================
    def _is_valid_public_url(self, url: str, check_reachable: bool = True, 
                              max_redirects: int = 3) -> bool:
        """
        Validate URL with comprehensive checks
        
        Args:
            url: URL to validate
            check_reachable: If True, makes HEAD/GET request
            max_redirects: Maximum redirects to follow
        """
        if not url:
            return False
        
        # Basic format check
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Parse URL
        try:
            parsed = urlparse(url)
            if not parsed.netloc or not parsed.scheme:
                return False
        except Exception:
            return False
        
        # Reject internal/local URLs
        internal_domains = [
            'localhost', '127.0.0.1', '0.0.0.0',
            '::1', '10.', '172.16.', '192.168.'
        ]
        if any(parsed.netloc.startswith(domain) for domain in internal_domains):
            logger.warning(f"Rejected internal URL: {url[:50]}...")
            return False
        
        # Skip reachability check for speed
        if not check_reachable:
            return True
        
        # FIX: Multi-step URL validation
        try:
            # Step 1: Try HEAD request (fast)
            response = self.session.head(
                url,
                timeout=10,
                allow_redirects=True,
                verify=True
            )
            
            if 200 <= response.status_code < 400:
                return True
            
            # Step 2: Handle 403/405 with GET + Range
            if response.status_code in [403, 405]:
                response = self.session.get(
                    url,
                    headers={'Range': 'bytes=0-0'},
                    timeout=10,
                    allow_redirects=True,
                    stream=True
                )
                return response.status_code in [200, 206, 301, 302, 303, 307, 308]
            
            # Step 3: Handle redirects
            if response.status_code in [301, 302, 303, 307, 308]:
                # Follow redirect
                redirect_url = response.headers.get('Location')
                if redirect_url:
                    return self._is_valid_public_url(redirect_url, check_reachable=True)
            
            logger.warning(f"URL returned {response.status_code}: {url[:80]}...")
            return False
            
        except requests.exceptions.Timeout:
            logger.warning(f"URL timeout: {url[:80]}...")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning(f"URL connection failed: {url[:80]}...")
            return False
        except Exception as e:
            logger.warning(f"URL validation error: {e}")
            return False

    # ============================================================
    # FIX 2: Dynamic Request with Metrics
    # ============================================================
    def _rate_limited_request(
        self,
        url: str,
        data: Dict = None,
        method: str = 'POST',
        timeout: int = 120,
        headers: Dict = None,
        retry_on: List[int] = None
    ) -> Dict:
        """
        Make API request with rate limiting and retry logic
        
        Args:
            url: API endpoint
            data: Request data
            method: HTTP method
            timeout: Request timeout
            headers: Additional headers
            retry_on: List of status codes to retry
        """
        method = method.upper()
        retry_on = retry_on or [429, 500, 502, 503, 504]
        
        for attempt in range(self.max_retries):
            try:
                # Merge headers
                request_headers = self.session.headers.copy()
                if headers:
                    request_headers.update(headers)
                
                # FIX: Dynamic method handling
                if method == 'GET':
                    response = self.session.request(
                        method, url,
                        params=data,
                        headers=request_headers,
                        timeout=timeout
                    )
                else:
                    response = self.session.request(
                        method, url,
                        data=data,
                        headers=request_headers,
                        timeout=timeout
                    )
                
                # ============================================================
                # Advanced Error Classification
                # ============================================================
                
                # Rate limit
                if response.status_code == 429:
                    wait_time = min(self.max_delay, self.retry_delay * (2 ** attempt))
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                # Server errors
                if response.status_code in [500, 502, 503, 504]:
                    if response.status_code in retry_on:
                        wait_time = min(self.max_delay, self.retry_delay * (1.5 ** attempt))
                        logger.warning(f"Server error {response.status_code}, retrying...")
                        time.sleep(wait_time)
                        continue
                
                # OAuth errors
                if response.status_code == 400:
                    try:
                        error_data = response.json() if response.text else {}
                        error_type = error_data.get('error', {}).get('type', '')
                        if 'OAuthException' in error_type:
                            logger.error(f"OAuth error: {error_type}")
                            return {'error': 'OAuthException', 'details': error_data}
                    except:
                        pass
                
                # Empty response (204)
                if response.status_code == 204:
                    return {}
                
                response.raise_for_status()
                
                # Parse response
                if response.text and response.text.strip():
                    return response.json()
                return {}
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    time.sleep(wait_time)
                    continue
                return {'error': 'Request timeout'}
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    time.sleep(wait_time)
                    continue
                return {'error': str(e)}
        
        return {'error': 'Max retries exceeded'}

    # ============================================================
    # FIX 3: Async Support with aiohttp
    # ============================================================
    async def _async_rate_limited_request(
        self,
        url: str,
        data: Dict = None,
        method: str = 'POST',
        timeout: int = 120,
        headers: Dict = None
    ) -> Dict:
        """Async version for web frameworks"""
        try:
            import aiohttp
        except ImportError:
            logger.error("aiohttp not installed. Install with: pip install aiohttp")
            return {'error': 'aiohttp not installed'}
        
        method = method.upper()
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    if method == 'GET':
                        async with session.get(
                            url, 
                            params=data, 
                            headers=headers or {},
                            timeout=timeout_obj
                        ) as response:
                            if response.status == 429:
                                wait_time = min(self.max_delay, self.retry_delay * (2 ** attempt))
                                await asyncio.sleep(wait_time)
                                continue
                            return await response.json()
                    else:
                        async with session.post(
                            url,
                            data=data,
                            headers=headers or {},
                            timeout=timeout_obj
                        ) as response:
                            if response.status == 429:
                                wait_time = min(self.max_delay, self.retry_delay * (2 ** attempt))
                                await asyncio.sleep(wait_time)
                                continue
                            return await response.json()
                            
            except asyncio.TimeoutError:
                logger.warning(f"Async timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                return {'error': 'Timeout'}
            except Exception as e:
                logger.warning(f"Async error: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                return {'error': str(e)}
        
        return {'error': 'Max retries exceeded'}

    # ============================================================
    # FIX 4: Container Polling with Metrics
    # ============================================================
    def _poll_container_status(self, container_id: str) -> Dict:
        """Poll container status with metrics"""
        url = f"{self.base_url}/{container_id}"
        
        for attempt in range(self.max_poll_attempts):
            try:
                result = self._rate_limited_request(
                    url=url,
                    data={
                        'access_token': self.access_token,
                        'fields': 'status,error_message'
                    },
                    method='GET',
                    timeout=30
                )
                
                if 'error' in result:
                    if 'timeout' in str(result['error']).lower():
                        continue
                    return result
                
                status = result.get('status', '')
                error_msg = result.get('error_message', '')
                
                if status == 'FINISHED':
                    logger.info(f"Container {container_id} ready")
                    return {'status': 'ready', 'container_id': container_id}
                
                if status == 'ERROR':
                    logger.error(f"Container error: {error_msg}")
                    return {'status': 'error', 'error': error_msg}
                
                if status == 'EXPIRED':
                    logger.error(f"Container expired: {container_id}")
                    return {'status': 'error', 'error': 'Container expired'}
                
                # Still processing
                if attempt % 5 == 0:  # Log every 5th attempt
                    logger.info(f"Container {container_id}: {status} ({attempt + 1}/{self.max_poll_attempts})")
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.warning(f"Status poll error: {e}")
                time.sleep(self.poll_interval)
        
        return {'status': 'timeout', 'error': 'Container not ready after polling'}

    # ============================================================
    # FIX 5: Queue Support
    # ============================================================
    def add_to_queue(
        self,
        video_url: str,
        thumbnail_path: str,
        caption: str,
        hashtags: List[str],
        callback: Optional[Callable] = None
    ) -> str:
        """Add upload to queue for batch processing"""
        task_id = f"ig_{int(time.time())}_{len(self._upload_queue)}"
        
        task = {
            'id': task_id,
            'video_url': video_url,
            'thumbnail_path': thumbnail_path,
            'caption': caption,
            'hashtags': hashtags,
            'callback': callback,
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
        }
        
        self._upload_queue.append(task)
        logger.info(f"Task {task_id} added to queue (queue size: {len(self._upload_queue)})")
        
        return task_id

    def process_queue(self, batch_size: int = 3) -> List[Dict]:
        """Process upload queue in batches"""
        results = []
        
        if not self._upload_queue:
            logger.info("Queue is empty")
            return results
        
        if self._is_processing:
            logger.warning("Queue already being processed")
            return results
        
        self._is_processing = True
        
        try:
            # Process in batches
            while self._upload_queue:
                batch = self._upload_queue[:batch_size]
                self._upload_queue = self._upload_queue[batch_size:]
                
                for task in batch:
                    try:
                        logger.info(f"Processing {task['id']}...")
                        result = self.upload_reel(
                            video_url=task['video_url'],
                            thumbnail_path=task['thumbnail_path'],
                            caption=task['caption'],
                            hashtags=task['hashtags']
                        )
                        
                        task['status'] = 'completed' if 'url' in result else 'failed'
                        task['result'] = result
                        results.append(task)
                        
                        # Call callback if provided
                        if task.get('callback'):
                            try:
                                task['callback'](result)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                        
                    except Exception as e:
                        logger.error(f"Task {task['id']} failed: {e}")
                        task['status'] = 'failed'
                        task['error'] = str(e)
                        results.append(task)
                
                # Rate limit between batches
                if self._upload_queue:
                    time.sleep(self.retry_delay)
        
        finally:
            self._is_processing = False
        
        return results

    # ============================================================
    # Main Upload Methods
    # ============================================================
    def _create_media_container(
        self,
        video_url: str,
        caption: str,
        thumbnail_url: Optional[str] = None
    ) -> Dict:
        """Create media container with thumbnail support"""
        url = f"{self.base_url}/{self.ig_user_id}/media"
        
        data = {
            'access_token': self.access_token,
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': caption,
            'share_to_feed': 'true',
        }
        
        # Add thumbnail if available
        if thumbnail_url and self._is_valid_public_url(thumbnail_url, check_reachable=False):
            data['thumb_url'] = thumbnail_url
            logger.info(f"Thumbnail included: {thumbnail_url[:50]}...")
        
        logger.info("Creating media container...")
        result = self._rate_limited_request(url, data)
        
        if 'id' in result:
            container_id = result['id']
            logger.info(f"Container created: {container_id}")
            
            # Poll for status
            status_result = self._poll_container_status(container_id)
            if status_result.get('status') == 'ready':
                return {'id': container_id, 'status': 'ready'}
            else:
                return {'error': status_result.get('error', 'Container not ready')}
        
        return {'error': result.get('error', 'Container creation failed')}

    def _publish_container(self, container_id: str) -> Dict:
        """Publish container with retry"""
        url = f"{self.base_url}/{self.ig_user_id}/media_publish"
        data = {
            'access_token': self.access_token,
            'creation_id': container_id,
        }
        
        logger.info(f"Publishing container {container_id}...")
        result = self._rate_limited_request(url, data)
        
        if 'id' in result:
            return {
                'media_id': result['id'],
                'url': f"https://instagram.com/reel/{result['id']}",
                'status': 'published'
            }
        
        return {'error': result.get('error', 'Publish failed')}

    def _upload_thumbnail_to_cloudinary(self, thumbnail_path: str) -> Optional[str]:
        """Upload thumbnail to Cloudinary"""
        try:
            from core.cloud_uploader import CloudUploader
            uploader = CloudUploader()
            return uploader.upload_thumbnail(thumbnail_path)
        except Exception as e:
            logger.warning(f"Cloudinary thumbnail upload failed: {e}")
            return None

    def upload_reel(
        self,
        video_url: str,
        thumbnail_path: str,
        caption: str,
        hashtags: List[str]
    ) -> Dict:
        """
        Upload reel with full retry logic
        
        Args:
            video_url: PUBLIC URL of the video
            thumbnail_path: Local path to thumbnail
            caption: Video description
            hashtags: List of hashtags
        
        Returns:
            Dict with upload status
        """
        metrics = UploadMetrics()
        metrics.start_time = time.time()
        
        try:
            # ============================================================
            # VALIDATION
            # ============================================================
            
            if not self.ig_user_id:
                return {"error": "INSTAGRAM_USER_ID not set"}
            
            if not self.access_token:
                return {"error": "INSTAGRAM_ACCESS_TOKEN not set"}
            
            if not self._is_valid_public_url(video_url):
                return {
                    "error": "video_url must be a public http(s) URL. "
                             "Use Cloudinary or other CDN for hosting."
                }
            
            # Optimize caption
            optimized_caption = self.optimize_caption(caption, hashtags)
            logger.info(f"Caption length: {len(optimized_caption)} chars")
            
            # Upload thumbnail to Cloudinary
            thumbnail_url = None
            if thumbnail_path and os.path.exists(thumbnail_path):
                thumbnail_url = self._upload_thumbnail_to_cloudinary(thumbnail_path)
                if thumbnail_url:
                    logger.info(f"Thumbnail URL: {thumbnail_url[:60]}...")
                else:
                    logger.warning("No thumbnail URL available")
            
            # ============================================================
            # RETRY LOOP
            # ============================================================
            
            last_error = None
            for attempt in range(self.max_retries):
                metrics.attempts += 1
                logger.info(f"Attempt {attempt + 1}/{self.max_retries}")
                
                try:
                    # Step 1: Create media container
                    container_start = time.time()
                    container_result = self._create_media_container(
                        video_url=video_url,
                        caption=optimized_caption,
                        thumbnail_url=thumbnail_url
                    )
                    metrics.container_creation_time = time.time() - container_start
                    
                    if 'error' in container_result:
                        error_msg = container_result['error']
                        logger.warning(f"Container creation failed: {error_msg}")
                        
                        # Check if retryable
                        if any(k in str(error_msg).lower() for k in ['rate', 'limit', 'timeout']):
                            if attempt < self.max_retries - 1:
                                metrics.retries += 1
                                wait_time = min(self.max_delay, self.retry_delay * (2 ** attempt))
                                logger.info(f"Retrying in {wait_time}s...")
                                time.sleep(wait_time)
                                continue
                        elif 'video_url' in str(error_msg).lower():
                            return {'error': error_msg}
                        else:
                            if attempt < self.max_retries - 1:
                                metrics.retries += 1
                                time.sleep(self.retry_delay * (attempt + 1))
                                continue
                            return {'error': error_msg}
                    
                    container_id = container_result.get('id')
                    if not container_id:
                        return {'error': 'No container ID returned'}
                    
                    # Step 2: Publish container
                    publish_start = time.time()
                    publish_result = self._publish_container(container_id)
                    metrics.publish_time = time.time() - publish_start
                    
                    if 'error' in publish_result:
                        error_msg = publish_result['error']
                        logger.warning(f"Publish failed: {error_msg}")
                        
                        if attempt < self.max_retries - 1:
                            metrics.retries += 1
                            wait_time = min(self.max_delay, self.retry_delay * (attempt + 1))
                            logger.info(f"Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        return {'error': error_msg}
                    
                    # Success!
                    metrics.end_time = time.time()
                    logger.info(f"✅ Instagram Reel published in {metrics.total_duration:.1f}s!")
                    
                    return {
                        **publish_result,
                        'metrics': {
                            'attempts': metrics.attempts,
                            'retries': metrics.retries,
                            'duration': metrics.total_duration,
                            'container_time': metrics.container_creation_time,
                            'publish_time': metrics.publish_time,
                        }
                    }
                    
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Attempt {attempt + 1} error: {e}")
                    metrics.errors.append(str(e))
                    
                    if attempt < self.max_retries - 1:
                        metrics.retries += 1
                        wait_time = self.retry_delay * (attempt + 1)
                        logger.info(f"Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    continue
            
            metrics.end_time = time.time()
            return {
                'error': f"Failed after {self.max_retries} attempts",
                'last_error': last_error,
                'metrics': {
                    'attempts': metrics.attempts,
                    'retries': metrics.retries,
                    'duration': metrics.total_duration,
                    'errors': metrics.errors
                }
            }
            
        except Exception as e:
            metrics.end_time = time.time()
            return {
                'error': f"Upload failed: {str(e)}",
                'metrics': {
                    'attempts': metrics.attempts,
                    'duration': metrics.total_duration
                }
            }

    # ============================================================
    # Helper Methods
    # ============================================================
    
    def optimize_caption(self, caption: str, hashtags: List[str]) -> str:
        """Optimize caption for Instagram algorithm"""
        # Clean hashtags
        clean_tags = []
        for tag in hashtags[:5]:
            tag = tag.replace('#', '').replace(' ', '').strip()
            if tag and len(tag) > 1:
                clean_tags.append(f"#{tag}")
        
        # Structure caption
        caption_lines = [
            "🤯 " + caption[:100] + ("..." if len(caption) > 100 else ""),
            "",
            "Save this for later! 📌",
            "",
            ".",
            ".",
            ".",
        ]
        
        if clean_tags:
            caption_lines.append(" ".join(clean_tags))
        
        caption_lines.append("")
        caption_lines.append("Follow for more 👆")
        
        return "\n".join(caption_lines)

    def get_instagram_status(self) -> Dict:
        """Health check for Instagram credentials"""
        url = f"{self.base_url}/{self.ig_user_id}"
        data = {
            'access_token': self.access_token,
            'fields': 'id,username,media_count'
        }
        
        try:
            result = self._rate_limited_request(url, data, method='GET')
            
            if 'username' in result:
                return {
                    'status': 'ok',
                    'username': result.get('username'),
                    'media_count': result.get('media_count', 0)
                }
            elif 'error' in result:
                return {
                    'status': 'error',
                    'error': result.get('error'),
                    'details': result.get('details', '')
                }
            else:
                return {
                    'status': 'error',
                    'error': 'Unexpected response',
                    'details': str(result)[:200]
                }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_queue_status(self) -> Dict:
        """Get upload queue status"""
        return {
            'queue_size': len(self._upload_queue),
            'is_processing': self._is_processing,
            'tasks': [
                {
                    'id': t['id'],
                    'status': t['status'],
                    'created_at': t['created_at']
                }
                for t in self._upload_queue[:10]  # Show first 10
            ]
        }