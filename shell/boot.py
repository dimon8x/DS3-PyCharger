import board
import neopixel
import usb_cdc

# Light the onboard NeoPixel (WS2812, GPIO16 on the RP2040-Zero) orange as
# early as possible after power-up - same color code.py uses for the
# "idle" state.
pixel = neopixel.NeoPixel(board.GP16, 1, brightness=0.3, auto_write=True)
pixel.fill((255, 50, 0))

usb_cdc.disable()
