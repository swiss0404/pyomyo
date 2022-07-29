from cmath import e
import multiprocessing
import pandas as pd
from pyparsing import line
from pyomyo import Myo, emg_mode
import os
import pygame
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *
import pickle

min_roll = -30
max_roll = 30
min_pitch = -30
max_pitch = 30
neutral_roll = 0
neutral_pitch = 0
neutral_yaw = 0 
count = 0
is_recording = False
is_start = False 
count_list = [0]*10
R_myo_tty = str(b'\x00\x03\x00\x00\x08Swiss.np')
database_file = 'examples/database.csv'
record_cache_imu = []
record_cache_emg = []

def cls():
	# Clear the screen in a cross platform way
	# https://stackoverflow.com/questicoons/517970/how-to-clear-the-interpreter-console
    os.system('cls' if os.name=='nt' else 'clear')

# ------------ Myo Setup ---------------
q = multiprocessing.Queue()

def worker(q):
    m = Myo(mode=emg_mode.PREPROCESSED)
    m.connect()
    
    def add_to_queue_emg(emg, movement):
        q.put(emg)
        

    m.add_emg_handler(add_to_queue_emg)
    
    def add_to_queue_imu(quat, acc, gyro):
        imu_data = [quat, acc, gyro]
        q.put(imu_data)
    
    m.add_imu_handler(add_to_queue_imu)
    
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

# -------- Main Program Loop -----------


def resizewin(width, height):
    """
    For resizing window
    """
    if height == 0:
        height = 1
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.0*width/height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def init():
    glShadeModel(GL_SMOOTH)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)


