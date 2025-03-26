#!/usr/bin/env python
# Direct Clock Example - Uses direct display instead of threading
import time
import sys
from datetime import datetime
from samplebase import SampleBase
from PIL import Image, ImageDraw, ImageFont
import os

class ClockDisplay(SampleBase):
    def __init__(self, *args, **kwargs):
        super(ClockDisplay, self).__init__(*args, **kwargs)
    
    def run(self):
        # Create a canvas to draw on
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        
        # Try to load a font
        font = None
        font_size = 14
        try:
            # Try to find a font that exists
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
                '/Library/Fonts/Arial.ttf',  # macOS
                'C:\\Windows\\Fonts\\arial.ttf',  # Windows
                'fonts/FreeSans.ttf',  # Local directory
            ]
            for path in font_paths:
                if os.path.exists(path):
                    print(f"Loading font: {path}")
                    font = ImageFont.truetype(path, font_size)
                    break
        except Exception as e:
            print(f"Error loading font: {e}")
            
        if font is None:
            print("Using default font")
            font = ImageFont.load_default()
        
        print("Starting clock display loop...")
        try:
            while True:
                # Get current time
                now = datetime.now()
                time_str = now.strftime("%H:%M:%S")
                print(f"Current time: {time_str}")
                
                # Create a new image for the time
                width, height = self.matrix.width, self.matrix.height
                image = Image.new('RGB', (width, height), (0, 0, 0))
                draw = ImageDraw.Draw(image)
                
                # Calculate text position
                text_bbox = draw.textbbox((0, 0), time_str, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                position = ((width - text_width) // 2, (height - text_height) // 2)
                
                # Draw text
                draw.text(position, time_str, font=font, fill=(0, 191, 255))
                
                # Copy to canvas and update display
                offscreen_canvas.SetImage(image.convert('RGB'))
                offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
                
                # Wait before updating again
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("Interrupted by user")

# Main function
if __name__ == "__main__":
    clock = ClockDisplay()
    if not clock.process():
        clock.print_help()
    else:
        clock.run()