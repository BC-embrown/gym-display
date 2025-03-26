#!/usr/bin/env python
import time
import sys
import os
import RPi.GPIO as GPIO
from matrix_display import MatrixDisplay

class HitCounter:
    def __init__(self, logo_path="logo.png", sensor_pins=[17, 18, 27, 22], debounce_time=0.5):
        self.count = 0
        self.logo_path = logo_path
        self.sensor_pins = sensor_pins
        self.debounce_time = debounce_time
        self.last_hit_time = 0
        
        self.display = MatrixDisplay()
        if not self.display.process():
            self.display.print_help()
            sys.exit(1)
        
        self.setup_gpio()
    
    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        
        for pin in self.sensor_pins:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.hit_detected, bouncetime=int(self.debounce_time * 1000))
    
    def hit_detected(self, channel):
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
            print("Starting hit counter...")
            
            if os.path.exists(self.logo_path):
                print(f"Displaying logo for 3 seconds: {self.logo_path}")
                self.display.display_image_for_duration(self.logo_path, 3)
            
            self.display.set_text("0")
            self.display.set_font_size(20)
            self.display.set_color((255, 255, 255))
            self.display.set_mode("static")
            
            if not self.display._running:
                self.display.start()
            
            print("Counter started. Press CTRL-C to exit.")
            
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("Program interrupted")
        finally:
            self.cleanup()
    
    def cleanup(self):
        print(f"Final count: {self.count}")
        self.display.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    counter = HitCounter()
    counter.run()