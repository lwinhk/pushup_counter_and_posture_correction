"""
Server is the program which receives video frames from the clients and processes them for the pose estimation and posture correction. Finally, it will conclude the session and send to cloud server for data storage, analytics and presentation.
"""

from poses import MediaPipe
import socket, select, cv2, numpy as np
from cvzone.PoseModule import PoseDetector

HOST = "0.0.0.0"   # listen on all interfaces
PORT1 = 5005
PORT2 = 5006

def decode_jpeg_to_bgr(data: bytes):
    if not data:
        return None
    arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return frame

def main():
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
    win = "Server frames"
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
                else:
                    f = decode_jpeg_to_bgr(data)
                    if f is not None:
                        pd2.findPose(f, draw=1)
                        last_frame2 = f

            # Display whatever we have so far
            if last_frame1 is not None and last_frame2 is not None:
                # match heights before hstack
                h = min(last_frame1.shape[0], last_frame2.shape[0])
                f1 = cv2.resize(last_frame1, (int(last_frame1.shape[1]*h/last_frame1.shape[0]), h))
                f2 = cv2.resize(last_frame2, (int(last_frame2.shape[1]*h/last_frame2.shape[0]), h))
                combined = np.hstack((f1, f2))
                cv2.imshow(win, combined)
            elif last_frame1 is not None:
                cv2.imshow(win, last_frame1)
            elif last_frame2 is not None:
                cv2.imshow(win, last_frame2)
            else:
                # nothing received yet; keep window responsive
                cv2.imshow(win, np.zeros((240, 320, 3), dtype=np.uint8))

            if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q'), 27):
                break
    finally:
        cv2.destroyAllWindows()
        sock1.close()
        sock2.close()

if __name__ == "__main__":
    main()
