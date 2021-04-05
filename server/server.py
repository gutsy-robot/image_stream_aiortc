import argparse
import asyncio
import logging
import time
import numpy as np
import cv2
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling

"""
Server to transmit an image stream encoded as bytes to the client and receive position of the ball from the client.

Code taken from : https://github.com/aiortc/aiortc/blob/main/examples/datachannel-cli/cli.py

"""


class ImageStream:
    """
        A class to for tracking the position of the ball on the server.

        ...

        Attributes
        ----------
        None

        Methods
        -------
        step():
            Move the ball by the current velocity in unit time and update the velocities if you hit the wall.

        emit():
            generate an image with the current position of the ball.

        calculate_error(estimated_x, estimated_y):
            calculates error between actual and estimated ball positions.

        """

    def __init__(self):
        self.vel_x = 1
        self.vel_y = 1
        self.ball_x = 260
        self.ball_y = 300

    def step(self):
        """Move the ball by the current velocity in unit time and update the velocities if you hit the wall."""

        self.ball_x = self.ball_x + self.vel_x
        self.ball_y = self.ball_y + self.vel_y
        if self.ball_y >= 480:
            self.vel_y *= -1
        elif self.ball_y <= 0:
            self.vel_y *= -1
        if self.ball_x >= 640:
            self.vel_x *= -1
        elif self.ball_x <= 0:
            self.vel_x *= -1

    def emit(self):
        """generate an image with the current position of the ball."""

        img = np.zeros((480, 640, 3), dtype='uint8')
        cv2.circle(img, (self.ball_x, self.ball_y), 20, (255, 0, 0), -1)
        return img

    def calculate_error(self, estimated_x, estimated_y):
        """
        calculates error between actual and estimated ball positions.

        Parameters
        ----------
        estimated_x : float
        estimated_y: float

        Returns error between actual and estimated ball positions.
        -------

        """

        return np.sqrt((self.ball_x - estimated_x) ** 2 + (self.ball_y - estimated_y) ** 2)


async def consume_signaling(pc, signaling):
    """
    Method to respond to communication from the client side.

        Parameters
        ----------
        pc : RTCPeerConnection
        signaling: TCPSocketSignalling

        Returns: None
        -------

    """

    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)

            if obj.type == "offer":
                # send answer
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break


async def run_offer(pc, signaling):
    """
    Method to set up connection with the client and declare necessary callbacks

        Parameters
        ----------
        pc : RTCPeerConnection
        signaling: TCPSocketSignalling

        Returns: None
        -------

    """
    await signaling.connect()

    channel = pc.createDataChannel("chat")
    stream = ImageStream()

    @channel.on("open")
    def on_open():
        print("on open called")
        stream.step()
        img_str = cv2.imencode('.jpg', stream.emit())[1].tostring()
        channel.send(img_str)

    @channel.on("message")
    def on_message(message):
        x, y = float(message.split(',')[0]), float(message.split(',')[1])
        print("received ball coordinates from client: ", (x, y))
        print("error between the estimated and original ", stream.calculate_error(x, y))
        stream.step()
        img_str = cv2.imencode('.jpg', stream.emit())[1].tostring()
        channel.send(img_str)

    # send offer
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)
    await consume_signaling(pc, signaling)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data channels ping/pong")
    parser.add_argument("--verbose", "-v", action="count")
    add_signaling_arguments(parser)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    signaling = create_signaling(args)
    pc = RTCPeerConnection()
    coro = run_offer(pc, signaling)

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(pc.close())
        loop.run_until_complete(signaling.close())
