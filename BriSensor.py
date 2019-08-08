import time
import smbus
import RPi.GPIO as GPIO

bus = smbus.SMBus(3)                                            # i2c bus number (NOTE Default value: 1)
currbrightness = 0
targetbri = 0

while True:
    # Create a list of brightness values and afterwards calculate the average
    luxlist = []
    for counter in range(10):  # Refresh time 0,5*10=5s
        time.sleep(0.5)        # sampling freq. 2Hz

        # Read current brightness from memory
        with open("/sys/class/backlight/rpi_backlight/brightness", "r") as x:
            currbrightness = int(x.read())

        # Read brightness values from GPIO sensor
        bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
        data = bus.read_i2c_block_data(0x39, 0x0C | 0x80, 2)
        currluxvalue = data[1] * 256 + data[0]                    # current lux value from sensor
        luxlist.append(currluxvalue)                              # append current lux value to list

    # Calculate the average of brightness
    luxaverage = int(sum(luxlist) / len(luxlist))
    print("Measured lux values: ", luxlist)
    print("Lux average: ", luxaverage)

    # Calculate target brightness value
    if luxaverage in range(0, 5):
        targetbri = 100                                 # 1/5 brightness level
    elif luxaverage in range(5, 20):
        targetbri = 140                                 # 2/5 brightness level
    elif luxaverage in range(20, 100):
        targetbri = 180                                 # 3/5 brightness level
    elif luxaverage in range(100, 200):
        targetbri = 210                                 # 4/5 brightness level
    elif luxaverage > 200:
        targetbri = 255                                 # 5/5 brightness level

    # Gradually adjust the brightness
    if currbrightness >= targetbri:                     # Set adaptation step (decreasing / increasing)
        step = -1
    else:
        step = +1
    for currbrightness in range(currbrightness, targetbri, step):
        with open("/sys/class/backlight/rpi_backlight/brightness", "w") as f:
            f.write(str(currbrightness))
            print("Adjusting brightness... ", currbrightness)
            time.sleep(0.02)                            # transition speed

    # Setting up GPIO - NOTE Select in OAPro day/night settings "GPIO Pin":21 (PIN 40 RPi)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(40, GPIO.OUT)
    GPIO.setwarnings(False)                             # disable GPIO warnings
    print("Night mode (bool): ", GPIO.input(40))

    # Avoid constantly switching between DAY / NIGHT    # (GPIO True=NIGHT, False=DAY)
    if GPIO.input(40) is True and luxaverage <= 200:    # if already in "Night mode" and it's not day yet
        GPIO.output(40, True)                           # stay in "Night mode"
    else:
        # Set DAY/NIGHT
        if luxaverage in range(0, 20):                  # if it's night
            GPIO.output(40, True)                       # set "Night mode"
        else:                                           # else
            GPIO.output(40, False)                      # set "Day mode"
