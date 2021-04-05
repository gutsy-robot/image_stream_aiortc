import argparse
import asyncio
import logging
import math
import numpy as np
import cv2
import numpy
from av import VideoFrame
import matplotlib
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling


class BallStream(VideoStreamTrack):
    """
    A video track that returns an animated flag.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.counter = 0
        self.height, self.width = 480, 640
        self.ball_pos = np.array([100, 100])
        self.ball_velocity = np.array([1, 1])
        print("ball stream initi")

    async def recv(self):

        pts, time_base = await self.next_timestamp()
        img = np.zeros((self.height, self.width, 3), dtype='uint8')
        # Increment the position
        self.ball_pos += self.ball_velocity
        cv2.circle(img, (self.ball_pos[0], self.ball_pos[1]), 20, (255, 0, 0), -1)
        if self.ball_pos[1] >= 480:
            self.ball_velocity[1] *= -1
        elif self.ball_pos[1] <= 0:
            self.ball_velocity[1] *= -1
        if self.ball_pos[0] >= 640:
            self.ball_velocity[0] *= -1
        elif self.ball_pos[0] <= 0:
            self.ball_velocity[0] *= -1

        frame = VideoFrame.from_ndarray(
            img, format="bgr24"
        )
        frame.pts = pts
        frame.time_base = time_base
        return frame


async def run(pc, signaling, player=None):
    def add_tracks():
        print('add tracks called')
        if player and player.audio:
            pc.addTrack(player.audio)

        if player and player.video:
            pc.addTrack(player.video)
        else:
            pc.addTrack(BallStream())

    @pc.on("track")
    def on_track(track):
        print("Receiving %s" % track.kind)
        print("helloo")
        pc.addTrack(track)
        # recorder.addTrack(track)

    @pc.on("datachannel")
    def on_datachannel(channel):
        # channel_log(channel, "-", "created by remote party")
        print("channel started on server end")

        @channel.on("message")
        def on_message(message):
            # channel_log(channel, "<", message)
            print("received message from client: ", message)
    # connect signaling
    await signaling.connect()

    # if role == "offer":
    # send offer
    add_tracks()
    print("add tracks call done")
    await pc.setLocalDescription(await pc.createOffer())
    print("set local done")
    await signaling.send(pc.localDescription)
    print("send done")

    await consume_signaling(pc, signaling)
    # consume signaling


async def consume_signaling(pc, signaling):
    while True:
        obj = await signaling.receive()
        print("receive done")

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)

            if obj.type == "offer":
                # send answer
                # add_tracks()
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
                print("signal sent")

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
                player=None,
                signaling=signaling,
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
