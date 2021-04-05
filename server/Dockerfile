FROM python:3.6.9

ADD server.py .

RUN pip3 install numpy aiortc

RUN apt-get update && apt-get install -y python3-opencv
RUN pip install opencv-python

CMD ["python", "server.py", "-s", "tcp-socket"]