def draw(w, nx, ny, nz):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0, 0.0, -7.0)

    drawText((-2.6, 1.8, 2), "IMU recording", 18)
    if is_start:
        if is_recording:
            drawText((-2.6, 1.6, 2), "RECORDING", 18)
        else:
            drawText((-2.6, 1.6, 2), "REST", 18)
    else:
        drawText((-2.6, 1.6, 2), "PAUSE", 18)
    drawText((-2.6, -2, 2), "'s' to start, 'p' to pause, 'c' to calibrate ", 16)

    yaw = nx
    pitch = ny
    roll = nz
    drawText((-2.6, -1.8, 2), "Yaw: %f, Pitch: %f, Roll: %f" %(yaw, pitch, roll), 16)
    glRotatef(-roll, 0.00, 0.00, 1.00)
    glRotatef(pitch, 1.00, 0.00, 0.00)
    glRotatef(yaw, 0.00, 1.00, 0.00)

    glBegin(GL_QUADS)
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(1.0, 0.2, -1.0)
    glVertex3f(-1.0, 0.2, -1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(1.0, 0.2, 1.0)

    glColor3f(1.0, 0.5, 0.0)
    glVertex3f(1.0, -0.2, 1.0)
    glVertex3f(-1.0, -0.2, 1.0)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(1.0, -0.2, -1.0)

    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(1.0, 0.2, 1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(-1.0, -0.2, 1.0)
    glVertex3f(1.0, -0.2, 1.0)

    glColor3f(1.0, 1.0, 0.0)
    glVertex3f(1.0, -0.2, -1.0)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(-1.0, 0.2, -1.0)
    glVertex3f(1.0, 0.2, -1.0)

    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(-1.0, 0.2, -1.0)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(-1.0, -0.2, 1.0)

    glColor3f(1.0, 0.0, 1.0)
    glVertex3f(1.0, 0.2, -1.0)
    glVertex3f(1.0, 0.2, 1.0)
    glVertex3f(1.0, -0.2, 1.0)
    glVertex3f(1.0, -0.2, -1.0)
    glEnd()


def drawText(position, textString, size):
    font = pygame.font.SysFont("Courier", size, True)
    textSurface = font.render(textString, True, (255, 255, 255, 255), (0, 0, 0, 255))
    textData = pygame.image.tostring(textSurface, "RGBA", True)
    glRasterPos3d(*position)
    glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)

def quat_to_ypr(q):
    yaw   = math.atan2(2.0 * (q[1] * q[2] + q[0] * q[3]), q[0] * q[0] + q[1] * q[1] - q[2] * q[2] - q[3] * q[3])
    pitch = math.asin(-2.0 * (q[1] * q[3] - q[0] * q[2]))
    roll  = math.atan2(2.0 * (q[0] * q[1] + q[2] * q[3]), q[0] * q[0] - q[1] * q[1] - q[2] * q[2] + q[3] * q[3])
    pitch *= 180.0 / math.pi
    yaw   *= 180.0 / math.pi
    yaw   -= 0  # Declination at Chandrapur, Maharashtra is - 0 degress 13 min bangkok thailand is idk
    roll  *= 180.0 / math.pi
    return [yaw, pitch, roll]

def keep_domain(angle):
    if angle >= 180:
        angle-=360
    elif angle <= -180:
        angle+=360
    return angle

def check_is_recording_moe(adjusted_roll,adjusted_pitch):
    global count_list
    if min_roll < adjusted_roll and adjusted_roll < max_roll and min_pitch < adjusted_pitch and adjusted_pitch < max_pitch:
        count_list = count_list[1:]
        count_list.append(1)
    else: 
        count_list = count_list[1:]
        count_list.append(-1)
    if sum(count_list) >= 0:
        return False
    else:
        return True 

def name_prompt(data):
    while True:
        print('please choose your name')
        for i in range(len(data['name'].unique())):
            print(str(i) +': '+ data['name'].unique()[i])
        name_num = input('type in your name number : ')
        print('\n---------------------------------\n')
        try:
            name_num = int(name_num)
            if 0 <= name_num <= len(data['name'].unique()) - 1:
                return data['name'].unique()[name_num]
            else:
                print('Number is not within the range')

        except ValueError:
            print('Invalid value')


def gesture_prompt(data, name): 
    while True:
        print('please choose gesture')
        for i in range(len(data[data.name == name]['gesture'])):
            print(str(i) +': '+ data[data.name == name]['gesture'].iloc[i])
        gesture_num = input('type in gesture number: ')
        print('\n---------------------------------\n')
        try:
            gesture_num = int(gesture_num)
            if 0 <= int(gesture_num) <= len(data[data.name == name]['gesture']) - 1:
                return data[data.name == name]['gesture'].iloc[gesture_num]
            else:
                print('Number is not within the range')

        except ValueError:
            print('Invalid value')
            

def mode_prompt ():
    while True:
        print('select mode')
        print('0: recording continuous\n1: record only once\n2: add gesture name')
        mode = input('type in mode number: ')
        print('\n---------------------------------\n')
        try:
            mode = int(mode)
            if 0 <= int(mode) <= 2:
                return mode
            else:
                print('Number is not within the range')
                
        except ValueError:
            print('Invalid value')

    
def add_new_gesture(data,database_file,name):
    new_gesture_name = input('type new gesture name: ')
    try:
        str(new_gesture_name)
        if new_gesture_name not in data[data.name == name]['gesture'].to_list():
            data = data.append({'name': name, 'gesture': new_gesture_name ,'repetition' : 0}, ignore_index=True)
            data.to_csv(open(database_file, "wb" ), index = False)
        else: 
            print('This gesture already exists')
            add_new_gesture(data,database_file,name)
    except ValueError:
        print('input invalid') 
        add_new_gesture(data,database_file,name)



if __name__ == "__main__":
    data = pd.read_csv(open(database_file, "rb" ))
    name = name_prompt(data)
    mode = mode_prompt()
    if mode == 2:
        add_new_gesture(data,database_file,name)
        data = pd.read_csv(open(database_file, "rb" ))
    gesture = gesture_prompt(data, name)

    video_flags = OPENGL | DOUBLEBUF
    pygame.init()
    p = multiprocessing.Process(target=worker, args=(q,))
    p.start()
    screen = pygame.display.set_mode((640, 480), video_flags)
    pygame.display.set_caption("IMU orientation visualization")
    resizewin(640, 480)
    init()
    frames = 0
    ticks = pygame.time.get_ticks()
    try:
        while True:
            while not(q.empty()):
                emg_imu = list(q.get())
                if len(emg_imu) != 8:
                    quat, acc, gyro = emg_imu
                    # print("Quaternions:", quat)
                    # print("Acceleration:", acc)
                    # print("Gyroscope:", gyro)
                    [w, nx, ny, nz] = [x/16384 for x in quat]
                    try:
                        [yaw, pitch , roll] = quat_to_ypr([w, nx, ny, nz])
                        adjusted_yaw = keep_domain(yaw - neutral_yaw)
                        adjusted_pitch = keep_domain(pitch - neutral_pitch)
                        adjusted_roll = keep_domain(roll - neutral_roll)
                    except ValueError:
                        adjusted_yaw = 0
                        adjusted_pitch = 0
                        adjusted_roll = 0
                    draw(1, adjusted_yaw, adjusted_pitch, adjusted_roll)
                    pygame.display.flip()
                    if is_start:
                        is_recording = check_is_recording_moe(adjusted_roll,adjusted_pitch)
                        imu_data = emg_imu
                        adjusted_ypr = [adjusted_yaw,adjusted_pitch,adjusted_roll]
                        neutral_ypr = [neutral_yaw,neutral_pitch,neutral_roll]
                        record_cache_imu.append([imu_data,adjusted_ypr,neutral_ypr,is_recording,pygame.time.get_ticks()])
                    # frames += 1      
                    # print("fps: %d" % ((frames*1000)/(pygame.time.get_ticks()-ticks)))
                else:
                    emg_data = emg_imu 
                    if is_start:
                        record_cache_emg.append([emg_data,is_recording,pygame.time.get_ticks()])
                for ev in pygame.event.get():
                    if ev.type == QUIT:
                        raise KeyboardInterrupt()
                    elif ev.type == KEYDOWN:
                        if ev.unicode == 'c':
                            neutral_roll = roll 
                            neutral_pitch = pitch
                            neutral_yaw = yaw
                        elif ev.unicode == 'e':
                            print("Pressed e, erasing calibration")
                            neutral_roll = 0 
                            neutral_pitch = 0
                            neutral_yaw = 0
                        elif ev.unicode == 's':
                            print("Pressed s, Started")
                            print('start record')
                            is_recording = True
                            is_start = True
                        elif ev.unicode == 'p':
                            print("Pressed p, Paused")
                            is_start = False
                        elif ev.unicode == 'q':
                            print("Pressed q, exit and save")
                            data = pd.read_csv(open(database_file, "rb" ))
                            pre_add_rep = int(data[(data.name == name) & (data.gesture == gesture)]['repetition'])
                            pickle.dump(record_cache_emg, open('examples/data/'+ name + "_" + gesture + "_" + str(pre_add_rep+1) + "_" + "emg_rec.p", "wb" ) )
                            pickle.dump(record_cache_imu, open('examples/data/'+ name + "_" + gesture + "_" + str(pre_add_rep+1) + "_" + "imu_rec.p", "wb" ) )
                            data.loc[(data.name == name) & (data.gesture == gesture),['repetition']] = int(data[(data.name == name) & (data.gesture == gesture)]['repetition']) + 1
                            data.to_csv(open(database_file, "wb" ), index = False)
                            is_start = False
                            record_cache_emg = []
                            record_cache_imu = []
                            print("saved")
                            raise KeyboardInterrupt()
    except KeyboardInterrupt:
        print(min_roll,max_roll,min_pitch,max_pitch)
        print("Quitting")
        pygame.quit()