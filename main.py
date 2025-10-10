from gpio import RgbLed
from gpio import UltrasonicRanging
from gpio import TouchSwitch
from gpio import Button
import threading
import time

color = 0x000000
touched = False
distance = 0

def read_distance():
	global distance
	global ultrasonic_ranging

	while not stop_event.is_set():
		distance = ultrasonic_ranging.distance()
		time.sleep(0.5)

def set_color():
	global color
	global rgb_led
		
	while not stop_event.is_set():
		if rgb_led.get_color != color:
			rgb_led.set_color(color)
			time.sleep(0.5)

def is_touched():
	global touched
	global touch_switch

	while not stop_event.is_set():
		touched = touch_switch.is_touched()

		if touched:
			print("Touched.")
		else:
			print("Not-touched")
			
		time.sleep(1)
		
def detect(state):
	global detected
	global distance
	
	detected = state
	print(f"Button detection - {detected}")
	print(f"Distance = {distance}")
	
ultrasonic_ranging = UltrasonicRanging()
rgb_led = RgbLed()
touch_switch = TouchSwitch()
button = Button(detect)

stop_event = threading.Event()

if __name__ == "__main__":
	ultrasonic_ranging_thread = threading.Thread(target=read_distance, name="ultrasonic_ranging_thread")
	rgb_led_thread = threading.Thread(target=set_color, name="rgb_led_thread")
	#touch_switch_thread = threading.Thread(target=is_touched, name="touch_switch_thread")

	rgb_led_thread.start()
	#touch_switch_thread.start()
	ultrasonic_ranging_thread.start()

	try:
		while True:
			input_val = int(input("Choose color\n[1] = Red\n[2] = Green\n"))
			
			if input_val == 1:
				color = 0xFF0000
			elif input_val == 2:
				color = 0x00FF00
				
	except KeyboardInterrupt:
		stop_event.set()

		ultrasonic_ranging_thread.join()
		rgb_led_thread.join()
	#	touch_switch_thread.join()

		rgb_led.destroy()
		ultrasonic_ranging.destroy()
	#	touch_switch.destroy()
