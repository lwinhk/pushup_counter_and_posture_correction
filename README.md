# Push-up Counter and Posture Correction
This is the IoT project to detect push-up, count and evaluate posture.\

Server will listen to socket 5005 and 5006. Client will capture video frames from camera and broadcast at port 5005. ClientRecorded will capture video frames from recorded video (vid1.mp4) and broadcast at port 5006.
Server will receive video frames from one of the clients or both clients and process using PoseDetector.

# Files
* bigquery.py = Add a new row in BigQuery data table
* client.py = Capture video frames from camera, resize them and send them to UDP server
* client_recorded.py = Capture video frames from video file, resize them and send them to UDP server
* create_key.py = Create a key for Google Cloud service account (only use once to create key)
* gpio.py = A GPIO class to manage sensors
* main.py = A program to test GPIO class and sensors (it is not used in the demo)
* poses.py = A class that contains MediaPipe landmarks and their numbers
* server.py = Receive video frames from UDP clients, detect posture, count push-up, evaluate posture and manage sensors
* vid1.mp4 = A sample push-up video file to use in client_recorded.py

# Environment Variables
`client1_port=5005`\
`client2_port=5006`\
`server_ip=0.0.0.0`

`google_cloud_api_key="xxxxxxxx"`\
`google_cloud_client_id="xxxxxxxx"`\
`google_cloud_client_secret="xxxxxxxx"`

`export client1_port`\
`export client2_port`\
`export server_ip`\
`export google_cloud_api_key`\
`export google_cloud_client_id`\
`export google_cloud_client_secret`

# Python Dependencies
Google Cloud\
Google OAuth2\
OpenCV\
RPi.GPIO\
MediaPipe PoseDetector\
Numpy

# Running
To run the application, you can run below commands in 2 separate terminals.

`python client.py`\
`python server.py`

To quit the application, go to separate GUI windows (not terminal) and press "q".

# Support
Please contact the developer at dpc3559@autuni.ac.nz or lwinhk2008@gmail.com.