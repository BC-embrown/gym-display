#!/usr/bin/env python3
import time
import os
import threading
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from evdev import InputDevice, categorize, ecodes
import RPi.GPIO as GPIO

class DirectTestCounter:
    def __init__(self, logo_path="logo.png", debounce_time=0.5):
        self.count = 0
        self.logo_path = logo_path
        self.debounce_time = debounce_time
        self.last_hit_time = 0
        self.mode = "beam"
        self.flashing = False
        self.input_buffer = ""
        self.last_flash_time = 0
        self.flash_interval = 0.5

        # Storing data for strength setting
        self.total_strength_value = 0
        self.current_strength_value = "" # converted to int when they add
        self.reset_counter = 0

        self.beam_pins = [26, 16, 5, 6]
        GPIO.setmode(GPIO.BCM)
        for pin in self.beam_pins:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.options = RGBMatrixOptions()
        self.options.rows = 64
        self.options.cols = 64
        self.options.chain_length = 1
        self.options.parallel = 1
        self.options.hardware_mapping = 'regular'
        self.options.gpio_slowdown = 5
        self.options.brightness = 100
        self.options.disable_hardware_pulsing = True

        self.matrix = RGBMatrix(options=self.options)
        self.canvas = self.matrix.CreateFrameCanvas()

        self.font = None
        self.font_size = 56
        self.text_color = (214, 160, 255)
        self.font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        try:
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
                '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
            ]
            for path in font_paths:
                if os.path.exists(path):
                    self.font_path = path
                    self.font = ImageFont.truetype(self.font_path, self.font_size)
                    print(f"Loaded font: {path}")
                    break
        except Exception as e:
            print(f"Error loading font: {e}")

        if self.font is None:
            print("Using default font")
            self.font = ImageFont.load_default()

    def init(self):
        print("Starting test hit counter...")
        init_load_wait_time = 2
        if os.path.exists(self.logo_path):
            print(f"Displaying logo for {init_load_wait_time} seconds: {self.logo_path}")
            self.display_image(self.logo_path, init_load_wait_time)
        else:
            print(f"Logo file not found: {self.logo_path}")
        self.display_number(0)

    def run(self):
        try:
            self.init()
            kb_thread = threading.Thread(target=self.check_for_keyboard_input)
            kb_thread.daemon = True
            kb_thread.start()
            print("Counter started.")

            while True:
                current_time = time.time()
                if current_time - self.last_hit_time > self.debounce_time:
                    for pin in self.beam_pins:
                        if GPIO.input(pin) == GPIO.LOW:
                            self.increment_counter()
                            break
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("Program interrupted")
        finally:
            self.cleanup()

    def cleanup(self):
        print(f"Final count: {self.count}")
        self.canvas.Clear()
        self.matrix.SwapOnVSync(self.canvas)
        GPIO.cleanup()

    def check_for_keyboard_input(self):
        device_path = '/dev/input/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.3:1.0-event-kbd'
        try:
            dev = InputDevice(device_path)
            print(f"Listening for keypresses from: {device_path}")
        except Exception as e:
            print(f"Failed to open device at {device_path}: {e}")
            return
        for event in dev.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                if key_event.keystate == key_event.key_down:
                    keycode = key_event.keycode
                    print(f"Key pressed: {keycode}")
                    if self.mode == "beam":
                        self.beam_keyboard_input_check(keycode)
                    elif self.mode == "strength":
                        self.strength_keyboard_input_check(keycode)

    def change_mode(self):
        # if you dont want it to show the logo inbetween changing modes comment the lines below
        logo_show_time = 1 
        self.display_image(self.logo_path, logo_show_time)
        
        if self.mode == "beam":
            self.mode = "strength"
            self.display_strength_value()
        elif self.mode == "strength":
            self.mode = "beam"
            self.display_beam_value()

    ###########################################################################

    ########################### STRENGTH MODE #################################

    ###########################################################################

    def strength_keyboard_input_check(self, keycode):
        if keycode in ('KEY_EQUAL', 'KEY_KPPLUS'):
            self.strength_equals_pressed()
        elif keycode in ('KEY_SLASH', 'KEY_KPSLASH'): # This is the reset command for the strength mode, press twice to reset the value to 0 (bc you obv need to the 0 key for value input)
            self.strength_reset_input()
        elif keycode in ('KEY_0', 'KEY_KP0'): # This is gross
            self.current_strength_value += "0"
        elif keycode in ('KEY_1', 'KEY_KP1'):
            self.current_strength_value += "1"
        elif keycode in ('KEY_2', 'KEY_KP2'):
            self.current_strength_value += "2"
        elif keycode in ('KEY_3', 'KEY_KP3'):
            self.current_strength_value += "3"
        elif keycode in ('KEY_4', 'KEY_KP4'):
            self.current_strength_value += "4"
        elif keycode in ('KEY_5', 'KEY_KP5'):
            self.current_strength_value += "5"
        elif keycode in ('KEY_6', 'KEY_KP6'):
            self.current_strength_value += "6"
        elif keycode in ('KEY_7', 'KEY_KP7'):
            self.current_strength_value += "7"
        elif keycode in ('KEY_8', 'KEY_KP8'):
            self.current_strength_value += "8"
        elif keycode in ('KEY_9', 'KEY_KP9'):
            self.current_strength_value += "9"
        elif keycode in ('KEY_NUMLOCK', 'KEY_KPNUMLOCK'):
            self.change_mode()

    def strength_equals_pressed(self):
        if self.current_strength_value == "":
            # ignore the command bc they've not assigned a value yet
            return
        try:
            # Wrapping this in a try catch, it shouldn't ever fail, but just incase, I don't trust casting user input, even when I control the inputs 
            current_strength_val = int(self.current_strength_value)
            self.total_strength_value += current_strength_val
            self.display_strength_value()
        except:
            pass

    def strength_reset_input(self):
        self.reset_counter += 1
        if self.reset_counter >= 2:
            self.reset_strength_mode()    
            self.display_number("Stregth\nmode\nreset")
            time.sleep(1)
            self.display_number("0")

    def reset_strength_mode(self):
        self.reset_counter = 0
        self.total_strength_value = 0
        self.current_strength_value = ""

    def display_strength_value(self):
        self.display_number(f"{self.total_strength_value}kg")


    ###########################################################################

    ########################### BEAM MODE #################################

    ###########################################################################

    def beam_keyboard_input_check(self, keycode):
        if keycode == 'KEY_MINUS':
            self.decrement_counter()
        elif keycode in ('KEY_EQUAL', 'KEY_KPPLUS'):
            self.increment_counter()
        elif keycode in ('KEY_SLASH', 'KEY_KPSLASH'):
            self.display_number("/")
        elif keycode in ('KEY_NUMLOCK', 'KEY_KPNUMLOCK'):
            self.change_mode()
        elif keycode in ('KEY_0', 'KEY_KP0'):
            self.count = 0
            self.display_beam_value()

    def increment_counter(self):
        current_time = time.time()
        if current_time - self.last_hit_time > self.debounce_time:
            self.count += 1
            self.last_hit_time = current_time
            print(f"Increment! Count: {self.count}")
            self.display_beam_value()

    def decrement_counter(self):
        current_time = time.time()
        if current_time - self.last_hit_time > self.debounce_time:
            self.count -= 1
            self.last_hit_time = current_time
            print(f"Decrement! Count: {self.count}")
            self.display_beam_value()

    def display_beam_value(self):
        self.display_number(self.count)

    def display_image(self, image_path, duration=None):
        try:
            if not os.path.exists(image_path):
                print(f"Image not found: {image_path}")
                return False

            img = Image.open(image_path).convert('RGB')
            img.thumbnail((self.matrix.width, self.matrix.height), Image.LANCZOS)

            width, height = img.size
            x_offset = (self.matrix.width - width) // 2
            y_offset = (self.matrix.height - height) // 2

            self.canvas.Clear()
            self.canvas.SetImage(img, x_offset, y_offset)
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

        # Try largest font, reduce until it fits
        max_font_size = 60
        min_font_size = 10
        font_size = max_font_size

        while font_size >= min_font_size:
            font = ImageFont.truetype(self.font_path, font_size)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            if text_width <= self.matrix.width and text_height <= self.matrix.height:
                break
            font_size -= 1

        x_position = (self.matrix.width - text_width) // 2
        y_position = (self.matrix.height - text_height) // 2 - 5  # Slight upward nudge
        if y_position < 0:
            y_position = 0

        print(f"Auto font size: {font_size}, Text: {text}, Pos: ({x_position}, {y_position})")

        draw.text((x_position, y_position), text, font=font, fill=self.text_color)
        self.canvas.SetImage(img)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)


if __name__ == "__main__":
    counter = DirectTestCounter()
    counter.run()
