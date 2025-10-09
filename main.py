from gpio import RgbLed
from gpio import UltrasonicRanging
from gpio import TouchSwitch
import threading
import time

color = 0x000000
touched = False
distance = 0

ultrasonic_ranging = UltrasonicRanging
rgb_led = RgbLed
touch_switch = TouchSwitch

stop_event = threading.Event()

def read_distance():
	global distance

	while not stop_event.is_set():
		distance = ultrasonic_ranging.distance()
		print(f"Distance = {distance}")

		time.sleep(0.5)

def set_color():
	global color

	while not stop_event.is_set():
		rgb_led.set_color(color)
		time.sleep(0.5)

def is_touched():
	global touched

	while not stop_event.is_set():
		touched = touch_switch.is_touched()

		if touched:
			print("Resetting the session.")

		time.sleep(0.1)

if __name__ == "__main__":
	ultrasonic_ranging_thread = threading.Thread(target=read_distance, name="ultrasonic_ranging_thread", args=(distance))
	rgb_led_thread = threading.Thread(target=set_color, name="rgb_led_thread", args=(color))
	touch_switch_thread = threading.Thread(target=is_touched, name="touch_switch_thread", args=(touched))

	try:
		while True:
			input_val = int(input("Choose color -\n[1] for Red\n[2] = Green\n"))
			
			if input_val == 1:
				color = 0xFF0000
			elif input_val == 2:
				color = 0x00FF00
				
	except KeyboardInterrupt:
		stop_event.set()

		ultrasonic_ranging_thread.join()
		rgb_led_thread.join()
		touch_switch_thread.join()

		rgb_led.destroy()
		ultrasonic_ranging.destroy()
		touch_switch.destroy()
