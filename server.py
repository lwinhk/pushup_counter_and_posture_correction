"""
Server is the program which receives video frames from the clients and processes them for the pose estimation and posture correction. Finally, it will conclude the session and send to cloud server for data storage, analytics and presentation.
"""

from poses import MediaPipe
import cv2
import socket
import numpy as np
import cvzone
from cvzone.PoseModule import PoseDetector
from bigquery import BigQuery
import sys

# server.py (top of file)
import logging
import time

logging.basicConfig(
    level=logging.DEBUG,  # or INFO to reduce noise
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Turn up specific Google/GCP loggers that matter for Storage Write API
logging.getLogger("google.auth").setLevel(logging.DEBUG)
logging.getLogger("google.api_core.bidi").setLevel(logging.DEBUG)
logging.getLogger("google.api_core.retry").setLevel(logging.DEBUG)
logging.getLogger("google.cloud.bigquery_storage_v1").setLevel(logging.DEBUG)
logging.getLogger("grpc").setLevel(logging.DEBUG)

HOST1 = "192.168.1.146"
PORT1 = 5005
HOST2 = "192.168.1.146"
PORT2 = 5006

import os

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

def main():
    project_id = "pushup-counter-aut"
    # dataset_id = "pushup-counter-aut.pushup_dataset"
    # table_id = "pushup-counter-aut.pushup_dataset.pushup_sessions"
    dataset_id = "pushup_dataset"
    table_id = "pushup_sessions"
    big_query = BigQuery(project_id, dataset_id, table_id, API_KEY)
    big_query.test()

    data = {
        "id": 2,
        "user_id": 3,
        "counter": 10,
        "incorrect_counter": 5,
        "correct_counter": 5,
        "timestamp": int(time.time()),                 # second
        "incorrect_counter_perc": "50",                # NUMERIC as string
        "correct_counter_perc":   "50",                # NUMERIC as string
        "created_at": "2025-09-30 16:43:00"            # DATETIME literal
    }

    big_query.simple_send(data)

    return 0

    sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow quick rebind after restart
    sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        # SO_REUSEPORT not available on some platforms; ignore if it fails
        sock1.setsockopt(socket.SOL_SOCKET, getattr(socket, "SO_REUSEPORT", 15), 1)
        sock2.setsockopt(socket.SOL_SOCKET, getattr(socket, "SO_REUSEPORT", 15), 1)
    except OSError:
        pass

    sock1.bind((HOST1, PORT1))
    sock1.settimeout(0.1)  # so we can still process GUI events

    sock2.bind((HOST2, PORT2))
    sock2.settimeout(0.1)  # so we can still process GUI events

    pd = PoseDetector(trackCon = 0.70, detectionCon = 0.70) # Track Confidence and Detection Confidence

    print(f"Listening on {HOST1}:{PORT1} and {HOST2}:{PORT2} (press 'q' in OpenCV window to quit)")
    while True:
        try:
            data1, _ = sock1.recvfrom(65535)   # one full JPEG per datagram
        except socket.timeout:
            # No new frame right now; proceed to handle UI
            data1 = None

        try:
            data2, _ = sock2.recvfrom(65535)
        except socket.timeout:
            data2 = None

        if data1 and data2:
            arr1 = np.frombuffer(data1, dtype=np.uint8)
            frame1 = cv2.imdecode(arr1, cv2.IMREAD_COLOR)
            arr2 = np.frombuffer(data2, dtype=np.uint8)
            frame2 = cv2.imdecode(arr2, cv2.IMREAD_COLOR)
            
            if frame1 is not None and frame2 is not None:
                pd.findPose(frame1, draw = 1)
                pd.findPose(frame2, draw = 1)
                # lmList, bBox = pd.findPosition(frame, draw = 0, bboxWithHands = 0) # lmlist = LandMarker List https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker

                combined_image = np.hstack((frame1, frame2))

                # Display the combined image
                cv2.imshow('Server frames', combined_image)
                # cv2.imshow("UDP Client — latest frame", frame)
            elif frame1 is not None and frame2 is None:
                pd.findPose(frame1, draw = 1)
                # lmList, bBox = pd.findPosition(frame, draw = 0, bboxWithHands = 0) # lmlist = LandMarker List https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker

                cv2.imshow("Server frames", frame1)
            elif frame2 is not None and frame1 is None:
                pd.findPose(frame2, draw = 1)
                # lmList, bBox = pd.findPosition(frame, draw = 0, bboxWithHands = 0) # lmlist = LandMarker List https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker

                cv2.imshow("Server frames", frame2)
        else:
            print("data not found")

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()
    sock1.close()
    sock2.close()

if __name__ == "__main__":
    main()