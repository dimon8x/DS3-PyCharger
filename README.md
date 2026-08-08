# DS3-PyCharger
Raspberry Pi Pico charging board for DualShock 3 with any USB power device

Вдохновлено
https://github.com/radu-gs/DS3PicoCharger


# Как создать

1. Прошить CircuitPython на Pi Pico, RP 2040 Zero или подобную. Получим съемный диск CIRCUITPY.

+ Pico by Raspberry Pi
https://circuitpython.org/board/raspberry_pi_pico/

+ RP2040-Zero by Waveshare
https://circuitpython.org/board/waveshare_rp2040_zero/

2. Скопировать boot.py и code.py в корень CIRCUITPY
3. Библиотеку neopixel.mpy (и её зависимость adafruit_pixelbuf, если используется отдельно) копируем в папку lib на диск CIRCUITPY из Adafruit CircuitPython Library Bundle, версию под вашу прошивку CircuitPython.
https://circuitpython.org/libraries

# Примечание

+ Оранжевый - режим ожидания
+ Красный мигающий - идет зарядка
+ Синий мигающий - почти заряжен
+ Зеленый - полностью заряжен

GPIO пины можно выбрать другие, изменив их в коде.
