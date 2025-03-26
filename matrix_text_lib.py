#!/usr/bin/env python
from samplebase import SampleBase
from PIL import Image, ImageDraw, ImageFont
import time
import os
import textwrap
import random
import threading
import sys

class MatrixDisplay(SampleBase):
    def __init__(self, *args, **kwargs):
        super(MatrixDisplay, self).__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to display on the RGB LED panel", default="Hello world!")
        self.parser.add_argument("-m", "--mode", help="Display mode: 'scroll-h', 'scroll-up', 'scroll-down', 'random' or 'static'", default="static")
        self.parser.add_argument("--random-interval", help="Seconds between direction changes in random mode", default=5.0, type=float)
        self.parser.add_argument("--font-size", help="Font size to use", default=12, type=int)
        self.parser.add_argument("--color", help="Text color in R,G,B format (0-255)", default="255,255,0")
        self.parser.add_argument("--bg-color", help="Background color in R,G,B format (0-255)", default="0,0,0")
        self.parser.add_argument("--speed", help="Scroll speed (lower is faster)", default=0.03, type=float)
        self.parser.add_argument("--wrap", help="Number of characters per line (0 for auto)", default=0, type=int)
        self.parser.add_argument("--font", help="TrueType font file path", default=None)
        self.parser.add_argument("--image", help="Path to image file to display", default=None)
        
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._update_lock = threading.Lock()
        
        self._display_text = "Hello world!"
        self._display_mode = "static"
        self._text_color = (255, 255, 0)
        self._bg_color = (0, 0, 0)
        self._font_size = 12
        self._scroll_speed = 0.03
        self._wrap_length = 0
        self._font_path = None
        self._random_interval = 5.0
        self._image_path = None
        self._current_image = None
        self._display_type = "text"  # "text" or "image"
    
    def process_args(self):
        result = super(MatrixDisplay, self).process()
        if not result:
            return False
            
        self._display_text = self.args.text
        self._display_mode = self.args.mode.lower()
        self._font_size = self.args.font_size
        self._scroll_speed = self.args.speed
        self._wrap_length = self.args.wrap
        self._font_path = self.args.font
        self._random_interval = self.args.random_interval
        self._image_path = self.args.image
        
        if self._image_path and os.path.exists(self._image_path):
            self._display_type = "image"
            self.load_image(self._image_path)
        
        try:
            r, g, b = map(int, self.args.color.split(','))
            self._text_color = (r, g, b)
        except:
            self._text_color = (255, 255, 0)
            
        try:
            r, g, b = map(int, self.args.bg_color.split(','))
            self._bg_color = (r, g, b)
        except:
            self._bg_color = (0, 0, 0)
            
        return True
    
    def set_text(self, text):
        with self._update_lock:
            self._display_text = text
            self._display_type = "text"
    
    def set_mode(self, mode):
        if mode in ["scroll-h", "scroll", "scroll-up", "scroll-down", "random", "static"]:
            with self._update_lock:
                self._display_mode = mode
    
    def set_color(self, color):
        with self._update_lock:
            self._text_color = color
    
    def set_bg_color(self, color):
        with self._update_lock:
            self._bg_color = color
    
    def set_font_size(self, size):
        with self._update_lock:
            self._font_size = size
    
    def set_speed(self, speed):
        with self._update_lock:
            self._scroll_speed = speed
    
    def set_wrap_length(self, length):
        with self._update_lock:
            self._wrap_length = length
    
    def set_font(self, font_path):
        with self._update_lock:
            self._font_path = font_path
    
    def set_random_interval(self, interval):
        with self._update_lock:
            self._random_interval = interval
    
    def load_image(self, image_path):
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return False
            
        try:
            with self._update_lock:
                img = Image.open(image_path).convert('RGB')
                self._current_image = img
                self._display_type = "image"
                self._image_path = image_path
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def create_text_image(self):
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
                    '/Library/Fonts/Arial.ttf',
                    'C:\\Windows\\Fonts\\arial.ttf',
                ]
                for path in font_paths:
                    if os.path.exists(path):
                        font = ImageFont.truetype(path, self._font_size)
                        break
        except Exception as e:
            print(f"Error loading font: {e}")
        
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
    
    def get_display_image(self):
        if self._display_type == "image" and self._current_image:
            width, height = self.matrix.width, self.matrix.height
            img = self._current_image.copy()
            img.thumbnail((width, height), Image.LANCZOS)
            
            # Center the image if smaller than matrix
            if img.width < width or img.height < height:
                new_img = Image.new('RGB', (width, height), self._bg_color)
                paste_x = (width - img.width) // 2
                paste_y = (height - img.height) // 2
                new_img.paste(img, (paste_x, paste_y))
                return new_img
            return img
        else:
            return self.create_text_image()
    
    def start(self):
        if self._running:
            print("Display is already running.")
            return False
        
        if not hasattr(self, 'matrix'):
            print("Error: Matrix not initialized. Call process() first.")
            return False
        
        if not hasattr(self, 'args'):
            self.process_args()
        
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
        last_text = None
        last_color = None
        last_mode = None
        last_image_path = None
        last_display_type = None
        
        try:
            while not self._stop_event.is_set():
                with self._update_lock:
                    text_changed = last_text != self._display_text
                    color_changed = last_color != self._text_color
                    mode_changed = last_mode != self._display_mode
                    image_changed = last_image_path != self._image_path
                    type_changed = last_display_type != self._display_type
                    
                    mode = self._display_mode
                    display_type = self._display_type
                    
                    if text_changed or color_changed or image_changed or type_changed:
                        image = self.get_display_image()
                        last_text = self._display_text
                        last_color = self._text_color
                        last_image_path = self._image_path
                        last_display_type = self._display_type
                        
                    speed = self._scroll_speed
                    random_interval = self._random_interval
                
                if mode == "scroll-h" or mode == "scroll":
                    self._scroll_horizontal(image, speed)
                elif mode == "scroll-up":
                    self._scroll_vertical(image, "up", speed)
                elif mode == "scroll-down":
                    self._scroll_vertical(image, "down", speed)
                elif mode == "random":
                    self._scroll_random(image, speed, random_interval)
                else:
                    self._static_image(image)
                
                last_mode = mode
                
                # If something changed during a scroll method, break out
                # and restart the loop
                if self._stop_event.is_set():
                    break
                    
                if (last_text != self._display_text or 
                    last_color != self._text_color or 
                    last_mode != self._display_mode or
                    last_image_path != self._image_path or
                    last_display_type != self._display_type):
                    continue
                    
                # Add a small delay to prevent this loop from consuming too much CPU
                time.sleep(0.05)
                
        except Exception as e:
            print(f"Error in display loop: {e}")
        finally:
            self._running = False
    
    def _scroll_horizontal(self, image, speed):
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
            with self._update_lock:
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
            with self._update_lock:
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
                with self._update_lock:
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
    
    def _static_image(self, image):
        self.matrix.SetImage(image.convert('RGB'))
        
        check_interval = 0.1
        while not self._stop_event.is_set():
            with self._update_lock:
                if self._display_mode != "static":
                    break
            time.sleep(check_interval)
    
    def display_image_for_duration(self, image_path, duration):
        if self.load_image(image_path):
            self.set_mode("static")
            if not self._running:
                self.start()
            time.sleep(duration)
            return True
        return False
    
    def show_image(self, image_path):
        return self.load_image(image_path)
    
    def show_text(self, text, color=None, size=None):
        self.set_text(text)
        if color:
            self.set_color(color)
        if size:
            self.set_font_size(size)
        
    def run(self):
        self.process_args()
        
        image = self.get_display_image()
        
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

if __name__ == "__main__":
    display = MatrixDisplay()
    if not display.process():
        display.print_help()
    else:
        try:
            display.run()
        except KeyboardInterrupt:
            print("Exiting\n")
            sys.exit(0)