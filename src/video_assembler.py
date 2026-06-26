"""
video_assembler.py
FFmpeg ka use karke final video banata hai:
- stock/tool clips ko concat + crop/scale karta hai (vertical 1080x1920)
- voiceover audio attach karta hai
- .srt captions burn-in karta hai (subtitles filter)
"""
import os
import subprocess


class VideoAssembler:
    def __init__(self, resolution=(1080, 1920), fps=30):
        self.width, self.height = resolution
        self.fps = fps

    def _normalize_clip(self, input_path: str, output_path: str, duration: float):
        """Har clip ko same resolution/fps par crop-to-fill karta hai."""
        vf = (
            f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
            f"crop={self.width}:{self.height},fps={self.fps}"
        )
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path, "-t", str(duration),
            "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            output_path,
        ], check=True)
        return output_path

    def concat_clips(self, clip_paths: list, total_duration: float, tmp_dir: str = "output/_tmp") -> str:
        os.makedirs(tmp_dir, exist_ok=True)
        per_clip_duration = max(2.0, total_duration / max(1, len(clip_paths)))

        normalized = []
        for i, clip in enumerate(clip_paths):
            out = os.path.join(tmp_dir, f"norm_{i}.mp4")
            self._normalize_clip(clip, out, per_clip_duration)
            normalized.append(out)

        list_file = os.path.join(tmp_dir, "concat_list.txt")
        with open(list_file, "w") as f:
            for n in normalized:
                f.write(f"file '{os.path.abspath(n)}'\n")

        concatenated = os.path.join(tmp_dir, "concatenated.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
            "-c", "copy", concatenated,
        ], check=True)
        return concatenated

    def attach_audio(self, video_path: str, audio_path: str, output_path: str):
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            output_path,
        ], check=True)
        return output_path

    def burn_captions(self, video_path: str, srt_path: str, output_path: str,
                       font_size: int = 64, font_color: str = "white"):
        # FFmpeg subtitles filter (libass) - Urdu text ke liye RTL-friendly font zaroori hai
        style = (
            f"FontName=Jameel Noori Nastaleeq,FontSize={font_size},"
            f"PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,"
            f"BorderStyle=3,Outline=2,Alignment=2,MarginV=120"
        )
        subs_filter = f"subtitles={srt_path}:force_style='{style}'"
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vf", subs_filter,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            output_path,
        ], check=True)
        return output_path

    def assemble(self, clip_paths: list, audio_path: str, srt_path: str,
                 audio_duration: float, output_path: str = "output/final_video.mp4"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        concatenated = self.concat_clips(clip_paths, audio_duration)
        with_audio = concatenated.replace(".mp4", "_with_audio.mp4")
        self.attach_audio(concatenated, audio_path, with_audio)
        self.burn_captions(with_audio, srt_path, output_path)
        return output_path
