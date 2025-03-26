#!/usr/bin/env python
import time
import sys
import os
import threading
from matrix_display import MatrixDisplay

class TestHitCounter:
    def __init__(self, logo_path="logo.png", sensor_pins=[17, 18, 27, 22], debounce_time=0.5):
        self.count = 0
        self.logo_path = logo_path
        self.sensor_pins = sensor_pins
        self.debounce_time = debounce_time
        self.last_hit_time = 0
        
        self.display = MatrixDisplay()
        
        self.display.parser.add_argument("--led-no-drop-privs", dest="drop_privileges",
        help="Don't drop privileges from 'root' after initializing the hardware.",
        action='store_false')
        self.display.parser.set_defaults(drop_privileges=False)
        
        if not self.display.process():
            self.display.print_help()
            sys.exit(1)
    
    def keyboard_listener(self):
        print("Press SPACE to simulate a hit, Q to quit")
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
                
            while True:
                key = getch()
                if key == ' ':
                    self.hit_detected()
                elif key.lower() == 'q':
                    break
        except Exception as e:
            print(f"Error in keyboard listener: {e}")
    
    def hit_detected(self):
        current_time = time.time()
        
        if current_time - self.last_hit_time > self.debounce_time:
            self.count += 1
            self.last_hit_time = current_time
            print(f"Hit detected! Count: {self.count}")
            
            self.update_display()
    
    def update_display(self):
        self.display.set_text(str(self.count))
        self.display.set_font_size(20)
        self.display.set_color((255, 255, 255))
    
    def run(self):
        try:
            print("Starting test hit counter...")
            
            if os.path.exists(self.logo_path):
                print(f"Displaying logo for 3 seconds: {self.logo_path}")
                self.display.display_image_for_duration(self.logo_path, 3)
            else:
                print(f"Logo file not found: {self.logo_path}")
            
            self.display.set_text("0")
            self.display.set_font_size(20)
            self.display.set_color((255, 255, 255))
            self.display.set_mode("static")
            
            if not self.display._running:
                self.display.start()
            
            kb_thread = threading.Thread(target=self.keyboard_listener)
            kb_thread.daemon = True
            kb_thread.start()
            
            print("Counter started.")
            kb_thread.join()
                
        except KeyboardInterrupt:
            print("Program interrupted")
        finally:
            self.cleanup()
    
    def cleanup(self):
        print(f"Final count: {self.count}")
        self.display.stop()

if __name__ == "__main__":
    counter = TestHitCounter()
    counter.run()