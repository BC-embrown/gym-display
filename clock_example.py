#!/usr/bin/env python
# Example: Digital Clock using the Matrix Text Display Library
import time
import sys
import signal
from datetime import datetime
from matrix_text_lib import MatrixTextDisplay

def main():
    # Create the display instance
    display = MatrixTextDisplay()
    
    # Process arguments first (important!)
    if not display.process():
        display.print_help()
        return
        
    # Configure initial display
    display.set_mode("static")
    display.set_font_size(16)  # Larger font for the clock
    display.set_color((0, 191, 255))  # Deep Sky Blue
    
    # Initialize with current time instead of default text
    now = datetime.now()
    display.set_text(now.strftime("%H:%M:%S"))
    
    # Start the display
    if not display.start():
        return
        
    # Setup signal handler for clean exit
    def signal_handler(sig, frame):
        print("Exiting...")
        display.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Display different clock formats
        formats = [
            "%H:%M:%S",      # 24-hour with seconds
            "%H:%M",         # 24-hour without seconds
            "%I:%M:%S %p",   # 12-hour with seconds and AM/PM
            "%I:%M %p",      # 12-hour without seconds, with AM/PM
            "%b %d\n%H:%M"   # Date and time
        ]
        
        format_index = 0
        format_change_time = time.time() + 20  # Change format every 20 seconds
        
        # Color cycle variables
        colors = [
            (255, 255, 255),  # White
            (0, 191, 255),    # Deep Sky Blue
            (255, 215, 0),    # Gold
            (152, 251, 152),  # Pale Green
            (255, 105, 180),  # Hot Pink
        ]
        color_index = 0
        color_change_time = time.time() + 5  # Change color every 5 seconds
        
        while True:
            # Get current time
            now = datetime.now()
            
            # Format the time according to current format
            time_str = now.strftime(formats[format_index])
            display.set_text(time_str)
            
            # Check if we should change format
            current_time = time.time()
            if current_time >= format_change_time:
                format_index = (format_index + 1) % len(formats)
                format_change_time = current_time + 20
                print(f"Switching to format: {formats[format_index]}")
                
                # When changing format, adjust font size based on complexity
                if "%b" in formats[format_index] or "\n" in formats[format_index]:
                    display.set_font_size(14)  # Smaller for multiline/date formats
                else:
                    display.set_font_size(16)  # Larger for time-only formats
            
            if current_time >= color_change_time:
                color_index = (color_index + 1) % len(colors)
                display.set_color(colors[color_index])
                color_change_time = current_time + 5
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        display.stop()
        
if __name__ == "__main__":
    main()