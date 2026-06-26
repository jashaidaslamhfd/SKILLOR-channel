"""
tts_generator.py
Edge TTS se Urdu voice generate karta hai aur word-level timing boundaries bhi save karta hai
(caption sync ke liye zaroori).
"""
import asyncio
import edge_tts


class TTSGenerator:
    def __init__(self, voice: str = "ur-PK-AsadNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    async def _generate_async(self, text: str, output_path: str):
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
        word_boundaries = []

        with open(output_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    word_boundaries.append({
                        "text": chunk["text"],
                        "start": chunk["offset"] / 10_000_000,          # 100-ns units -> seconds
                        "duration": chunk["duration"] / 10_000_000,
                    })
        return word_boundaries

    def generate(self, text: str, output_path: str = "output/voice.mp3"):
        """
        Returns: list of word boundary dicts -> [{text, start, duration}, ...]
        """
        word_boundaries = asyncio.run(self._generate_async(text, output_path))
        return word_boundaries


if __name__ == "__main__":
    tts = TTSGenerator()
    boundaries = tts.generate(
        "Salam dosto! Aaj hum baat karein ge ChatGPT k ek naye feature ke baare mein.",
        "output/voice_test.mp3",
    )
    for b in boundaries[:5]:
        print(b)
