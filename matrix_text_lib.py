#!/usr/bin/env python
# RGB Matrix Text Display Library
from samplebase import SampleBase
from PIL import Image, ImageDraw, ImageFont
import time
import os
import textwrap
import random
import threading

class MatrixTextDisplay(SampleBase):
    def __init__(self, *args, **kwargs):
        super(MatrixTextDisplay, self).__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to display on the RGB LED panel", default="Hello world!")
        self.parser.add_argument("--mode", help="Display mode: 'scroll-h', 'scroll-up', 'scroll-down', 'random' or 'static'", default="static")
        self.parser.add_argument("--random-interval", help="Seconds between direction changes in random mode", default=5.0, type=float)
        self.parser.add_argument("--font-size", help="Font size to use", default=12, type=int)
        self.parser.add_argument("--color", help="Text color in R,G,B format (0-255)", default="255,255,0")
        self.parser.add_argument("--bg-color", help="Background color in R,G,B format (0-255)", default="0,0,0")
        self.parser.add_argument("--speed", help="Scroll speed (lower is faster)", default=0.03, type=float)
        self.parser.add_argument("--wrap", help="Number of characters per line (0 for auto)", default=0, type=int)
        self.parser.add_argument("--font", help="TrueType font file path", default=None)
        

        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._text_update_lock = threading.Lock()
        
        self._display_text = "Hello world!"
        self._display_mode = "static"
        self._text_color = (255, 255, 0)
        self._bg_color = (0, 0, 0)
        self._font_size = 12
        self._scroll_speed = 0.03
        self._wrap_length = 0
        self._font_path = None
        self._random_interval = 5.0
        
    def process_args(self):
        """Process command line arguments and set display properties"""
        if not hasattr(self, 'args'):
            self.args = self.parser.parse_args()
            
        self._display_text = self.args.text
        self._display_mode = self.args.mode.lower()
        self._font_size = self.args.font_size
        self._scroll_speed = self.args.speed
        self._wrap_length = self.args.wrap
        self._font_path = self.args.font
        self._random_interval = self.args.random_interval
        
        try:
            r, g, b = map(int, self.args.color.split(','))
            self._text_color = (r, g, b)
        except:
            print("Text color format should be R,G,B (e.g., 255,255,0 for yellow)")
            self._text_color = (255, 255, 0) 
            
        try:
            r, g, b = map(int, self.args.bg_color.split(','))
            self._bg_color = (r, g, b)
        except:
            print("Background color format should be R,G,B (e.g., 0,0,0 for black)")
            self._bg_color = (0, 0, 0)
    
    def set_text(self, text):
        """Update the displayed text"""
        with self._text_update_lock:
            self._display_text = text
    
    def set_mode(self, mode):
        """Update the display mode"""
        if mode in ["scroll-h", "scroll", "scroll-up", "scroll-down", "random", "static"]:
            with self._text_update_lock:
                self._display_mode = mode
        else:
            print(f"Invalid mode: {mode}")
    
    def set_color(self, color):
        """Update the text color (tuple of R,G,B values from 0-255)"""
        with self._text_update_lock:
            self._text_color = color
    
    def set_bg_color(self, color):
        """Update the background color (tuple of R,G,B values from 0-255)"""
        with self._text_update_lock:
            self._bg_color = color
    
    def set_font_size(self, size):
        """Update the font size"""
        with self._text_update_lock:
            self._font_size = size
    
    def set_speed(self, speed):
        """Update the scroll speed (lower is faster)"""
        with self._text_update_lock:
            self._scroll_speed = speed
    
    def set_wrap_length(self, length):
        """Update the text wrap length (0 for auto)"""
        with self._text_update_lock:
            self._wrap_length = length
    
    def set_font(self, font_path):
        """Update the font file path"""
        with self._text_update_lock:
            self._font_path = font_path
    
    def set_random_interval(self, interval):
        """Update the random scroll direction change interval (seconds)"""
        with self._text_update_lock:
            self._random_interval = interval
    
    def create_text_image(self):
        """Generate image with the current text and settings"""
        width, height = self.matrix.width, self.matrix.height
        
        image = Image.new('RGB', (width, height), self._bg_color)
        draw = ImageDraw.Draw(image)
        
        font = None
        try:
            if self._font_path:
                font = ImageFont.truetype(self._font_path, self._font_size)
            else:
                font_paths = [
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                    'C:\\Windows\\Fonts\\arial.ttf'
                ]
                for path in font_paths:
                    if os.path.exists(path):
                        font = ImageFont.truetype(path, self._font_size)
                        break
        except Exception as e:
            print(f"Error loading font: {e}")
            print("Falling back to default font")
        
        if font is None:
            font = ImageFont.load_default()
        
        text = self._display_text
        if self._wrap_length > 0:
            wrapped_text = textwrap.fill(text, self._wrap_length)
        else:
            avg_char_width = draw.textlength("X", font=font)
            chars_per_line = max(1, int(width / avg_char_width))
            wrapped_text = textwrap.fill(text, chars_per_line)
        
        text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        position = ((width - text_width) // 2, (height - text_height) // 2)
        
        draw.multiline_text(position, wrapped_text, font=font, fill=self._text_color, align="center")
        
        return image
    
    def start(self):
        """Start displaying text in a background thread"""
        if self._running:
            print("Display is already running.")
            return
        
        if not hasattr(self, 'matrix'):
            if not self.process():
                self.print_help()
                return False
        
        self._stop_event.clear()
        
        self._thread = threading.Thread(target=self._display_loop)
        self._thread.daemon = True
        self._running = True
        self._thread.start()
        return True
    
    def stop(self):
        if not self._running:
            return
        
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self._running = False
    
    def _display_loop(self):
        try:
            while not self._stop_event.is_set():
                with self._text_update_lock:
                    mode = self._display_mode
                    image = self.create_text_image()
                    speed = self._scroll_speed
                    random_interval = self._random_interval
                
                if mode == "scroll-h" or mode == "scroll":
                    self._scroll_horizontal(image, speed)
                    if self._stop_event.is_set():
                        break
                elif mode == "scroll-up":
                    self._scroll_vertical(image, "up", speed)
                    if self._stop_event.is_set():
                        break
                elif mode == "scroll-down":
                    self._scroll_vertical(image, "down", speed)
                    if self._stop_event.is_set():
                        break
                elif mode == "random":
                    self._scroll_random(image, speed, random_interval)
                    if self._stop_event.is_set():
                        break
                else:  # static
                    self._static_image(image)
                    if self._stop_event.is_set():
                        break
        except Exception as e:
            print(f"Error in display loop: {e}")
        finally:
            self._running = False
    
    def _scroll_horizontal(self, image, speed):
        """Horizontal scrolling implementation with stop check"""
        img_width, img_height = image.size
        double_buffer = self.matrix.CreateFrameCanvas()
        
        if img_width < self.matrix.width:
            scroll_image = Image.new('RGB', (self.matrix.width * 2, img_height), self._bg_color)
            scroll_image.paste(image, (0, 0))
            scroll_image.paste(image, (self.matrix.width, 0))
            img_width = scroll_image.width
            image = scroll_image
        
        xpos = 0
        while not self._stop_event.is_set():
            with self._text_update_lock:
                if self._display_mode != "scroll-h" and self._display_mode != "scroll":
                    break
                current_speed = self._scroll_speed
            
            xpos += 1
            if xpos > img_width / 2:
                xpos = 0
            
            double_buffer.SetImage(image, -xpos)
            double_buffer.SetImage(image, -xpos + img_width // 2)
            
            double_buffer = self.matrix.SwapOnVSync(double_buffer)
            time.sleep(current_speed)
    
    def _static_image(self, image):
        self.matrix.SetImage(image.convert('RGB'))
        
        check_interval = 0.1 
        while not self._stop_event.is_set():
            with self._text_update_lock:
                if self._display_mode != "static":
                    break
            time.sleep(check_interval)
    
    def run(self):
        self.process_args()
        
        image = self.create_text_image()
        
        mode = self._display_mode
        if mode == "scroll-h" or mode == "scroll":
            self._scroll_horizontal(image, self._scroll_speed)
        elif mode == "scroll-up":
            self._scroll_vertical(image, "up", self._scroll_speed)
        elif mode == "scroll-down":
            self._scroll_vertical(image, "down", self._scroll_speed)
        elif mode == "random":
            self._scroll_random(image, self._scroll_speed, self._random_interval)
        else:
            self._static_image(image)

    def _scroll_vertical(self, image, direction, speed):
        img_width, img_height = image.size
        double_buffer = self.matrix.CreateFrameCanvas()
        
        scroll_image = Image.new('RGB', (img_width, self.matrix.height * 2), self._bg_color)
        scroll_image.paste(image, (0, 0))
        scroll_image.paste(image, (0, self.matrix.height))
        img_height = scroll_image.height
        image = scroll_image

        ypos = 0
        while not self._stop_event.is_set():
            with self._text_update_lock:
                mode_dir = "up" if self._display_mode == "scroll-up" else "down"
                if mode_dir != direction:
                    break
                current_speed = self._scroll_speed
            
            if direction == "up":
                ypos += 1
            else:
                ypos -= 1
                
            if direction == "up" and ypos > img_height / 2:
                ypos = 0
            elif direction == "down" and ypos < -img_height / 2:
                ypos = 0
            
            y_offset = -ypos if direction == "up" else ypos
            
            double_buffer.SetImage(image, 0, y_offset)
            if direction == "up":
                double_buffer.SetImage(image, 0, y_offset - img_height // 2)
            else:
                double_buffer.SetImage(image, 0, y_offset + img_height // 2)
            
            double_buffer = self.matrix.SwapOnVSync(double_buffer)
            time.sleep(current_speed)
    
    def _scroll_random(self, image, speed, random_interval):
        img_width, img_height = image.size
        
        h_scroll_image = Image.new('RGB', (self.matrix.width * 2, img_height), self._bg_color)
        h_scroll_image.paste(image, (0, 0))
        h_scroll_image.paste(image, (self.matrix.width, 0))
        
        v_scroll_image = Image.new('RGB', (img_width, self.matrix.height * 2), self._bg_color)
        v_scroll_image.paste(image, (0, 0))
        v_scroll_image.paste(image, (0, self.matrix.height))
        
        double_buffer = self.matrix.CreateFrameCanvas()
        
        scroll_methods = ["horizontal", "up", "down"]
        current_method = random.choice(scroll_methods)
        
        xpos = 0
        ypos = 0
        
        last_change_time = time.time()
        
        while not self._stop_event.is_set():
            with self._text_update_lock:
                if self._display_mode != "random":
                    break
                current_speed = self._scroll_speed
                current_interval = self._random_interval
            
            current_time = time.time()
            if current_time - last_change_time >= current_interval:
                available_methods = [m for m in scroll_methods if m != current_method]
                current_method = random.choice(available_methods)
                last_change_time = current_time
            
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
            time.sleep(current_speed)