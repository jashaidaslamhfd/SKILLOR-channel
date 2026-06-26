"""
thumbnail_generator.py
Generate professional thumbnails for SKILLOR videos
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import random
import logging

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    def __init__(self):
        self.width = 1280
        self.height = 720
        self.colors = [
            (26, 26, 46),  # Dark blue
            (15, 15, 35),  # Darker
            (40, 20, 60),  # Purple
            (20, 40, 60),  # Teal
        ]
        logger.info("✅ ThumbnailGenerator initialized")
    
    def generate(self, title: str, tool_screenshot_path: str = None, 
                 output_path: str = "output/thumbnail.jpg") -> str:
        """Generate thumbnail with title overlay"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create gradient background
        bg_color = random.choice(self.colors)
        img = Image.new('RGB', (self.width, self.height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Gradient effect
        for i in range(self.height):
            r = int(bg_color[0] + (80 * i / self.height))
            g = int(bg_color[1] + (40 * i / self.height))
            b = int(bg_color[2] + (80 * i / self.height))
            draw.rectangle([(0, i), (self.width, i+1)], fill=(r, g, b))
        
        # Add tool screenshot if available
        if tool_screenshot_path and os.path.exists(tool_screenshot_path):
            try:
                tool_img = Image.open(tool_screenshot_path)
                tool_img = tool_img.resize((700, 400), Image.Resampling.LANCZOS)
                img.paste(tool_img, (290, 100))
            except Exception as e:
                logger.warning(f"Could not paste screenshot: {e}")
        
        # Load fonts (fallback if not available)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 50)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 45)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 50)
                title_font = ImageFont.truetype("arial.ttf", 45)
            except:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
        
        # SKILLOR logo
        draw.text((40, 40), "SKILLOR", fill=(255, 200, 0), font=font)
        
        # Add title (wrapped)
        wrapped = textwrap.wrap(title, width=35)
        y = 480
        for line in wrapped[:3]:
            # Shadow
            draw.text((42, y+2), line, fill=(0, 0, 0), font=title_font)
            draw.text((40, y), line, fill=(255, 255, 255), font=title_font)
            y += 55
        
        # Watch Now button
        draw.rounded_rectangle([(40, y+20), (280, y+80)], radius=15, fill=(255, 200, 0))
        draw.text((70, y+30), "▶️ Watch Now", fill=(0, 0, 0), font=font)
        
        # Add subtle border
        draw.rectangle([(0, 0), (self.width-1, self.height-1)], outline=(255, 200, 0), width=3)
        
        img.save(output_path, "JPEG", quality=95)
        logger.info(f"✅ Thumbnail saved: {output_path}")
        return output_path


if __name__ == "__main__":
    gen = ThumbnailGenerator()
    gen.generate("ChatGPT ka naya feature 2026", output_path="test_thumbnail.jpg")
