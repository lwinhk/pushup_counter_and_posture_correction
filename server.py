"""
Server is the program which receives video frames from the clients and processes them for the pose estimation and posture correction. Finally, it will conclude the session and send to cloud server for data storage, analytics and presentation.
"""

from poses import MediaPipe
import socket, select, cv2, numpy as np
from cvzone.PoseModule import PoseDetector
import os
import time
from bigquery import BigQuery
from datetime import datetime
import math
from gpio import RgbLed
from gpio import UltrasonicRanging
from gpio import Button
import threading

"""
Begin environment preparation
"""
# set default values for server and client network configuration
# listen on all interfaces
HOST = "0.0.0.0"   
PORT1 = 5005
PORT2 = 5006

# server and client network configuration from system environment variables
server_ip = os.getenv('server_ip')
if server_ip:
    HOST = server_ip
client1_port = os.getenv('client1_port')
if client1_port:
    PORT1 = int(client1_port)
client2_port = os.getenv('client2_port')
if client2_port:
    PORT2 = int(client2_port)

# big query credentials from system environment variables
API_KEY = ""
gc_api_key = os.environ.get('google_cloud_api_key')
if gc_api_key:
    API_KEY = gc_api_key
CLIENT_ID = ""
gc_client_id = os.environ.get('google_cloud_client_id')
if gc_client_id:
    CLIENT_ID = gc_client_id
CLIENT_SECRET = ""
gc_client_secret = os.environ.get('google_cloud_client_secret')
if gc_client_secret:
    CLIENT_SECRET = gc_client_secret

# big query session data
session_data = None
user_id = 0
count = 0
correct_count = 0
incorrect_count = 0

project_id = "pushup-counter-aut"
dataset_id = "pushup_dataset"
table_id = "pushup_sessions"
big_query = BigQuery(project_id, dataset_id, table_id, API_KEY)

# exercise data
DOWN = 0
UP = 1
direction = DOWN

# sensor data
color = 0x000000
RED_COLOR = 0xFF0000
GREEN_COLOR = 0x00FF00
touched = False
MAX_DISTANCE = 1600
MIN_DISTANCE = 0
distance = 0

ultrasonic_ranging = None
rgb_led = None
button = None

stop_event = None

"""
End environment preparation
"""

"""
Begin functions
"""

# big data functions
def begin_session():
    global user_id, session_data
    global count, incorrect_count, correct_count
    
    session_data = None
    user_id = 0
    count = 0
    incorrect_count = 0
    correct_count = 0

    print("Begin new session...")

    while True:
        user_id = input("Choose user ID [1, 2, 3].\n")

        try:
            user_id = int(user_id)
    
            if user_id not in [1, 2, 3]:
                print("Invalid user ID. Please select again.")
            else:
                break
        except:
            break

def end_session():
    global count, incorrect_count, correct_count
    
    current_datetime = datetime.now()
    # session id is to be auto-increment in big query
    session_id = 0
    incorrect_count = math.ceil(incorrect_count)
    correct_count = math.floor(correct_count)

    session_data = {
        "id": session_id,
        "user_id": user_id,
        "counter": int(count),
        "incorrect_counter": int(incorrect_count),
        "correct_counter": int(correct_count),
        "timestamp": int(time.time()),                                              # second
        #"incorrect_counter_perc": f"{(incorrect_count/count*100):.2f}",             # NUMERIC as string
        #"correct_counter_perc":   f"{(correct_count/count*100):.2f}",               # NUMERIC as string
        "incorrect_counter_perc": int(incorrect_count/count*100),
        "correct_counter_perc": int(correct_count/count*100),
        "created_at": current_datetime.strftime("%Y-%m-%d %H:%M:%S")                # DATETIME literal
    }

    print("Ending session...")
    big_query.simple_send(session_data)
    print("Session data is sent to cloud")
    # restart the session
    begin_session()


# image processing functions
def speak(text):
    pass

def decode_jpeg_to_bgr(data: bytes):
    if not data:
        return None
    arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    # frame = cv2.imdecode(arr)
    # frame = np.zeros((300, 300, 3), dtype=np.uint8)
    return frame

class Position:
    def __init__(self):
        self.x = 0
        self.y = 0

def is_person_present():
    global distance, MAX_DISTANCE, MIN_DISTANCE

    # user is present in front of ultrasonic sensor and user_id is set
    return distance >= MIN_DISTANCE and distance <= MAX_DISTANCE and user_id > 0

def is_posture_correct_2(leftShoulder, leftHip, leftKnee, rightShoulder, rightHip, rightKnee):
    return True

def is_posture_correct(leftWrist, leftShoulder, rightWrist, rightShoulder):
    if leftWrist.x > leftShoulder.x and rightWrist.x < rightShoulder.x:
        return True

    return False

