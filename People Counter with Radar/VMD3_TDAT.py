# Simple script to read out PDAT and TDAT from RFbeam V-MD3
# Author:   RFbeam Microwave GmbH
# Python Version: 3.7.4

import socket
import sys
import matplotlib.pyplot as plt
import math
import time
import requests
import json

DREAMUG_URL = "Target url"
json_data = {}

def send_data(val):
    now = time.localtime()
    datetime = time.strftime('%Y-%m-%d-%H-%M', now)

    json_data["isRegularData"] = True
    json_data["dataString"] = []
    json_data["dataString"].append({
            "tra_lat":"*****",
            "tra_lon":"*****",
            "tra_datetime":datetime,
            "tra_temp":str(val),
            "de_number":"legaro_proto4"})

    #로그용으로 사용
    with open("./sample.json", 'w') as outfile:
        json.dump(json_data, outfile)
    print(json_data)

    #호출 결과를 result에 담는다.
    result = requests.post(DREAMUG_URL, data=json.dumps(json_data))

    #드림머그 서버가 응답한 값 : 정상이면 {"status_code":"0","message":"Success","result":넘긴targetdata} 반환
    # 만약 result에 null이 찍히면 값이 제대로 안 넘어간 것
    #result.json으로 써도되기는 한데 서버가 이상해서 json으로 안뱉을까봐 그냥 text로 사용
    #result로 찍어볼 수 있는 다양한 값들 참고
    #https://dgkim5360.tistory.com/entry/python-requests 여기서 4번 참고
    print(result.text)

def recv_msg(sockTCP, msg_len, max_msg_size):
    resp_frame = bytearray(msg_len)
    pos = 0
    while pos < msg_len:
        resp_frame[pos:pos + max_msg_size] = sockTCP.recv(max_msg_size)
        pos += max_msg_size
    return resp_frame

# Define variables
msg_len = 9
max_msg_size = 8
packageLength = 1500
x = list(range(128))
print("TCP connect start")

# Create TCP_IP object with corresponding IP and port
TCP_IP = '192.168.100.201'
TCP_PORT = 6172
sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sockTCP.connect((TCP_IP, TCP_PORT))
except:
    print('Error while connecting with TCP/IP socket')
    sys.exit(1)
print("connect success")



print("UDP connect start")
# Create UDP object with corresponding IP and port
UDP_IP = "192.168.100.1"
UDP_PORT = 4567
sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
try:
    sockUDP.bind((UDP_IP, UDP_PORT))
except:
    print('Error while connecting with UDP socket')
    sys.exit(1)
print("UDP connect success")

print("seosor connect start")
# Connect with sensor
header = bytes("INIT", 'utf-8')
payloadlength = (0).to_bytes(4, byteorder='little')
cmd_frame = header + payloadlength
sockTCP.send(cmd_frame)
print("send frame to Radar server")
resp_frame = recv_msg(sockTCP, msg_len, max_msg_size)
if resp_frame[8] != 0:
    print('Error: Command not acknowledged')
    sys.exit(1)
print("seosor connect success")

