#!/usr/bin/env python3
import time
import sys
import os
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import threading
import base64
import io

LOGO_BASE64 = b'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'

class BreakBeamCounter:
    def __init__(self, logo_path="logo.png", debounce_time=1):
        self.count = 0
        self.logo_path = logo_path
        self.debounce_time = debounce_time
        self.last_hit_time = 0
        self.running = True
        
        # Configure the sensors
        # Using the pins specified in your documentation
        self.setup_sensors()
        
        # Configure matrix options
        self.options = RGBMatrixOptions()
        self.options.rows = 64
        self.options.cols = 64
        self.options.chain_length = 1
        self.options.parallel = 1
        self.options.hardware_mapping = 'regular'
        self.options.gpio_slowdown = 5
        self.options.brightness = 100
        self.options.disable_hardware_pulsing = True
        
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
        
        # Start sensor monitoring thread
        self.sensor_thread = threading.Thread(target=self.monitor_sensors)
        self.sensor_thread.daemon = True
        self.sensor_thread.start()
    
    def setup_sensors(self):
        # Define the pin mappings - update these according to your connections
        # These map from the example D5 to appropriate board pins
        try:
            # Create digital inputs with pull-up resistors
            # The D5, D6, etc. names in the Adafruit example map to these GPIO pins
            # Update these to match your actual connections
            self.break_beam1 = digitalio.DigitalInOut(board.D26)  # GPIO26 (Pin 37)
            self.break_beam2 = digitalio.DigitalInOut(board.D16)  # GPIO16 (Pin 36)
            self.break_beam3 = digitalio.DigitalInOut(board.D5)   # GPIO5 (Pin 29)
            self.break_beam4 = digitalio.DigitalInOut(board.D6)   # GPIO6 (Pin 31)
            
            # Configure all sensors
            for sensor in [self.break_beam1, self.break_beam2, self.break_beam3, self.break_beam4]:
                sensor.direction = digitalio.Direction.INPUT
                sensor.pull = digitalio.Pull.UP
                
            print("All break beam sensors initialized")
            
        except Exception as e:
            print(f"Error setting up sensors: {e}")
            print("Note: If you see 'module' object has no attribute errors, you may need to update your pin definitions")
            # Try with explicit fallback to GPIO pins if board.D* doesn't work
            try:
                import busio
                print("Attempting alternate pin initialization...")
                
                # Try using the Pin module directly
                from adafruit_blinka.microcontroller.bcm283x.pin import Pin
                self.break_beam1 = digitalio.DigitalInOut(Pin(26))
                self.break_beam2 = digitalio.DigitalInOut(Pin(16))
                self.break_beam3 = digitalio.DigitalInOut(Pin(5))
                self.break_beam4 = digitalio.DigitalInOut(Pin(6))
                
                # Configure all sensors
                for sensor in [self.break_beam1, self.break_beam2, self.break_beam3, self.break_beam4]:
                    sensor.direction = digitalio.Direction.INPUT
                    sensor.pull = digitalio.Pull.UP
                    
                print("Alternative sensor initialization successful")
                
            except Exception as alt_e:
                print(f"Alternative initialization also failed: {alt_e}")
                print("Continuing without sensors - keyboard control only")
                
                # Keyboard fallback for testing
                print("Press SPACE to simulate a hit")
                self.kb_thread = threading.Thread(target=self.keyboard_listener)
                self.kb_thread.daemon = True
                self.kb_thread.start()
    
    def keyboard_listener(self):
        try:
            import termios, tty, sys
            def getch():
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    ch = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                return ch
                
            while self.running:
                key = getch()
                if key == ' ':
                    self.hit_detected("Keyboard")
                elif key.lower() == 'q':
                    self.running = False
                    break
        except Exception as e:
            print(f"Error in keyboard listener: {e}")
    
    def monitor_sensors(self):
        # Store previous states to detect changes
        prev_states = {
            "beam1": True,
            "beam2": True,
            "beam3": True,
            "beam4": True
        }
        
        while self.running:
            try:
                # Check each sensor
                curr_states = {
                    "beam1": self.break_beam1.value,
                    "beam2": self.break_beam2.value, 
                    "beam3": self.break_beam3.value,
                    "beam4": self.break_beam4.value
                }
                
                # Check for any beam break (LOW signal)
                for name, state in curr_states.items():
                    # If beam was previously unbroken (True) and is now broken (False)
                    if prev_states[name] and not state:
                        print(f"{name} was just broken!")
                        self.hit_detected(name)
                
                # Update previous states
                prev_states = curr_states.copy()
                
            except Exception as e:
                print(f"Error reading sensors: {e}")
            
            # Small delay to prevent CPU overuse
            time.sleep(0.01)
    
    def hit_detected(self, source):
        current_time = time.time()
        
        if current_time - self.last_hit_time > self.debounce_time:
            self.count += 1
            self.last_hit_time = current_time
            print(f"Hit detected from {source}! Count: {self.count}")
            
            self.update_display()
    
    def update_display(self):
        self.display_number(self.count)
    
    def display_image(self, image_path, duration=None):
        try:
            print(f"Attempting to open image: {image_path}")
            if not os.path.exists(image_path):
                print(f"Image not found: {image_path}")
                return False
                
            img = Image.open(image_path)
            print(f"Image opened successfully. Format: {img.format}, Size: {img.size}, Mode: {img.mode}")
            img = img.convert('RGB')
            print("Converted to RGB")
            
            img.thumbnail((self.matrix.width, self.matrix.height), Image.LANCZOS)
            print(f"Resized to: {img.size}")
            
            # Center the image
            width, height = img.size
            x_offset = (self.matrix.width - width) // 2
            y_offset = (self.matrix.height - height) // 2
            print(f"Positioning at offset: ({x_offset}, {y_offset})")
            
            # Clear the canvas
            self.canvas.Clear()
            print("Canvas cleared")
            
            # Display the image
            self.canvas.SetImage(img, x_offset, y_offset)
            print("Image set to canvas")
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            print("Canvas swapped")
            
            if duration:
                print(f"Waiting for {duration} seconds")
                time.sleep(duration)
                
            return True
                
        except Exception as e:
            print(f"Error displaying image: {e}")
            import traceback
            traceback.print_exc()
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

    def display_embedded_logo(self, duration=3):
        """Display the embedded logo"""
        try:
            # Decode the embedded logo
            logo_data = base64.b64decode(LOGO_BASE64)
            logo_stream = io.BytesIO(logo_data)
            
            # Explicitly specify the format (adjust if your logo is not PNG)
            img = Image.open(logo_stream, formats=["PNG"]).convert('RGB')
            
            # Print image details for debugging
            print(f"Image opened: Size={img.size}, Mode={img.mode}")
            
            # Resize and display
            img.thumbnail((self.matrix.width, self.matrix.height), Image.LANCZOS)
            self.canvas.SetImage(img)
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            time.sleep(duration)
            return True
        except Exception as e:
            print(f"Error displaying embedded logo: {e}")
            import traceback
            traceback.print_exc()  # Print the full stack trace
            return False


    def run(self):
        try:
            print("Starting break beam counter...")
            
            self.display_embedded_logo(3)
            
            # Initialize counter display
            self.display_number(0)
            
            print("Counter started. Press CTRL-C to exit.")
            
            # Keep the program running
            while self.running:
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
        # Stop monitoring
        self.running = False
        if hasattr(self, 'sensor_thread'):
            self.sensor_thread.join(timeout=1.0)

if __name__ == "__main__":
    counter = BreakBeamCounter()
    counter.run()