import RPi.GPIO as GPIO
import time

# class template
class Device:
    def __init__(self):
        pass

    def setup(self):
        pass

    def destroy(self):
        pass

class RgbLed(Device):
    RED_CHANNEL = 11
    GREEN_CHANNEL = 12
    BLUE_CHANNEL = 13

    RED_PIN = None
    GREEN_PIN = None
    BLUE_PIN = None

    RED_COLOR = 0xFF0000
    GREEN_COLOR = 0x00FF00
    BLUE_COLOR = 0x0000FF

    def __init__(self):
        self.setup()

    def setup(self):
        # numbers of GPIOs by physical location
        GPIO.setmode(GPIO.BOARD)

        # set pins mode to output
        GPIO.setup(self.RED_CHANNEL, GPIO.OUT)
        GPIO.setup(self.GREEN_CHANNEL, GPIO.OUT)
        GPIO.setup(self.BLUE_CHANNEL, GPIO.OUT)

        # set pins to high(+3.3v) to off LED
        GPIO.output(self.RED_CHANNEL, GPIO.HIGH)
        GPIO.output(self.GREEN_CHANNEL, GPIO.HIGH)
        GPIO.output(self.BLUE_CHANNEL, GPIO.HIGH)

        # set frequency to 2KHz
        self.RED_PIN = GPIO.PWM(self.RED_CHANNEL, 2000)
        self.GREEN_PIN = GPIO.PWM(self.GREEN_CHANNEL, 1999)
        self.BLUE_PIN = GPIO.PWM(self.BLUE_CHANNEL, 5000)

        # initial duty cycle = 0 (LED off)
        self.RED_PIN.start(0)
        self.GREEN_PIN.start(0)
        self.BLUE_PIN.start(0)

    def map(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def set_color(self, color):
        r_val = (color & 0xff0000) >> 16
        g_val = (color & 0x00ff00) >> 8
        b_val = (color & 0x0000ff) >> 0
            
        r_val = self.map(r_val, 0, 255, 0, 100)
        g_val = self.map(g_val, 0, 255, 0, 100)
        b_val = self.map(b_val, 0, 255, 0, 100)

        self.RED_PIN.ChangeDutyCycle(r_val)
        self.GREEN_PIN.ChangeDutyCycle(g_val)
        self.BLUE_PIN.ChangeDutyCycle(b_val)

    def destroy(self):
        # stop duty cycles
        self.RED_PIN.stop()
        self.GREEN_PIN.stop()
        self.BLUE_PIN.stop()

        # clean up channels
        GPIO.cleanup(self.RED_CHANNEL)
        GPIO.cleanup(self.GREEN_CHANNEL)
        GPIO.cleanup(self.BLUE_CHANNEL)

class UltrasonicRanging(Device):
    TRIG_CHANNEL = 15
    ECHO_CHANNEL = 16

    def __init__(self):
        self.setup()

    def setup(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.TRIG_CHANNEL, GPIO.OUT)
        GPIO.setup(self.ECHO_CHANNEL, GPIO.IN)

    # distance = time * velocity_of_sound (340 meters per second) / 2 (in meters)
    def distance(self):
        GPIO.output(self.TRIG_CHANNEL, 0)
        time.sleep(0.000002)

        GPIO.output(self.TRIG_CHANNEL, 1)
        time.sleep(0.00001)
        GPIO.output(self.TRIG_CHANNEL, 0)

        while GPIO.input(self.ECHO_CHANNEL) == 0:
            a = 0
        time1 = time.time()
        while GPIO.input(self.ECHO_CHANNEL) == 1:
            a = 1
        time2 = time.time()

        duration = time2 - time1
        return duration * 340 / 2 * 100

    def destroy(self):
        GPIO.cleanup(self.TRIG_CHANNEL)
        GPIO.cleanup(self.ECHO_CHANNEL)

class TouchSwitch(Device):
    TOUCH_CHANNEL = 18

    def __init__(self):
        self.setup()

    def setup(self):
        GPIO.setmode(GPIO.BOARD)
        # Set TouchPin's mode as input, and pull up to high level (3.3V)
        GPIO.setup(self.TOUCH_CHANNEL, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def is_touched(self):
        state = GPIO.input(self.TOUCH_CHANNEL)
        return state == GPIO.HIGH

    def destroy(self):
        GPIO.cleanup(self.TOUCH_CHANNEL)