import time
import board
import neopixel
import usb.core
import usb_host
import microcontroller

microcontroller.cpu.frequency = 120000000

# Onboard NeoPixel (WS2812) on GPIO16 of the RP2040-Zero.
pixel = neopixel.NeoPixel(board.GP16, 1, brightness=0.3, auto_write=True)
pixel.fill((255, 50, 0))  # orange

try:
    # change D+/D- pins if needed, D- needs to be the next pin after D+
    usb_host.Port(board.GP0, board.GP1)

    # Give the host time to detect an already-connected device right after
    # boot - without this delay, usb.core.find() may return None for the
    # first second or so even though charging over VBUS is already
    # happening.
    time.sleep(1.5)

    BLINK_PERIOD = 0.5     # toggle the LED every 500ms -> full blink cycle = 1s
    CHECK_PERIOD = 0.5     # how often to re-check whether the controller is present
    BATTERY_PERIOD = 2.0   # how often to poll the DS3 battery level

    # The DS3 battery level lives in byte offset 30 of the input HID report
    # (report ID 0x01). This logic is taken from the Linux driver
    # (hid-sony.c, sixaxis_parse_report function):
    #   0..5   -> percentage via the table below (running on battery, not charging)
    #   0xEE   -> 100%, but still charging (DS3 doesn't report a fractional %
    #             while topping off)
    #   0xEF   -> 100%, charging finished
    DS3_BATTERY_TABLE = (0, 1, 25, 50, 75, 100)
    DS3_BATTERY_OFFSET = 30
    DS3_INPUT_REPORT_LEN = 49

    def ds3_wake_operational(dev):
        # Until this feature report is read, the DS3 won't start sending
        # up-to-date data (including battery level) - that's how the
        # SIXAXIS protocol works.
        buf = bytearray(17)
        dev.ctrl_transfer(0xA1, 0x01, 0x03F2, 0x00, buf)

    def ds3_read_battery(dev):
        """Return (percent, done) or None if the read failed.
        done=True only when charging is genuinely finished (byte 0xEF).
        When the byte is 0xEE, the DS3 already reports "100%" but is
        physically still topping off."""
        buf = bytearray(DS3_INPUT_REPORT_LEN)
        n = dev.ctrl_transfer(0xA1, 0x01, 0x0101, 0x00, buf)
        if n <= DS3_BATTERY_OFFSET:
            return None
        raw = buf[DS3_BATTERY_OFFSET]
        if raw >= 0xEE:
            return (100, bool(raw & 0x01))
        idx = raw if raw <= 5 else 5
        return (DS3_BATTERY_TABLE[idx], False)

    con = None
    blink_state = False
    battery_pct = None
    battery_full = False
    operational_ready = False

    now = time.monotonic()
    last_blink = now
    last_check = now
    last_battery_check = now

    while True:
        now = time.monotonic()

        # Re-check whether the controller is present, without blocking the blink
        if now - last_check >= CHECK_PERIOD:
            last_check = now
            new_con = usb.core.find()
            if new_con is None:
                if con is not None:
                    # device just disconnected - reset state
                    operational_ready = False
                    battery_pct = None
                    battery_full = False
                con = None
            else:
                if con is None:
                    # device just connected (including a reconnect) - reset
                    # state so the charging status gets re-read from scratch
                    operational_ready = False
                    battery_pct = None
                    battery_full = False
                con = new_con

        if con != None:
            if not operational_ready:
                try:
                    ds3_wake_operational(con)
                    operational_ready = True
                except Exception:
                    pass  # try again on the next cycle

            if operational_ready and (now - last_battery_check >= BATTERY_PERIOD):
                last_battery_check = now
                try:
                    result = ds3_read_battery(con)
                    if result is not None:
                        battery_pct, battery_full = result
                    else:
                        battery_pct, battery_full = None, False
                except Exception:
                    battery_pct, battery_full = None, False

            if battery_pct == 100 and battery_full:
                # Charging genuinely finished (byte 0xEF) - solid green
                pixel.fill((0, 255, 0))
                blink_state = False
            elif battery_pct == 100 and not battery_full:
                # DS3 already reports 100%, but is physically still topping
                # off (byte 0xEE) - blinking blue
                if now - last_blink >= BLINK_PERIOD:
                    last_blink = now
                    blink_state = not blink_state
                    pixel.fill((0, 0, 255) if blink_state else (0, 0, 0))
            else:
                # Charging (< 100%) - blinking red every 500ms
                if now - last_blink >= BLINK_PERIOD:
                    last_blink = now
                    blink_state = not blink_state
                    pixel.fill((255, 0, 0) if blink_state else (0, 0, 0))
        else:
            # No device connected - solid orange (powered/idle)
            pixel.fill((255, 50, 0))
            blink_state = False

        time.sleep(0.02)

except Exception as e:
    # If the script crashed - light the LED purple for diagnostics and
    # keep re-printing the error every second, so it's visible no matter
    # when Thonny connects (a one-time print can scroll past unseen).
    error_text = str(e)
    pixel.fill((128, 0, 128))
    while True:
        print("ERROR:", error_text)
        time.sleep(1)
