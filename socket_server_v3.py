import socket
import gpiod
import time

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_host = '0.0.0.0'  
server_port = 12345  
server_socket.bind((server_host, server_port))
server_socket.listen(1)  

trigger_pin = 17  

DIGIT = (14,15,18,27,22)

leds = []

chip = gpiod.Chip('gpiochip4')  

for i in DIGIT:
   line = chip.get_line(i)
   line.request(consumer="", type=gpiod.LINE_REQ_DIR_OUT)
   leds.append(line)

line = chip.get_line(trigger_pin)
line.request(consumer="", type=gpiod.LINE_REQ_DIR_OUT)

print("server start")

client_socket, client_address = server_socket.accept()
print(f"{client_address} is connect")


led_cnt = 0
while True:
    data = client_socket.recv(1024).decode()
    if not data:
        break  
    if data == 'led_1':
        leds[0].set_value(1)
    elif data == 'led_2':
        leds[1].set_value(1)
    elif data == 'led_3':
        leds[2].set_value(1)
    elif data == 'led_4':
        leds[3].set_value(1)
    elif data == 'led_5':
        leds[4].set_value(1)
        flag = 0
        while flag < 2:
            line.set_value(1)  
            time.sleep(0.5)  
            line.set_value(0)  
            time.sleep(0.5)  
            flag += 1
        for i in leds:
            i.set_value(0)
    if data == 'all_off':
        line.set_value(0)
        for i in leds:
            i.set_value(0)

client_socket.close()
server_socket.close()
