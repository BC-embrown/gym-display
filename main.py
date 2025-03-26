#!/usr/bin/env python
# Display text on an RGB LED matrix with options for scrolling or static display
from samplebase import SampleBase
from rgbmatrix import graphics
import time
import os

class TextDisplay(SampleBase):
    def __init__(self, *args, **kwargs):
        super(TextDisplay, self).__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to display on the RGB LED panel", default="Hello world!")
        self.parser.add_argument("-m", "--mode", help="Display mode: 'scroll' or 'static'", default="scroll")
        self.parser.add_argument("-f", "--font", help="Font to use from the fonts directory", default="7x13.bdf")
        self.parser.add_argument("--color", help="Text color in R,G,B format (0-255)", default="255,255,0")
        self.parser.add_argument("--speed", help="Scroll speed (lower is faster)", default=0.05, type=float)
        
    def run(self):
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        
        # Fix font path to use local fonts directory
        font_path = os.path.join("fonts", self.args.font)
        try:
            font.LoadFont(font_path)
        except Exception as e:
            print(f"Error loading font: {e}")
            print(f"Trying alternate path...")
            # Fallback to another common location
            try:
                font.LoadFont(self.args.font)
            except Exception as e:
                print(f"Error loading font from alternate path: {e}")
                print("Available fonts should be in ./fonts/ directory with .bdf extension")
                return
        
        # Parse color
        try:
            r, g, b = map(int, self.args.color.split(','))
            text_color = graphics.Color(r, g, b)
        except:
            print("Color format should be R,G,B (e.g., 255,255,0 for yellow)")
            text_color = graphics.Color(255, 255, 0)  # Default to yellow
            
        my_text = self.args.text
        
        if self.args.mode.lower() == "scroll":
            self.scroll_text(offscreen_canvas, font, text_color, my_text)
        else:
            self.static_text(offscreen_canvas, font, text_color, my_text)
    
    def scroll_text(self, canvas, font, color, text):
        pos = canvas.width
        
        while True:
            canvas.Clear()
            length = graphics.DrawText(canvas, font, pos, 10, color, text)
            pos -= 1
            if (pos + length < 0):
                pos = canvas.width
                
            time.sleep(self.args.speed)
            canvas = self.matrix.SwapOnVSync(canvas)
    
    def static_text(self, canvas, font, color, text):
        canvas.Clear()
        
        # Try to find best font size and position to fit text
        # First measure the text with current font
        font_height = font.height
        text_width = 0
        for c in text:
            text_width += font.CharacterWidth(ord(c))
        
        # Calculate position to center the text
        x_pos = max(0, (canvas.width - text_width) // 2)
        y_pos = (canvas.height + font_height) // 2  # Vertical center
        
        # If text is too wide, we'll just start from left edge
        if text_width > canvas.width:
            x_pos = 0
            
        # Draw the text
        graphics.DrawText(canvas, font, x_pos, y_pos, color, text)
        
        # Update display
        canvas = self.matrix.SwapOnVSync(canvas)
        
        # Keep displaying until CTRL+C
        try:
            print("Press CTRL-C to stop.")
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            return

# Main function
if __name__ == "__main__":
    text_display = TextDisplay()
    if (not text_display.process()):
        text_display.print_help()