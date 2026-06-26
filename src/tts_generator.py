"""
tts_generator.py
Edge TTS se Urdu voice generate karta hai aur word boundaries save karta hai
"""
import asyncio
import os
import logging
import edge_tts

logger = logging.getLogger(__name__)


class TTSGenerator:
    def __init__(self, voice: str = "ur-PK-AsadNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        """Initialize TTS Generator with Edge TTS"""
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        logger.info(f"✅ TTSGenerator initialized with voice: {voice}")
    
    async def _generate_async(self, text: str, output_path: str):
        """Generate TTS asynchronously and return word boundaries"""
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
        word_boundaries = []
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    word_boundaries.append({
                        "text": chunk["text"],
                        "start": chunk["offset"] / 10_000_000,  # Convert to seconds
                        "duration": chunk["duration"] / 10_000_000,
                    })
        
        return word_boundaries
    
    def generate(self, text: str, output_path: str = "output/voice.mp3") -> list:
        """Generate TTS and return word boundaries"""
        try:
            word_boundaries = asyncio.run(self._generate_async(text, output_path))
            
            if not word_boundaries:
                logger.warning("No word boundaries generated, creating fallback")
                word_boundaries = self._create_fallback_boundaries(text)
            
            logger.info(f"✅ TTS generated: {output_path} ({len(word_boundaries)} words)")
            return word_boundaries
            
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            # Create fallback boundaries
            return self._create_fallback_boundaries(text)
    
    def _create_fallback_boundaries(self, text: str) -> list:
        """Create fallback word boundaries if TTS fails"""
        words = text.split()
        duration_per_word = 0.3
        boundaries = []
        
        for i, word in enumerate(words):
            boundaries.append({
                "text": word,
                "start": i * duration_per_word,
                "duration": duration_per_word
            })
        
        return boundaries


if __name__ == "__main__":
    # Test TTS
    tts = TTSGenerator()
    boundaries = tts.generate(
        "Salam dosto! Aaj hum baat karein ge ChatGPT k ek naye feature ke baare mein.",
        "output/voice_test.mp3",
    )
    for b in boundaries[:5]:
        print(b)
