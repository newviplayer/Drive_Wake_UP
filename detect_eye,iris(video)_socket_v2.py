import torch
# 오류 잡아주는 쪽
import pathlib
from pathlib import Path
pathlib.PosixPath = pathlib.WindowsPath
# -------------------
import cv2
import time
import socket
import threading
import queue

# 서버에 연결
server_host = '***.***.***.***'  # 라즈베리 파이의 IP 주소 또는 호스트 이름
server_port = 12345  # 서버가 대기하는 포트
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_host, server_port))

model = torch.hub.load('./yolov5','custom' ,'best.pt', source='local')
print("model load success")
resize_rate = 1
# Image
# img_src = 'test_image.jpg'
# Video


# # Inference
# results = model(img_src)
# print(type(results.pandas().xyxy[0]))
# ----------------------------------
# xmin = 0
# ymin = 1
# xmax = 2
# ymax = 3
# confidence = 4
# class = 5
# name = 6
# ----------------------------------

# Image resize ?
# a = input('resize ? : ')
# if a == 'y':
#     resize_rate = 0.2
# elif a == 'n':
#     resize_rate = 1

def yolo_model(data):
    # data 모델 돌리기
    yolo_results = model(data)
    # 모델 돌려서 나온 values
    df = yolo_results.pandas().xyxy[0]
    # values 저장할 빈 list 선언
    obj_list = []
    # values dict 형태로 저장하기위한 전처리 and 저장
    for i in range(len(df)):
        obj_confi = round(df['confidence'][i], 2)
        obj_name = df['name'][i]
        x_min = int(df['xmin'][i])
        y_min = int(df['ymin'][i])
        x_max = int(df['xmax'][i])
        y_max = int(df['ymax'][i])
        obj_dict = {
                    'class' : obj_name, 
                    'confidence' : obj_confi,
                    'xmin' : x_min,
                    'ymin' : y_min,
                    'xmax' : x_max, 
                    'ymax' : y_max
        }
        obj_list.append(obj_dict)
    return obj_list

# img = cv2.imread(img_src, cv2.IMREAD_COLOR)
# img = cv2.resize(img, dsize=(0, 0), fx = resize_rate, fy = resize_rate, interpolation=cv2.INTER_AREA)

video_src = cv2.VideoCapture(0)

# def detect_iris(q):
alarm_cnt = 0
detect_cnt = 0
cnt = 7
while cv2.waitKey(20) < 0:
    ret, video = video_src.read()
    if not ret:
        break
    # video_s = cv2.resize(video, (0, 0), None, resize_rate, resize_rate)
    video = cv2.flip(video, 1)
    results = yolo_model(video)

    # 눈, 눈동자 좌우 구별 하기위한 list
    eye_list = []
    iris_list = []

    for result in results:
        xmin = int(result['xmin'])
        ymin = int(result['ymin'])
        xmax = int(result['xmax'])
        ymax = int(result['ymax'])
        if result['class'] == 'eye':
            cv2.rectangle(video, (xmin, ymin), (xmax, ymax), (255,255,0), 1)
            eye_list.append(result)
        if result['class'] == 'iris':
            x_len = xmax - xmin
            y_len = ymax - ymin
            cir_center = (int((xmax + xmin) / 2), int((ymax + ymin) / 2))
            cir_radius = ((x_len + y_len) / 4)
            cv2.circle(video, cir_center,int(cir_radius), (0,255,255),1)
            iris_list.append(result)
    # print("eye_list")
    # print(eye_list)
    # print("iris_list")
    # print(iris_list)
    # 오른쪽 눈인지 왼쪽 눈인지 식별 해주기 (좌표값으로 해주면 될거같음)
    if len(eye_list) == 2:
        if eye_list[0]['xmin'] > eye_list[1]['xmin']:
            cv2.putText(video, 'RE', (eye_list[0]['xmin'], eye_list[0]['ymin']-5),cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
            cv2.putText(video, 'LE', (eye_list[1]['xmin'], eye_list[1]['ymin']-5),cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
        else:
            cv2.putText(video, 'LE', (eye_list[0]['xmin'], eye_list[0]['ymin']-5),cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
            cv2.putText(video, 'RE', (eye_list[1]['xmin'], eye_list[1]['ymin']-5),cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)

    if len(iris_list) == 2:
        if iris_list[0]['xmin'] > iris_list[1]['xmin']:
            cv2.putText(video, 'RI', (iris_list[0]['xmin'], iris_list[0]['ymin']-5),cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
            cv2.putText(video, 'LI', (iris_list[1]['xmin'], iris_list[1]['ymin']-5),cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
        else:
            cv2.putText(video, 'LI', (iris_list[0]['xmin'], iris_list[0]['ymin']-5),cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
            cv2.putText(video, 'RI', (iris_list[1]['xmin'], iris_list[1]['ymin']-5),cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
        detect_cnt += 1
        print(f"detect_cnt  =  {detect_cnt}")
        if detect_cnt == 6:
            send_off_data = 'all_off'
            client_socket.sendall(send_off_data.encode())
            print(f"detect_cnt             =                6")
            alarm_cnt = 0
            detect_cnt = 0
    elif len(iris_list) == 0:
        alarm_cnt += 1
        print(alarm_cnt)
        if alarm_cnt == 3:
            send_led_data = 'led_1'
            client_socket.sendall(send_led_data.encode())
            print(f"send   {send_led_data}")
        elif alarm_cnt == 6:
            send_led_data = 'led_2'
            client_socket.sendall(send_led_data.encode())
            print(f"send   {send_led_data}")
        elif alarm_cnt == 9:
            send_led_data = 'led_3'
            client_socket.sendall(send_led_data.encode())
            print(f"send   {send_led_data}")
        elif alarm_cnt == 12:
            send_led_data = 'led_4'
            client_socket.sendall(send_led_data.encode())
            print(f"send   {send_led_data}")
        elif alarm_cnt == 15:
            send_led_data = 'led_5'
            client_socket.sendall(send_led_data.encode())
            print(f"send   {send_led_data}")
        elif alarm_cnt == 16:
            send_led_data = 'beep_on'
            client_socket.sendall(send_led_data.encode())
            print(f"send   {send_led_data}")
        elif alarm_cnt == 18:
            send_led_data = 'beep_off'
            client_socket.sendall(send_led_data.encode())
            print(f"send   {send_led_data}")
        elif alarm_cnt == 19:
            send_led_data = 'beep_on'
            client_socket.sendall(send_led_data.encode())
            print(f"send   {send_led_data}")
        elif alarm_cnt == 21:    
            send_led_data = 'all_off'
            client_socket.sendall(send_led_data.encode())
            print(f"send   {send_led_data}")
            alarm_cnt = 0
        detect_cnt = 0
    cv2.imshow('detect', video)

client_socket.close()
