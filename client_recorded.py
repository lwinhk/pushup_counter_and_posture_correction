import cv2
import socket
import numpy as np
import sys

HOST = "127.0.0.1"
PORT = 5006
MAX_UDP = 65507          # absolute max UDP payload
TARGET_MAX = 60000       # stay safely under the max
FRAME_WIDTH = 640
JPG_QUALITY = 20         # choose suitable one from 90, 80, 70, 60, 50, 40, 30, 20

def encode_jpeg_under_limit(frame, target_max=TARGET_MAX):
    # Resize to width 640 for predictable size
    h, w = frame.shape[:2]
    new_w = FRAME_WIDTH
    new_h = int(h * (new_w / w))
    frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 20])
    b = buf.tobytes()
    if len(b) <= target_max:
        return b
    
    return None

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    addr = (HOST, PORT)

    cap = cv2.VideoCapture('vid1.mp4')

    print(f"Sending UDP JPEG frames to {HOST}:{PORT} (press 'q' in OpenCV window to quit)")
    while True:
        ok, frame = cap.read()
        if not ok:
            cap = cv2.VideoCapture('vid1.mp4')
            continue

        payload = encode_jpeg_under_limit(frame)

        if payload is None or len(payload) > MAX_UDP:
            # skip this frame if we somehow exceeded the UDP limit
            continue

        sock.sendto(payload, addr)

        # Optional preview
        cv2.imshow("Server preview", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    if sys.platform == "Linux":
        camera.stop()
    elif sys.platform == "win32" or sys.platform == "Windows":
        cap.release()

    cv2.destroyAllWindows()
    sock.close()

if __name__ == "__main__":
    main()