"""
Can plot EMG data in 2 different ways
change DRAW_LINES to try each.
Press Ctrl + C in the terminal to exit 
"""

import pygame
from pygame.locals import *
import multiprocessing
from OpenGL.GL import *
from OpenGL.GLU import *
from pyomyo import Myo, emg_mode
import faulthandler

faulthandler.enable()
# ------------ Myo Setup ---------------
q = multiprocessing.Queue()


def worker(q):
    m = Myo(mode=emg_mode.PREPROCESSED)
    m.connect()

    def add_to_queue(emg, movement):
        q.put(emg)

    m.add_emg_handler(add_to_queue)

    def print_battery(bat):
        print("Battery level:", bat)

    m.add_battery_handler(print_battery)

    # Orange logo and bar LEDs
    m.set_leds([128, 0, 0], [128, 0, 0])
    # Vibrate to know we connected okay
    m.vibrate(1)

    """worker function"""
    while True:
        m.run()
    print("Worker Stopped")


# last_vals = None
# def plot(scr, vals):
# 	DRAW_LINES = True

# 	global last_vals
# 	if last_vals is None:
# 		last_vals = vals
# 		return

# 	D = 5
# 	w, h = scr.get_size()
# 	scr.scroll(-D)
# 	scr.fill((0, 0, 0), (w - D, 0, w, h))
# 	for i, (u, v) in enumerate(zip(last_vals, vals)):
# 		if DRAW_LINES:
# 			pygame.draw.line(scr, (0, 255, 0),
# 							 (w - D, int(h/9 * (i+1 - u))),
# 							 (w, int(h/9 * (i+1 - v))))
# 			pygame.draw.line(scr, (255, 255, 255),
# 							 (w - D, int(h/9 * (i+1))),
# 							 (w, int(h/9 * (i+1))))
# 		else:
# 			c = int(255 * max(0, min(1, v)))
# 			scr.fill((c, c, c), (w - D, i * h / 8, D, (i + 1) * h / 8 - i * h / 8))

# 	pygame.display.flip()
# 	last_vals = vals

# import pygame
# from pygame.locals import *


# ------------ Myo Setup ---------------
# ... (keep your Myo setup code here)

last_vals = None


def plot(vals):
    global last_vals
    if last_vals is None:
        last_vals = vals
        return

    w, h = 800, 600  # define your width and height here
    D = 5

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    for i, (u, v) in enumerate(zip(last_vals, vals)):
        glBegin(GL_LINES)
        glColor3f(0, 1, 0)  # green color for the first line
        glVertex2f(w - D, h / 9 * (i + 1 - u))
        glVertex2f(w, h / 9 * (i + 1 - v))

        glColor3f(1, 1, 1)  # white color for the second line
        glVertex2f(w - D, h / 9 * (i + 1))
        glVertex2f(w, h / 9 * (i + 1))
        glEnd()

    pygame.display.flip()
    last_vals = vals


# -------- Main Program Loop -----------
if __name__ == "__main__":
    p = multiprocessing.Process(target=worker, args=(q,))
    p.start()

    w, h = 800, 600
    scr = pygame.display.set_mode((w, h))

    try:
        while True:
            # Handle pygame events to keep the window responding
            pygame.event.pump()
            # Get the emg data and plot it
            while not (q.empty()):
                emg = list(q.get())
                plot([e / 500.0 for e in emg])
                print(emg)

    except KeyboardInterrupt:
        print("Quitting")
        pygame.quit()
        quit()
