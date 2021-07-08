Calculating ball position in an Image stream in aiortc
===

Requirements
---
Numpy, opencv, aiortc, multiprocessing, pytest


Server
--

The server end produces an image stream which consists of a black background and a blue ball. 
The stream periodically updates the position of the ball. The server transmits the frames as bytes
to the client on a datachannel. The server also receives the estimated position of the ball from the client
and then calculates and displays the error in the estimation.

To launch the server cd into the server directory and use the following command:
    
    python server.py -s tcp-socket

Client
--

The client receives the encoded frames from the server. It decodes the received frames to numpy
and then detects position of the ball using computer vision techniques. The estimated ball 
position is communicated back to the server via a datachannel.

To launch the client cd into the client directory and use the following command:
    
    python client.py -s tcp-socket



Test
--

To run the server unit tests, change directory to server and run:
    
    pytest test_server.py

To run the client unit tests, change directory to client and run:

    pytest test_client.py


Example Video
---
[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/TVfckV-8fTk/0.jpg)](https://www.youtube.com/watch?v=TVfckV-8fTk
)


Future Work
--

Currently, the images are being communicated from the server end on the datachannel itself. Ideally, 
we would want that to happen on a MediaStreamTrack. I was able to create a server client which is present
in the Mediastream directory. There I was able to send frames from the server to the client by 
extending the MediaStreamTrack class and the client was also able to receive it and find out the 
position of the ball. However, I wasn't able to figure out how to send back the calculated 
ball position back to the server using data channel. The declaration of data channel on the client 
side seems to obstruct the flow of incoming frames from the client. I think I would have to write a 
negotiate function similar to what has been done
[here](https://github.com/aiortc/aiortc/blob/main/examples/server/client.js#L51).  To check out this unfinished work, 
change the current directory to mediastream and then in 2 separate terminals run:

    python server.py -s tcp-socket
    
    python client.py -s tcp-socket

This video demonstrates this unfinished variant of the server client app in action.


[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/x9f_TQVZlr4/0.jpg)](https://www.youtube.com/watch?v=x9f_TQVZlr4)


Both the server and client directories have a docker file created for them, however, I wasn't able to get
the communication between the 2 docker containers to work. So, this is also something that could be done in 
the future.

Creating the minikube pipeline for deployment.
