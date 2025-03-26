#!/usr/bin/env python
# Display text on an RGB LED matrix using PIL for text rendering
from samplebase import SampleBase
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
import textwrap
import time

class ImageTextDisplay(SampleBase):
    def __init__(self, *args, **kwargs):
        super(ImageTextDisplay, self).__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to display on the RGB LED panel", default="Hello world!")
        self.parser.add_argument("--mode", help="Display mode: 'scroll-h', 'scroll-up', 'scroll-down', 'random' or 'static'", default="static")
        self.parser.add_argument("--random-interval", help="Seconds between direction changes in random mode", default=5.0, type=float)
        self.parser.add_argument("--font-size", help="Font size to use", default=12, type=int)
        self.parser.add_argument("--color", help="Text color in R,G,B format (0-255)", default="255,255,0")
        self.parser.add_argument("--bg-color", help="Background color in R,G,B format (0-255)", default="0,0,0")
        self.parser.add_argument("--speed", help="Scroll speed (lower is faster)", default=0.03, type=float)
        self.parser.add_argument("--wrap", help="Number of characters per line (0 for auto)", default=0, type=int)
        self.parser.add_argument("--font", help="TrueType font file path", default=None)

    def create_text_image(self):
        width, height = self.matrix.width, self.matrix.height
        
        # Parse colors
        try:
            r, g, b = map(int, self.args.color.split(','))
            text_color = (r, g, b)
        except:
            print("Text color format should be R,G,B (e.g., 255,255,0 for yellow)")
            text_color = (255, 255, 0)  # Default to yellow
            
        try:
            r, g, b = map(int, self.args.bg_color.split(','))
            bg_color = (r, g, b)
        except:
            print("Background color format should be R,G,B (e.g., 0,0,0 for black)")
            bg_color = (0, 0, 0)  # Default to black
        
        # Create a blank image with background color
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # Try to use the specified font or fall back to default
        font = None
        try:
            if self.args.font:
                font = ImageFont.truetype(self.args.font, self.args.font_size)
            else:
                # Try to use a default system font
                font_paths = [
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
                    '/Library/Fonts/Arial.ttf',  # macOS
                    'C:\\Windows\\Fonts\\arial.ttf',  # Windows
                ]
                for path in font_paths:
                    if os.path.exists(path):
                        font = ImageFont.truetype(path, self.args.font_size)
                        break
        except Exception as e:
            print(f"Error loading font: {e}")
            print("Falling back to default font")
        
        if font is None:
            font = ImageFont.load_default()
        
        # Get text and determine wrapping
        text = self.args.text
        if self.args.wrap > 0:
            # Use specified wrap length
            wrapped_text = textwrap.fill(text, self.args.wrap)
        else:
            # Auto-wrap based on image width
            avg_char_width = draw.textlength("X", font=font)
            chars_per_line = max(1, int(width / avg_char_width))
            wrapped_text = textwrap.fill(text, chars_per_line)
        
        # Calculate text position to center it
        text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Center text position
        position = ((width - text_width) // 2, (height - text_height) // 2)
        
        # Draw the text
        draw.multiline_text(position, wrapped_text, font=font, fill=text_color, align="center")
        
        return image

    def run(self):
        # Generate the text image
        image = self.create_text_image()
        
        mode = self.args.mode.lower()
        if mode == "scroll-h" or mode == "scroll":
            self.scroll_horizontal(image)
        elif mode == "scroll-up":
            self.scroll_vertical(image, direction="up")
        elif mode == "scroll-down":
            self.scroll_vertical(image, direction="down")
        elif mode == "random":
            self.scroll_random(image)
        else:
            self.static_image(image)
    
    def scroll_horizontal(self, image, xpos_start=0):
        img_width, img_height = image.size
        double_buffer = self.matrix.CreateFrameCanvas()
        
        # Create an image that's wider for smooth scrolling
        if img_width < self.matrix.width:
            # If image is smaller than display, create space for scrolling
            scroll_image = Image.new('RGB', (self.matrix.width * 2, img_height), (0, 0, 0))
            scroll_image.paste(image, (0, 0))
            scroll_image.paste(image, (self.matrix.width, 0))
            img_width = scroll_image.width
            image = scroll_image
        
        # let's scroll
        xpos = xpos_start
        print("Press CTRL-C to stop.")
        try:
            while True:
                xpos += 1
                if xpos > img_width / 2:  # Reset when we've scrolled half the image
                    xpos = 0
                
                double_buffer.SetImage(image, -xpos)
                double_buffer.SetImage(image, -xpos + img_width // 2)
                
                double_buffer = self.matrix.SwapOnVSync(double_buffer)
                time.sleep(self.args.speed)
        except KeyboardInterrupt:
            return
            
    def scroll_vertical(self, image, direction="up", ypos_start=0):
        img_width, img_height = image.size
        double_buffer = self.matrix.CreateFrameCanvas()
        
        # Create an image that's taller for smooth vertical scrolling
        # We need to make it double the height of the matrix
        scroll_image = Image.new('RGB', (img_width, self.matrix.height * 2), (0, 0, 0))
        
        # If the image is smaller than display height, make it scroll nicely by duplicating
        if img_height < self.matrix.height:
            scroll_image.paste(image, (0, 0))
            scroll_image.paste(image, (0, self.matrix.height))
            img_height = scroll_image.height
            image = scroll_image
        
        # let's scroll
        ypos = ypos_start
        print("Press CTRL-C to stop.")
        try:
            while True:
                if direction == "up":
                    ypos += 1  # Scroll upward (content moves up)
                else:
                    ypos -= 1  # Scroll downward (content moves down)
                    
                # Handle wrapping for continuous scrolling
                if direction == "up" and ypos > img_height / 2:
                    ypos = 0
                elif direction == "down" and ypos < -img_height / 2:
                    ypos = 0
                
                # Create a view into our larger image
                # For vertical scrolling, we need to crop the image properly
                y_offset = -ypos if direction == "up" else ypos
                
                # Set the image twice to create a continuous scroll
                double_buffer.SetImage(image, 0, y_offset)
                if direction == "up":
                    double_buffer.SetImage(image, 0, y_offset - img_height // 2)
                else:
                    double_buffer.SetImage(image, 0, y_offset + img_height // 2)
                
                double_buffer = self.matrix.SwapOnVSync(double_buffer)
                time.sleep(self.args.speed)
        except KeyboardInterrupt:
            return
    
    def scroll_random(self, image):
        import random
        
        # Prepare images for both horizontal and vertical scrolling
        img_width, img_height = image.size
        
        # Create horizontal scrolling image
        h_scroll_image = Image.new('RGB', (self.matrix.width * 2, img_height), (0, 0, 0))
        h_scroll_image.paste(image, (0, 0))
        h_scroll_image.paste(image, (self.matrix.width, 0))
        
        # Create vertical scrolling image
        v_scroll_image = Image.new('RGB', (img_width, self.matrix.height * 2), (0, 0, 0))
        v_scroll_image.paste(image, (0, 0))
        v_scroll_image.paste(image, (0, self.matrix.height))
        
        double_buffer = self.matrix.CreateFrameCanvas()
        
        # Available scroll methods
        scroll_methods = ["horizontal", "up", "down"]
        current_method = random.choice(scroll_methods)
        
        # Position trackers
        xpos = 0
        ypos = 0
        
        # Timing variables
        last_change_time = time.time()
        random_interval = self.args.random_interval
        
        print("Random scroll mode. Press CTRL-C to stop.")
        try:
            while True:
                # Check if it's time to change the scroll method
                current_time = time.time()
                if current_time - last_change_time >= random_interval:
                    # Choose a new scroll method, different from the current one
                    available_methods = [m for m in scroll_methods if m != current_method]
                    current_method = random.choice(available_methods)
                    print(f"Changing to {current_method} scroll")
                    last_change_time = current_time
                
                # Handle the current scroll method
                if current_method == "horizontal":
                    xpos += 1
                    if xpos > h_scroll_image.width / 2:
                        xpos = 0
                    
                    double_buffer.SetImage(h_scroll_image, -xpos)
                    double_buffer.SetImage(h_scroll_image, -xpos + h_scroll_image.width // 2)
                
                elif current_method == "up":
                    ypos += 1
                    if ypos > v_scroll_image.height / 2:
                        ypos = 0
                    
                    double_buffer.SetImage(v_scroll_image, 0, -ypos)
                    double_buffer.SetImage(v_scroll_image, 0, -ypos + v_scroll_image.height // 2)
                
                elif current_method == "down":
                    ypos -= 1
                    if ypos < -v_scroll_image.height / 2:
                        ypos = 0
                    
                    double_buffer.SetImage(v_scroll_image, 0, ypos)
                    double_buffer.SetImage(v_scroll_image, 0, ypos + v_scroll_image.height // 2)
                
                double_buffer = self.matrix.SwapOnVSync(double_buffer)
                time.sleep(self.args.speed)
        
        except KeyboardInterrupt:
            return
    
    def static_image(self, image):
        # Display the image
        self.matrix.SetImage(image.convert('RGB'))
        
        try:
            print("Press CTRL-C to stop.")
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            return

# Main function
if __name__ == "__main__":
    text_display = ImageTextDisplay()
    if (not text_display.process()):
        text_display.print_help()