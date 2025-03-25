#!/usr/bin/env python
from samplebase import SampleBase
from PIL import Image
import sys
import time

class GifPlayer(SampleBase):
    def __init__(self, *args, **kwargs):
        super(GifPlayer, self).__init__(*args, **kwargs)
        self.parser.add_argument("--image", help="The image to display", default="test.gif")
        self.parser.add_argument("--framerate", help="Framerate fraction adjustment", default=10, type=int)

    def run(self):
        image_file = self.args.image
        
        try:
            gif = Image.open(image_file)
        except Exception as e:
            print(f"Error opening image file: {e}")
            sys.exit("Unable to open the provided image")
            
        try:
            num_frames = gif.n_frames
        except Exception:
            sys.exit("Provided image is not a gif")

        # Preprocess the gif frames into canvases to improve playback performance
        canvases = []
        print("Preprocessing gif, this may take a moment depending on the size of the gif...")
        for frame_index in range(0, num_frames):
            gif.seek(frame_index)
            # must copy the frame out of the gif, since thumbnail() modifies the image in-place
            frame = gif.copy()
            frame.thumbnail((self.matrix.width, self.matrix.height), Image.LANCZOS)  # ANTIALIAS is deprecated in newer PIL versions
            canvas = self.matrix.CreateFrameCanvas()
            canvas.SetImage(frame.convert("RGB"))
            canvases.append(canvas)
        
        # Close the gif file to save memory now that we have copied out all of the frames
        gif.close()

        print("Completed Preprocessing, displaying gif")
        print("Press CTRL-C to stop.")

        # Infinitely loop through the gif
        cur_frame = 0
        while True:
            self.matrix.SwapOnVSync(canvases[cur_frame], framerate_fraction=self.args.framerate)
            if cur_frame == num_frames - 1:
                cur_frame = 0
            else:
                cur_frame += 1

# Main function
if __name__ == "__main__":
    gif_player = GifPlayer()
    if not gif_player.process():
        gif_player.print_help()