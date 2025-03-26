#!/usr/bin/env python
import time
import sys
import signal
from matrix_text_lib import MatrixTextDisplay

def main():

    display = MatrixTextDisplay()

    if not display.start():
        return
        
    def signal_handler(sig, frame):
        print("Exiting...")
        display.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("Displaying static text...")
        time.sleep(5)
        
        print("Changing to scrolling text...")
        display.set_mode("scroll-h")
        display.set_text("This text is scrolling horizontally!")
        display.set_color((255, 0, 0))
        time.sleep(10)
        
        print("Changing text and color...")
        display.set_text("Vertical scrolling")
        display.set_mode("scroll-up")
        display.set_color((0, 255, 0))
        time.sleep(10)
        
        print("Changing to random scroll mode...")
        display.set_text("Random direction scrolling")
        display.set_mode("random")
        display.set_random_interval(3.0) 
        display.set_color((0, 0, 255)) 
        time.sleep(15)
        
        print("Back to static with larger font...")
        display.set_mode("static")
        display.set_text("BIG!")
        display.set_font_size(20)
        display.set_color((255, 255, 0)) 
        time.sleep(5)
        
        colors = [
            (255, 0, 0),   # Red
            (0, 255, 0),   # Green
            (0, 0, 255),   # Blue
            (255, 255, 0), # Yellow
            (255, 0, 255), # Magenta
            (0, 255, 255), # Cyan
            (255, 255, 255) # White
        ]
        
        print("Color cycle demo...")
        for i in range(20):
            color_index = i % len(colors)
            display.set_color(colors[color_index])
            display.set_text(f"Color #{color_index+1}")
            time.sleep(1)
            
        print("Demo complete. Press CTRL-C to exit.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        display.stop()
        
if __name__ == "__main__":
    main()