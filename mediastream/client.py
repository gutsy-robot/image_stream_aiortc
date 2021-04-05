import argparse
import asyncio
import logging
import math

import cv2
import numpy
from av import VideoFrame

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
    MediaStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling
import scipy.misc
import matplotlib
from PIL import Image


class BallTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, pc=None):
        super().__init__()  # don't forget this!
        self.track = track
        self.counter = 0
        # self.channel = channel
        self.pc = pc
        self.curr_msg = "first msg"

    async def recv(self):
        frame = await self.track.recv()

        img = frame.to_ndarray(format="bgr24")

        cv2.imshow('client', img)
        k = cv2.waitKey(20)

        im_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        (thresh, im_bw) = cv2.threshold(im_gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        moments = cv2.moments(im_bw)
        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])
        print("estimated coordinates of ball center: ", (cx, cy))

        self.counter += 1
        self.curr_msg = str(self.counter)

        return frame


async def run(pc, signaling):
    await signaling.connect()

    @pc.on("track")
    def on_track(track):
        print("Receiving %s" % track.kind)
        ball_track = BallTrack(track, pc)
        pc.addTrack(ball_track)

    # consume signaling
    while True:
        print("receiving")
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)

            if obj.type == "offer":
                # send answer
                print("client side detecred offer")
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)

        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)

        elif obj is BYE:
            print("Exiting")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video stream from the command line")
    parser.add_argument("--verbose", "-v", action="count")
    add_signaling_arguments(parser)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # create signaling and peer connection
    signaling = create_signaling(args)
    pc = RTCPeerConnection()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                signaling=signaling,
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
