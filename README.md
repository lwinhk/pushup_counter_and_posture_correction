# There are 3 main files in this project.
* server.py
* client.py
* client_recorded.py

Server will listen to socket 5005 and 5006. Client will capture video frames from camera and broadcast at port 5005. ClientRecorded will capture video frames from recorded video (vid1.mp4) and broadcast at port 5006.
Server will receive video frames from one of the clients or both clients and process using PoseDetector.

To run the application, you can run below commands in 3 separate terminals.

> python server.py
> python client.py
> python client_recorded.py

To quit the application, go to separate GUI windows (not terminal) and press "q".