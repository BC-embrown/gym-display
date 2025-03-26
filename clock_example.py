#!/usr/bin/env python
# Debugged Clock Example
import time
import sys
import signal
from datetime import datetime
from matrix_text_lib import MatrixTextDisplay

def main():
    print("Starting clock application...")
    
    # Create the display instance
    display = MatrixTextDisplay()
    print("Display instance created")
    
    # Process arguments explicitly
    print("Processing arguments...")
    result = display.process()
    print(f"Process result: {result}")
    
    if not result:
        print("Failed to process arguments, printing help and exiting")
        display.print_help()
        return
        
    # Initialize with current time text BEFORE starting the thread
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(f"Setting initial time to: {current_time}")
    display.set_text(current_time)
    
    # Configure display properties
    print("Configuring display...")
    display.set_mode("static")
    display.set_font_size(16)
    display.set_color((0, 191, 255))  # Deep Sky Blue
    
    # Start the display
    print("Starting display thread...")
    start_result = display.start()
    print(f"Start result: {start_result}")
    
    if not start_result:
        print("Failed to start display, exiting")
        return
    
    print("Display thread started successfully")
    
    # Setup signal handler for clean exit
    def signal_handler(sig, frame):
        print("Exiting...")
        display.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("Entering main loop...")
        while True:
            # Get current time
            now = datetime.now()
            time_str = now.strftime("%H:%M:%S")
            
            # Update display text
            print(f"Updating time to: {time_str}")
            display.set_text(time_str)
            
            # Wait before updating again
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        print("Stopping display...")
        display.stop()
        print("Display stopped")
        
if __name__ == "__main__":
    main()