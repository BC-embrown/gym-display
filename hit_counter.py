#!/usr/bin/env python3
import time
import sys
import os
import gpiod
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import threading

class GpiodHitCounter:
    def __init__(self, logo_path="logo.png", sensor_pins=[26, 16, 5, 6], debounce_time=0.5):
        self.count = 0
        self.logo_path = logo_path
        self.sensor_pins = sensor_pins
        self.debounce_time = debounce_time
        self.last_hit_time = 0
        self.running = True
        
        # Configure matrix options
        self.options = RGBMatrixOptions()
        self.options.rows = 64
        self.options.cols = 64
        self.options.chain_length = 1
        self.options.parallel = 1
        self.options.hardware_mapping = 'regular'
        self.options.gpio_slowdown = 5  # Add this to help with stability
        self.options.brightness = 100
        self.options.disable_hardware_pulsing = True  # Important for avoiding priority errors
        
        # Create matrix
        self.matrix = RGBMatrix(options=self.options)
        self.canvas = self.matrix.CreateFrameCanvas()
        
        # Try to load a font
        self.font = None
        self.font_size = 32
        self.text_color = (214,160,255)
        try:
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
                '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
            ]
            for path in font_paths:
                if os.path.exists(path):
                    self.font = ImageFont.truetype(path, self.font_size)
                    print(f"Loaded font: {path}")
                    break
        except Exception as e:
            print(f"Error loading font: {e}")
            
        if self.font is None:
            print("Using default font")
            self.font = ImageFont.load_default()
        
        # Initialize gpiod
        try:
            self.chip = gpiod.Chip('gpiochip0')
            self.setup_gpio()
        except Exception as e:
            print(f"Error initializing GPIO: {e}")
            print("You may need to install gpiod: sudo apt install python3-gpiod")
            sys.exit(1)
    
    def setup_gpio(self):
        # Configure lines for input with pull-up
        self.lines = []
        for pin in self.sensor_pins:
            try:
                line = self.chip.get_line(pin)
                line.request(consumer="hit_counter", type=gpiod.LINE_REQ_EV_FALLING_EDGE, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)
                self.lines.append(line)
                print(f"Set up GPIO pin {pin}")
            except Exception as e:
                print(f"Error setting up pin {pin}: {e}")
        
        # Start a thread to monitor GPIO
        self.gpio_thread = threading.Thread(target=self.monitor_gpio)
        self.gpio_thread.daemon = True
        self.gpio_thread.start()
    
    def monitor_gpio(self):
        while self.running:
            for line in self.lines:
                try:
                    if line.event_wait(timeout=0.01):
                        event = line.event_read()
                        if event.type == gpiod.LINE_EVENT_FALLING_EDGE:
                            self.hit_detected(line.offset())
                except Exception as e:
                    pass  # Ignore transient errors
            time.sleep(0.01)  # Small delay to reduce CPU usage
    
    def hit_detected(self, pin):
        current_time = time.time()
        
        if current_time - self.last_hit_time > self.debounce_time:
            self.count += 1
            self.last_hit_time = current_time
            print(f"Hit detected on pin {pin}! Count: {self.count}")
            
            self.update_display()
    
    def update_display(self):
        self.display_number(self.count)
    
    def display_image(self, image_path, duration=None):
        try:
            if not os.path.exists(image_path):
                print(f"Image not found: {image_path}")
                return False
                
            img = Image.open(image_path).convert('RGB')
            img.thumbnail((self.matrix.width, self.matrix.height), Image.LANCZOS)
            
            # Center the image
            width, height = img.size
            x_offset = (self.matrix.width - width) // 2
            y_offset = (self.matrix.height - height) // 2
            
            # Clear the canvas
            self.canvas.Clear()
            
            # Display the image
            self.canvas.SetImage(img, x_offset, y_offset)
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            
            if duration:
                time.sleep(duration)
                
            return True
            
        except Exception as e:
            print(f"Error displaying image: {e}")
            return False
    
    def display_number(self, number):
        # Create a new image with black background
        img = Image.new('RGB', (self.matrix.width, self.matrix.height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Convert number to string
        text = str(number)
        
        # Calculate text position to center it
        text_bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        position = ((self.matrix.width - text_width) // 2, (self.matrix.height - text_height) // 2)
        
        # Draw the text
        draw.text(position, text, font=self.font, fill=self.text_color)
        
        # Display the image
        self.canvas.SetImage(img)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def run(self):
        try:
            print("Starting hit counter...")
            
            # Display logo if available
            if os.path.exists(self.logo_path):
                print(f"Displaying logo for 3 seconds: {self.logo_path}")
                self.display_image(self.logo_path, 3)
            
            # Initialize counter display
            self.display_number(0)
            
            print("Counter started. Press CTRL-C to exit.")
            
            # Keep the program running
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("Program interrupted")
        finally:
            self.cleanup()
    
    def cleanup(self):
        print(f"Final count: {self.count}")
        # Clear the display
        self.canvas.Clear()
        self.matrix.SwapOnVSync(self.canvas)
        # Stop GPIO monitoring
        self.running = False
        if hasattr(self, 'gpio_thread'):
            self.gpio_thread.join(timeout=1.0)
        # Release GPIO lines
        for line in self.lines:
            line.release()

if __name__ == "__main__":
    counter = GpiodHitCounter()
    counter.run()