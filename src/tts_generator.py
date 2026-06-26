"""
tts_generator.py
gTTS (Google Text-to-Speech) se Urdu/Roman Urdu voice generate karta hai 
aur subtitles/captions ke liye fallback word boundaries banata hai.
"""
import os
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)


class TTSGenerator:
    def __init__(self, voice: str = "default", rate: str = "+0%", pitch: str = "+0Hz"):
        """Initialize TTS Generator with gTTS"""
        # Note: gTTS abstracts direct voice names, using accent-based generation
        self.rate = rate
        self.pitch = pitch
        logger.info("✅ TTSGenerator initialized using gTTS (Google)")
    
    def generate(self, text: str, output_path: str = "output/voice.mp3") -> list:
        """Generate TTS and return word boundaries"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # lang='hi' (Hindi) is used here because it perfectly reads Roman Urdu/Hindi 
            # scripts without switching to a foreign English accent.
            tts = gTTS(text=text, lang='hi', slow=False)
            tts.save(output_path)
            
            # Generate fallback boundaries since gTTS doesn't stream word timestamps natively
            word_boundaries = self._create_fallback_boundaries(text)
            
            logger.info(f"✅ TTS generated successfully: {output_path} ({len(word_boundaries)} words)")
            return word_boundaries
            
        except Exception as e:
            logger.error(f"❌ gTTS generation failed: {e}")
            # Create fallback boundaries in case of complete failure
            return self._create_fallback_boundaries(text)
    
    def _create_fallback_boundaries(self, text: str) -> list:
        """Create fallback word boundaries based on word count"""
        words = text.split()
        # Roughly estimate 0.25 seconds per word for smooth caption pacing
        duration_per_word = 0.25
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
