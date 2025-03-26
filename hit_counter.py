#!/usr/bin/env python3
import time
import sys
import os
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import threading
import traceback
import getpass

class BreakBeamCounter:
    def __init__(self, logo_path="./logo.png", debounce_time=1):
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
            path = os.path.dirname(os.path.realpath(__file__)) + "/" + 'logo.png'
            img = Image.open(r'/home/pi/gym/gym-display/logo.png').convert('RGB')
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
            print(traceback.format_exc())
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
            print("Starting break beam counter...")

            if os.path.exists(self.logo_path):
                print(f"Displaying logo for 3 seconds: {self.logo_path}")
                self.display_image(self.logo_path, 3)
            
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