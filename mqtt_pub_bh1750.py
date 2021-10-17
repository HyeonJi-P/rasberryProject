#-*- coding:utf-8 -*-
import json
import time
import RPi_I2C_driver
import sys
sys.path.insert(0, '/home/pi/.local/lib/python2.7/site-packages')
sys.path.insert(0, '/home/pi/RPi_i2C_LCD_driver') #실행시 라이브러리를 못찾는 문제가 있어서 경로써주었음
import paho.mqtt.client as mqtt
import spidev

illuminance=[0,0,0,0,0] #조도센서 리스트
#광량 평균계산
illumAvg=0

I2C_CH = 1 #Light sensor 
BH1750_DEV_ADDR = 0x23
CONT_H_RES_MODE = 0X10
CONT_H_RES_MODE2 = 0X11
CONT_L_RES_MODE = 0X13
ONETIME_H_RES_MODE = 0x20
ONETIME_H_RES_MODE2 = 0x21
ONETIME_L_RES_MODE = 0x23
i2c = smbus.SMBus(I2C_CH)

client = mqtt.Client() #Mqtt Client 오브젝트 생성
client.username_pw_set("m06xDEKnu6ttqRltcTc4")
client.connect("demo.thingsboard.io", 1883) #MQTT 서버에 연결


for i in range(5):
    #조도센서
    luxBytes = i2c.read_i2c_block_data(BH1750_DEV_ADDR, CONT_H_RES_MODE,2)
    lux = int.from_bytes(luxBytes, byteorder='big')
    print('{0} lux'.format(lux))

    print("illuminance read ")
    illuminance[i]=lux #리스트에 저장
    if i==4:
        illum =0 #illuminance 합산용 지역변수
        for j in range(5):
            illum+= illuminance[j]
        illumAvg=illum/5
    time.sleep(1) #센서 주기    



sensor_data = {'light':illumAvg}
print(sensor_data)
client.publish("v1/devices/me/telemetry", json.dumps(sensor_data),1) #토픽과 메세지 발행


client.loop(2) #timeout 2sec.