try:
    # Set max range to 10m
    header = bytes("RSET", 'utf-8')
    payloadlength = (4).to_bytes(4, byteorder='little')
    max_range = (1).to_bytes(4, byteorder='little')
    cmd_frame = header + payloadlength + max_range
    sockTCP.send(cmd_frame)
    resp_frame = recv_msg(sockTCP, msg_len, max_msg_size)
    if resp_frame[8] != 0:
        print('Error: Command not acknowledged')
        sys.exit(1)
    print("here")
    # Create figure
    fig = plt.figure(figsize=(10, 5))
    plt.ion()
    plt.show()
    # Enable PDAT and TDAT data
    header = bytes("RDOT", 'utf-8')
    datarequest = (24).to_bytes(4, byteorder='little')
    cmd_frame = header + payloadlength + datarequest
    sockTCP.send(cmd_frame)
    resp_frame = recv_msg(sockTCP, msg_len, max_msg_size)
    
    
    index = 0
    # readout and plot time and frequency adc_data continuously
    for ctr in range(10):
        index += 1
        # GET PDAT DATA ---------------------------------
        pdat_data = []
        packageData, adr = sockUDP.recvfrom(packageLength)
        while packageData[0:4] != b'PDAT':  # do while header isn't expected header
            packageData, adr = sockUDP.recvfrom(packageLength)
        respLength = int.from_bytes(packageData[4:8], byteorder='little')  # get response length
        numberoftargets = round(respLength / 10)  # calculate number of detected targets
        packageData = packageData[8:len(packageData)]  # exclude header from data
        pdat_data = packageData  # store data
        packageData, adr = sockUDP.recvfrom(packageLength)  # get data
        while packageData.find(b'TDAT') == -1:
            pdat_data += packageData  # store data
            packageData, adr = sockUDP.recvfrom(packageLength)  # get data
    
        # GET TDAT DATA -------------------------------
        respLength = int.from_bytes(packageData[4:8], byteorder='little')  # get response length
        numberoftrackedtargets = round(respLength / 10)  # calculate number of tracked targets
        packageData = packageData[8:len(packageData)]  # exclude header from data
        tdat_data = packageData  # store data
        packageData, adr = sockUDP.recvfrom(packageLength)  # get data
        while packageData.find(b'PDAT') == -1:
            tdat_data += packageData  # store data
            packageData, adr = sockUDP.recvfrom(packageLength)  # get data
    
        # init arrays
        distance_pdat = []
        speed_pdat = []
        azimuth_pdat = []
        elevation_pdat = []
        magnitude_pdat = []
        distance_tdat = []
        speed_tdat = []
        azimuth_tdat = []
        elevation_tdat = []
        magnitude_tdat = []
        print("numberoftrackedtargets : ", numberoftrackedtargets)
        # get distance [cm], speed [km/h*100] and azimuth angle [degree*100] of the detected raw targets by converting pdat into uint16/int16
        for target in range(0, numberoftargets):
            distance_pdat.append(int.from_bytes(pdat_data[10 * target:10 * target + 2], byteorder='little', signed=False))
            speed_pdat.append(
                int.from_bytes(pdat_data[10 * target + 2:10 * target + 4], byteorder='little', signed=True) / 100)
            azimuth_pdat.append(
                math.radians(
                    int.from_bytes(pdat_data[10 * target + 4:10 * target + 6], byteorder='little', signed=True) / 100))
            elevation_pdat.append(
                math.radians(
                    int.from_bytes(pdat_data[10 * target + 6:10 * target + 8], byteorder='little', signed=True) / 100))
            magnitude_pdat.append(
                int.from_bytes(pdat_data[10 * target + 8:10 * target + 10], byteorder='little', signed=False))
    
        # get distance [cm], speed [km/h*100] and azimuth angle [degree*100] of the tracked targets by convert tdat data into uint16/int16
        for target in range(0, numberoftrackedtargets):
            distance_tdat.append(int.from_bytes(tdat_data[10 * target:10 * target + 2], byteorder='little', signed=False))
            speed_tdat.append(
                int.from_bytes(tdat_data[10 * target + 2:10 * target + 4], byteorder='little', signed=True) / 100)
            azimuth_tdat.append(
                math.radians(
                    int.from_bytes(tdat_data[10 * target + 4:10 * target + 6], byteorder='little', signed=True) / 100))
            elevation_tdat.append(
                math.radians(
                    int.from_bytes(tdat_data[10 * target + 6:10 * target + 8], byteorder='little', signed=True) / 100))
            magnitude_tdat.append(
                int.from_bytes(tdat_data[10 * target + 8:10 * target + 10], byteorder='little', signed=False))
    
        # clear figure
        plt.clf()
    
        # calculate x and y coordinates and plot the detected raw targets
        sub1 = fig.add_subplot(121)
        distance_x = 0
        distance_y = 0
        linecolor = ''
        for target in range(0, numberoftargets):
            distance_x = distance_pdat[target] * math.sin(azimuth_pdat[target]) / 100
            distance_y = distance_pdat[target] * math.cos(azimuth_pdat[target]) / 100
            if speed_pdat[target] > 0.5:
                linecolor = 'g'
            elif speed_pdat[target] < -0.5:
                linecolor = 'r'
            else:
                linecolor = 'b'
            lines = sub1.plot(distance_x, distance_y, marker='o', markersize=10, color=linecolor, linestyle='None')
        sub1.grid(True)
        sub1.axis([-10, 10, 0, 10])
        plt.title(
            'Raw targets range/range (Nb. of targets: ' + str(numberoftargets) + ') \n (Green: Receding, Red: Approaching)')
        plt.xlabel('Distance [m]')
        plt.ylabel('Distance [m]')
        close_count = 0
        far_count = 0
        stop_count = 0
        # calculate x and y coordinates and plot the tracked targets
        sub2 = fig.add_subplot(122)
        for target in range(0, numberoftrackedtargets):
            distance_x = distance_tdat[target] * math.sin(azimuth_tdat[target]) / 100
            distance_y = distance_tdat[target] * math.cos(azimuth_tdat[target]) / 100
            if speed_tdat[target] > 0.5:
                linecolor = 'g'
                far_count += 1
            elif speed_tdat[target] < -0.5:
                linecolor = 'r'
                close_count += 1
            else:
                linecolor = 'b'
                stop_count += 1
            lines = sub2.plot(distance_x, distance_y, marker='o', markersize=10, color=linecolor, linestyle='None')
        print("close object : ", close_count)
        print("far object : ", far_count)
        print("stop object : ", stop_count)
        if index == 5:
            send_data(numberoftrackedtargets)
            index = 0
            
        sub2.grid(True)
        sub2.axis([-10, 10, 0, 10])
        plt.title('Tracked targets range/range (Nb. of targets: ' + str(
            numberoftrackedtargets) + ') \n (Green: Receding, Red: Approaching)')
        plt.xlabel('Distance [m]')
        plt.ylabel('Distance [m]')
        
        # draw plots
        fig.canvas.draw()
        fig.canvas.flush_events()
    print("graph make success")
    plt.show()
except:
    # disconnect from sensor
    payloadlength = (0).to_bytes(4, byteorder='little')
    header = bytes("GBYE", 'utf-8')
    cmd_frame = header + payloadlength
    sockTCP.send(cmd_frame)    
    # close connection to TCP/IP
    sockTCP.close()
    # close connection to UDP
    sockUDP.close()
    
# disconnect from sensor
payloadlength = (0).to_bytes(4, byteorder='little')
header = bytes("GBYE", 'utf-8')
cmd_frame = header + payloadlength
sockTCP.send(cmd_frame)

# get response
response_gbye = recv_msg(sockTCP, msg_len, max_msg_size)
if response_gbye[8] != 0:
    print('Error during disconnecting with V-MD3')
    sys.exit(1)
# close connection to TCP/IP
sockTCP.close()
# close connection to UDP
sockUDP.close()