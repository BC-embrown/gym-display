#!/usr/bin/env python3
import time
import sys
import os
from gpiozero import Button
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions

class GpioZeroHitCounter:
    def __init__(self, logo_path="logo.png", sensor_pins=[26, 16, 5, 6], debounce_time=0.5):
        self.count = 0
        self.logo_path = logo_path
        self.debounce_time = debounce_time
        self.last_hit_time = 0
        
        # Configure matrix options
        self.options = RGBMatrixOptions()
        self.options.rows = 64
        self.options.cols = 64
        self.options.chain_length = 1
        self.options.parallel = 1
        self.options.hardware_mapping = 'regular'
        self.options.disable_hardware_pulsing = True
        
        # Create matrix
        self.matrix = RGBMatrix(options=self.options)
        self.canvas = self.matrix.CreateFrameCanvas()
        self.font = None      
        # Load font
        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            self.font = ImageFont.truetype(font_path, 20)
        except:
            self.font = ImageFont.load_default()

        self.font_size = 32
        self.text_color = (214,160,255)
        # Setup buttons with pull-up resistors
        self.buttons = []
        for pin in sensor_pins:
            try:
                button = Button(pin, pull_up=True, bounce_time=debounce_time)
                button.when_pressed = self.hit_detected
                self.buttons.append(button)
                print(f"Set up sensor on pin {pin}")
            except Exception as e:
                print(f"Error setting up pin {pin}: {e}")
    
    def hit_detected(self):
        current_time = time.time()
        if current_time - self.last_hit_time > self.debounce_time:
            self.count += 1
            self.last_hit_time = current_time
            print(f"Hit detected! Count: {self.count}")
            self.display_number(self.count)
    
    def display_image(self, image_path, duration=None):
        try:
            img = Image.open(image_path).convert('RGB')
            img.thumbnail((self.matrix.width, self.matrix.height), Image.LANCZOS)
            self.canvas.SetImage(img)
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            if duration:
                time.sleep(duration)
            return True
        except Exception as e:
            print(f"Error displaying image: {e}")
            return False
    
    def display_number(self, number):
        img = Image.new('RGB', (self.matrix.width, self.matrix.height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        text = str(number)
        
        text_bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        position = ((self.matrix.width - text_width) // 2, (self.matrix.height - text_height) // 2)
        draw.text(position, text, font=self.font, fill=(255, 255, 255))
        
        self.canvas.SetImage(img)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def run(self):
        try:
            print("Starting hit counter...")
            
            if os.path.exists(self.logo_path):
                print(f"Displaying logo for 3 seconds: {self.logo_path}")
                self.display_image(self.logo_path, 3)
            
            self.display_number(0)
            print("Counter started. Press CTRL-C to exit.")
            
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("Program interrupted")
            print(f"Final count: {self.count}")

if __name__ == "__main__":
    counter = GpioZeroHitCounter()
    counter.run()