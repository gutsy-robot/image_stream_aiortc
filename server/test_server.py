from server import ImageStream as stream
import numpy as np


def test_calculate_error():
    st = stream()
    st.ball_x = 4
    st.ball_y = 5

    assert st.calculate_error(1, 1) == 5
    assert st.calculate_error(0, 0) == np.sqrt(4**2 + 5**2)


def test_step():
    st = stream()
    st.ball_x = 100
    st.ball_y = 100
    st.step()

    assert st.ball_x == 101 and st.ball_y == 101

    st.ball_x = 640
    st.step()
    assert st.vel_x == -1

    st.ball_x = 100
    st.ball_y = 480
    st.vel_x = 1
    st.vel_y = 1
    st.step()

    assert st.vel_y == -1
