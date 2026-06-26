"""
video_assembler.py
FFmpeg se final video assemble karta hai
"""
import os
import subprocess
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoAssembler:
    def __init__(self, resolution=(1080, 1920), fps=30):
        """Initialize Video Assembler"""
        self.width, self.height = resolution
        self.fps = fps
        self.ffmpeg_path = self._find_ffmpeg()
        logger.info(f"✅ VideoAssembler initialized: {resolution}, {fps}fps")
    
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable"""
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("❌ FFmpeg not found! Please install FFmpeg.")
        return ffmpeg
    
    def _run_ffmpeg(self, args: list) -> bool:
        """Run FFmpeg command with error handling"""
        try:
            cmd = [self.ffmpeg_path] + args
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ FFmpeg error: {e.stderr}")
            return False
    
    def _normalize_clip(self, input_path: str, output_path: str, duration: float) -> str:
        """Normalize clip to target resolution and duration"""
        vf = (
            f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
            f"crop={self.width}:{self.height},"
            f"fps={self.fps}"
        )
        
        success = self._run_ffmpeg([
            "-y", "-i", input_path, "-t", str(duration),
            "-vf", vf, "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            output_path
        ])
        
        return output_path if success else None
    
    def concat_clips(self, clip_paths: list, total_duration: float, tmp_dir: str = "output/_tmp") -> str:
        """Concatenate multiple clips to fill total duration"""
        os.makedirs(tmp_dir, exist_ok=True)
        
        # Calculate per-clip duration
        per_clip_duration = max(2.0, total_duration / max(1, len(clip_paths)))
        
        # Normalize all clips
        normalized = []
        for i, clip in enumerate(clip_paths):
            out_path = os.path.join(tmp_dir, f"norm_{i}.mp4")
            result = self._normalize_clip(clip, out_path, per_clip_duration)
            if result:
                normalized.append(result)
        
        if not normalized:
            raise RuntimeError("No clips could be normalized!")
        
        # Create concat list
        list_file = os.path.join(tmp_dir, "concat_list.txt")
        with open(list_file, "w") as f:
            for n in normalized:
                f.write(f"file '{os.path.abspath(n)}'\n")
        
        # Concatenate
        output = os.path.join(tmp_dir, "concatenated.mp4")
        success = self._run_ffmpeg([
            "-y", "-f", "concat", "-safe", "0", "-i", list_file,
            "-c", "copy", output
        ])
        
        return output if success else None
    
    def attach_audio(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Attach audio to video"""
        success = self._run_ffmpeg([
            "-y", "-i", video_path, "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            output_path
        ])
        
        return output_path if success else None
    
    def burn_captions(self, video_path: str, srt_path: str, output_path: str,
                       font_size: int = 64, font_color: str = "white") -> str:
        """Burn captions into video"""
        # Style for Urdu captions
        style = (
            f"FontName=Jameel Noori Nastaleeq,FontSize={font_size},"
            f"PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,"
            f"BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=120"
        )
        
        subs_filter = f"subtitles={srt_path}:force_style='{style}'"
        
        success = self._run_ffmpeg([
            "-y", "-i", video_path,
            "-vf", subs_filter,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            output_path
        ])
        
        return output_path if success else None
    
    def assemble(self, clip_paths: list, audio_path: str, srt_path: str,
                 audio_duration: float, output_path: str = "output/final_video.mp4") -> str:
        """Complete video assembly pipeline"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        logger.info(f"Assembling video: {len(clip_paths)} clips, {audio_duration}s duration")
        
        # Concatenate clips
        concatenated = self.concat_clips(clip_paths, audio_duration)
        if not concatenated:
            raise RuntimeError("Failed to concatenate clips!")
        
        # Add audio
        with_audio = concatenated.replace(".mp4", "_with_audio.mp4")
        result = self.attach_audio(concatenated, audio_path, with_audio)
        if not result:
            raise RuntimeError("Failed to attach audio!")
        
        # Burn captions
        result = self.burn_captions(with_audio, srt_path, output_path)
        if not result:
            raise RuntimeError("Failed to burn captions!")
        
        logger.info(f"✅ Video assembled: {output_path}")
        return output_path


if __name__ == "__main__":
    # Test video assembler
    assembler = VideoAssembler()
    print("VideoAssembler ready")
