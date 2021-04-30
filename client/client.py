from multiprocessing import Process, Queue, Value
import argparse
import asyncio
import logging
import time
import numpy as np
import cv2
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling


"""
Client to receive an encoded image stream and decode it and calculate the ball position and communicate to the server.

Code taken from : https://github.com/aiortc/aiortc/blob/main/examples/datachannel-cli/cli.py

"""


def channel_log(channel, t, message):
    print("channel(%s) %s %s" % (channel.label, t, message))


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

def process_frame(decoded_imgs, cx, cy):
    decoded_img = decoded_imgs.get()
    x, y = get_ball_center(decoded_img)
    cx.value = x
    cy.value = y

def get_ball_center(decoded_img):
    """
    Method to calculate the position of the center of the ball.

       Parameters
       ----------
       decoded_img : bdr image as a numpy array

       Returns:
       -------
       cx: x coordinate of ball center
       cy: y coordinate of ball center

    """
    im_gray = cv2.cvtColor(decoded_img, cv2.COLOR_BGR2GRAY)
    (thresh, im_bw) = cv2.threshold(im_gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    moments = cv2.moments(im_bw)

    cx = int(moments["m10"] / moments["m00"])
    cy = int(moments["m01"] / moments["m00"])

    return cx, cy

async def run_answer(pc, signaling):
    """
    Method to set up connection with the server and declare necessary callbacks

        Parameters
        ----------
        pc : RTCPeerConnection
        signaling: TCPSocketSignalling

        Returns:
        -------
        None

    """
    q = Queue()

    print("queue declared")
    await signaling.connect()

    @pc.on("datachannel")
    def on_datachannel(channel):
        channel_log(channel, "-", "created by remote party")

        @channel.on("message")
        def on_message(message):
            # decode and stream
            decoded = cv2.imdecode(np.frombuffer(message, np.uint8), -1)
            cv2.imshow('client', decoded)
            k = cv2.waitKey(1)

            cx = Value("f", 0)
            cy = Value("f", 0)
            p = Process(target=process_frame, args=(q, cx, cy))
            q.put(decoded)
            p.start()
            p.join()
            res = str(cx.value) + ', ' + str(cy.value)
            channel.send(res)

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
    coro = run_answer(pc, signaling)

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(pc.close())
        loop.run_until_complete(signaling.close())
