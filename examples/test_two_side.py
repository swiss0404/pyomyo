import multiprocessing
import pygame
from pyomyo import Myo, emg_mode
import os
import sys
from OpenGL.GL import *
from OpenGL.GLU import *
import re
from serial.tools.list_ports import comports


def detect_tty():
    valid_ttys = []
    for p in comports():
        if re.search(r"PID=2458:0*1", p[2]):
            valid_ttys.append(p[0])
    assert len(valid_ttys) == 2, f"Expected 2 Myo devices, found {len(valid_ttys)}"
    return valid_ttys


r_addr = [233, 28, 231, 168, 151, 205]
l_addr = [48, 12, 163, 25, 55, 236]


def myo_worker(myo_queue, tty, color, mac_address):
    """Worker function for handling Myo data collection."""
    myo_device = Myo(tty=tty, mode=emg_mode.RAW)
    myo_device.connect(addr=mac_address)

    def emg_handler(emg, movement):
        myo_queue.put((emg, movement))

    myo_device.set_leds(color, color)
    myo_device.add_emg_handler(emg_handler)

    while True:
        myo_device.run()


def init_pygame():
    """Initialize Pygame and OpenGL."""
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, pygame.DOUBLEBUF | pygame.OPENGL)

    from OpenGL.GL import (
        glClearColor,
        glClear,
        GL_COLOR_BUFFER_BIT,
        GL_DEPTH_BUFFER_BIT,
    )

    glClearColor(0.0, 0.0, 0.0, 1.0)


def main():
    q_left = multiprocessing.Queue()
    q_right = multiprocessing.Queue()

    l_tty, r_tty = detect_tty()

    p_left = multiprocessing.Process(
        target=myo_worker, args=(q_left, l_tty, (255, 0, 0), l_addr)
    )
    p_right = multiprocessing.Process(
        target=myo_worker, args=(q_right, r_tty, (0, 255, 0), r_addr)
    )

    p_left.start()
    p_right.start()

    init_pygame()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not q_left.empty():
            emg_data_left, movement_left = q_left.get()
            print(f"Left Myo: {emg_data_left}, Movement: {movement_left}")

        if not q_right.empty():
            emg_data_right, movement_right = q_right.get()
            print(f"Right Myo: {emg_data_right}, Movement: {movement_right}")

        # OpenGL Drawing Code
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        pygame.display.flip()

    p_left.terminate()
    p_right.terminate()
    p_left.join()
    p_right.join()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
