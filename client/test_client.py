from client import get_ball_center
import numpy as np
import cv2


def test_get_ball_center():
    img = np.zeros((480, 640, 3), dtype='uint8')
    cv2.circle(img, (100, 100), 20, (255, 0, 0), -1)

    x, y = get_ball_center(img)
    assert x == 100 and y == 100

    img = np.zeros((480, 640, 3), dtype='uint8')
    cv2.circle(img, (30, 23), 20, (255, 0, 0), -1)
    x, y = get_ball_center(img)
    print(x, y)
    assert x == 30 and y == 23

    img = np.zeros((480, 640, 3), dtype='uint8')
    cv2.circle(img, (40, 400), 20, (255, 0, 0), -1)
    x, y = get_ball_center(img)
    print(x, y)
    assert x == 40 and y == 400