def angles(frame, leftShoulderLandMark, leftElbowLandMark, leftWristLandMark, rightShoulderLandMark, rightElbowLandMark, rightWristLandMark, drawPoints):
    global count, correct_count, incorrect_count
    global direction
    global DOWN
    global UP

    leftShoulder = Position()
    leftElbow = Position()
    leftWrist = Position()
    #leftHip = Position()
    #leftKnee = Position()
    rightShoulder = Position()
    rightElbow = Position()
    rightWrist = Position()
    #rightHip = Position()
    #rightKnee = Position()

    leftShoulder.x, leftShoulder.y = leftShoulderLandMark[0:2]
    leftElbow.x, leftElbow.y = leftElbowLandMark[0:2]
    leftWrist.x, leftWrist.y = leftWristLandMark[0:2]
    #leftHip.x, leftHip.y = leftHipLandMark[0:2]
    #leftKnee.x, leftKnee.y = leftKneeLandMark[0:2]
    rightShoulder.x, rightShoulder.y = rightShoulderLandMark[0:2]
    rightElbow.x, rightElbow.y = rightElbowLandMark[0:2]
    rightWrist.x, rightWrist.y = rightWristLandMark[0:2]
    #rightHip.x, rightHip.y = rightHipLandMark[0:2]
    #rightKnee.x, rightKnee.y = rightKneeLandMark[0:2]

    if drawPoints == True:
        cv2.circle(frame, (leftShoulder.x, leftShoulder.y), 10, (0, 255, 0), 5)
        cv2.circle(frame, (leftElbow.x, leftElbow.y), 10, (0, 255, 0), 5)
        cv2.circle(frame, (leftWrist.x, leftWrist.y), 10, (0, 255, 0), 5)
        cv2.circle(frame, (rightShoulder.x, rightShoulder.y), 10, (0, 255, 0), 5)
        cv2.circle(frame, (rightElbow.x, rightElbow.y), 10, (0, 255, 0), 5)
        cv2.circle(frame, (rightWrist.x, rightWrist.y), 10, (0, 255, 0), 5)

    #posture_correct = is_posture_correct_2(leftShoulder, leftHip, leftKnee, rightShoulder, rightHip, rightKnee)
    posture_correct = is_posture_correct(leftWrist, leftShoulder, rightWrist, rightShoulder)

    if posture_correct:
        if rgb_led.get_color() != GREEN_COLOR:
            rgb_led.set_color(GREEN_COLOR)
    else:
        if rgb_led.get_color() != RED_COLOR:
            rgb_led.set_color(RED_COLOR)

    leftElbowAngle = math.degrees(math.atan2(leftWrist.y - leftElbow.y, leftWrist.x - leftElbow.x) - math.atan2(leftShoulder.y - leftElbow.y, leftShoulder.x - leftElbow.x))
    rightElbowAngle = math.degrees(math.atan2(rightWrist.y - rightElbow.y, rightWrist.x - rightElbow.y) - math.atan2(rightShoulder.y - rightElbow.y, rightShoulder.x - rightElbow.x))

    # leftElbowAngle = int(np.interp(leftElbowAngle, [-30, 170], [170, -30]))
    # rightElbowAngle = int(np.interp(rightElbowAngle, [40, 170], [170, 40]))

    #print(leftElbowAngle, rightElbowAngle)

    #leftElbowAngle = int(np.interp(leftElbowAngle, [-70, 180], [100, 0]))
    #leftElbowAngle = int(np.interp(leftElbowAngle, [-30, 180], [100, 0]))
    #rightElbowAngle = int(np.interp(rightElbowAngle, [135, 190], [100, 0]))
    #rightElbowAngle = int(np.interp(rightElbowAngle, [34, 173], [100, 0]))

    #print(leftElbowAngle, rightElbowAngle)

    #if leftElbowAngle >= 70 and rightElbowAngle >= 70:
    #    if direction == DOWN:
    #        count += 0.5
    #        direction = UP

    #        if posture_correct:
    #            correct_count += 0.5
    #        else:
    #            incorrect_count += 0.5
    #if leftElbowAngle <= 70 and rightElbowAngle <= 70:
    #    if direction == UP:
    #        count += 0.5
    #        direction = DOWN

    #        if posture_correct:
    #            correct_count += 0.5
    #        else:
    #            incorrect_count += 0.5

    leftElbowAngle = 0
    a = np.array([leftShoulder.x, leftShoulder.y])
    b = np.array([leftElbow.x, leftElbow.y])
    c = np.array([leftWrist.x, leftWrist.y])

    radians = np.arctan2(c[1] - b[1], c[0] - b [0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle

    leftElbowAngle = angle

    #if direction == DOWN:
    #    print(f"angle = {leftElbowAngle}, direction=down, count={count}, correct_count={correct_count}, incorrect_count={incorrect_count}")
    #else:
    #    print(f"angle = {leftElbowAngle}, direction=up, count={count}, correct_count={correct_count}, incorrect_count={incorrect_count}")

    if leftElbowAngle > 160 and direction == DOWN:
        #print("INCREASE")
        direction = UP
        count += 1

        if posture_correct:
            correct_count += 1
        else:
            incorrect_count += 1

    if leftElbowAngle > 160:
        direction = UP

    if leftElbowAngle < 110 and direction == UP:
        direction= DOWN

    #cv2.rectangle(frame, (0, 0), (120, 120), (255, 0, 0), -1)
    #cv2.putText(frame, str(int(count)), (20, 70), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1.6, (0, 0, 255), 7)

# sensors functions (GPIO functions)

def read_distance():
	global distance
	global ultrasonic_ranging
	global stop_event

	while not stop_event.is_set():
		distance = ultrasonic_ranging.distance()
		time.sleep(0.5)

def set_color():
	global color
	global rgb_led
	global stop_event
		
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
	print(f"Push button is pressed - {state}")
	if state == 1:
		end_session()
    
def main():
    global ultrasonic_ranging
    global rgb_led
    global button
    global stop_event
    global count
    
    begin_session()

    ultrasonic_ranging = UltrasonicRanging()
    rgb_led = RgbLed()
    button = Button(detect)

    stop_event = threading.Event()

    ultrasonic_ranging_thread = threading.Thread(target=read_distance, name="ultrasonic_ranging_thread")
    rgb_led_thread = threading.Thread(target=set_color, name="rgb_led_thread")
    rgb_led_thread.start()
    ultrasonic_ranging_thread.start()

    sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock1.bind((HOST, PORT1))
    sock2.bind((HOST, PORT2))
    sock1.setblocking(False)
    sock2.setblocking(False)

    pd1 = PoseDetector(trackCon=0.70, detectionCon=0.70)
    pd2 = PoseDetector(trackCon=0.70, detectionCon=0.70)

    last_frame1 = None
    last_frame2 = None
    win = "Pushup Counter Server Program"
    cv2.namedWindow(win)
    print(f"Listening on {HOST}:{PORT1} and {HOST}:{PORT2} (press 'q' to quit)")

    try:
        while True:
            readable, _, _ = select.select([sock1, sock2], [], [], 0.05)

            for s in readable:
                try:
                    data, addr = s.recvfrom(65535)
                except BlockingIOError:
                    continue

                if s is sock1:
                    f = decode_jpeg_to_bgr(data)
                    if f is not None:
                        pd1.findPose(f, draw=1)
                        last_frame1 = f
                elif s is sock2:
                    f = decode_jpeg_to_bgr(data)
                    if f is not None:
                        pd2.findPose(f, draw=1)
                        last_frame2 = f
                else:
                    print("readable is not both sock1 nor sock2")

            # Display whatever we have so far
            if last_frame1 is not None and last_frame2 is not None:
                # match heights before hstack
                h = min(last_frame1.shape[0], last_frame2.shape[0])
                f1 = cv2.resize(last_frame1, (int(last_frame1.shape[1]*h/last_frame1.shape[0]), h))
                f2 = cv2.resize(last_frame2, (int(last_frame2.shape[1]*h/last_frame2.shape[0]), h))

                if is_person_present():
                    # lmlist = LandMarker List https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
                    lmList1, _ = pd1.findPosition(f1, draw = 0, bboxWithHands = 0) 
                    if len(lmList1) > 17:
                        #angles(f1, lmList1[MediaPipe.LEFT_SHOULDER], lmList1[MediaPipe.LEFT_ELBOW], lmList1[MediaPipe.LEFT_WRIST], lmList1[MediaPipe.LEFT_HIP], lmList1[MediaPipe.LEFT_KNEE], lmList1[MediaPipe.RIGHT_SHOULDER], lmList1[MediaPipe.RIGHT_ELBOW], lmList1[MediaPipe.RIGHT_WRIST], lmList1[MediaPipe.RIGHT_HIP], lmList1[MediaPipe.RIGHT_KNEE], drawPoints = 0)
                        angles(f1, lmList1[MediaPipe.LEFT_SHOULDER], lmList1[MediaPipe.LEFT_ELBOW], lmList1[MediaPipe.LEFT_WRIST], lmList1[MediaPipe.RIGHT_SHOULDER], lmList1[MediaPipe.RIGHT_ELBOW], lmList1[MediaPipe.RIGHT_WRIST], drawPoints = 0)
                    lmList2, _ = pd1.findPosition(f2, draw = 0, bboxWithHands = 0)
                    if len(lmList2) > 17:
                        #angles(f2, lmList2[MediaPipe.LEFT_SHOULDER], lmList2[MediaPipe.LEFT_ELBOW], lmList2[MediaPipe.LEFT_WRIST], lmList2[MediaPipe.LEFT_HIP], lmList2[MediaPipe.LEFT_KNEE], lmList2[MediaPipe.RIGHT_SHOULDER], lmList2[MediaPipe.RIGHT_ELBOW], lmList2[MediaPipe.RIGHT_WRIST], lmList2[MediaPipe.RIGHT_HIP], lmList2[MediaPipe.RIGHT_KNEE], drawPoints = 0)
                        angles(f2, lmList2[MediaPipe.LEFT_SHOULDER], lmList2[MediaPipe.LEFT_ELBOW], lmList2[MediaPipe.LEFT_WRIST], lmList2[MediaPipe.RIGHT_SHOULDER], lmList2[MediaPipe.RIGHT_ELBOW], lmList2[MediaPipe.RIGHT_WRIST], drawPoints = 0)

                combined = np.hstack((f1, f2))
                cv2.imshow(win, combined)
            elif last_frame1 is not None:
                f1 = last_frame1

                if is_person_present():
                    lmList1, _ = pd1.findPosition(f1, draw = 0, bboxWithHands = 0)
                    #print(lmList1)
                    if len(lmList1) > 17:
                        #angles(f1, lmList1[MediaPipe.LEFT_SHOULDER], lmList1[MediaPipe.LEFT_ELBOW], lmList1[MediaPipe.LEFT_WRIST], lmList1[MediaPipe.LEFT_HIP], lmList1[MediaPipe.LEFT_KNEE], lmList1[MediaPipe.RIGHT_SHOULDER], lmList1[MediaPipe.RIGHT_ELBOW], lmList1[MediaPipe.RIGHT_WRIST], lmList1[MediaPipe.RIGHT_HIP], lmList1[MediaPipe.RIGHT_KNEE], drawPoints = 0)
                        angles(f1, lmList1[MediaPipe.LEFT_SHOULDER], lmList1[MediaPipe.LEFT_ELBOW], lmList1[MediaPipe.LEFT_WRIST], lmList1[MediaPipe.RIGHT_SHOULDER], lmList1[MediaPipe.RIGHT_ELBOW], lmList1[MediaPipe.RIGHT_WRIST], drawPoints = 0)
                cv2.rectangle(f1, (0, 0), (120, 120), (255, 0, 0), -1)
                cv2.putText(f1, str(int(count)), (20, 70), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1.6, (0, 0, 255), 7)
                cv2.imshow(win, f1)
                
            elif last_frame2 is not None:
                f2 = last_frame2

                if is_person_present():
                    lmList2, _ = pd1.findPosition(f2, draw = 0, bboxWithHands = 0)
                    #print(lmList2)
                    if len(lmList2) > 17:
                        #angles(f2, lmList2[MediaPipe.LEFT_SHOULDER], lmList2[MediaPipe.LEFT_ELBOW], lmList2[MediaPipe.LEFT_WRIST], lmList2[MediaPipe.LEFT_HIP], lmList2[MediaPipe.LEFT_KNEE], lmList2[MediaPipe.RIGHT_SHOULDER], lmList2[MediaPipe.RIGHT_ELBOW], lmList2[MediaPipe.RIGHT_WRIST], lmList2[MediaPipe.RIGHT_HIP], lmList2[MediaPipe.RIGHT_KNEE], drawPoints = 0)
                        angles(f2, lmList2[MediaPipe.LEFT_SHOULDER], lmList2[MediaPipe.LEFT_ELBOW], lmList2[MediaPipe.LEFT_WRIST], lmList2[MediaPipe.RIGHT_SHOULDER], lmList2[MediaPipe.RIGHT_ELBOW], lmList2[MediaPipe.RIGHT_WRIST], drawPoints = 0)

                cv2.imshow(win, f2)
            else:
                # nothing received yet; keep window responsive
                print("frames are not available.")
                cv2.imshow(win, np.zeros((240, 320, 3), dtype=np.uint8))
                time.sleep(5)

            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break
    finally:
        cv2.destroyAllWindows()
        sock1.close()
        sock2.close()
        print("Sockets are closed")

        stop_event.set()
        print("Stop event is set")
        ultrasonic_ranging_thread.join()
        print("Ultrasonic ranging thread is killed")
        rgb_led_thread.join()
        print("RGB LED thread is killed")
        
        rgb_led.destroy()
        ultrasonic_ranging.destroy()
        button.destroy()

if __name__ == "__main__":
    main()
