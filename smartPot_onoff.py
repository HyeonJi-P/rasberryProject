import threading
from threading import Thread,Lock
import time
import smbus
import sys
sys.path.insert(0, '/home/pi/RPi_i2C_LCD_driver') #실행시 라이브러리를 못찾는 문제가 있어서 경로써주었음

import RPi_I2C_driver
import RPi.GPIO as GPIO
import spidev
import Adafruit_DHT #Adafruit 기능을 가져옴

############이메일 보내는 용도
from email.mime.text import MIMEText
import smtplib

#######

soil_moist=[0,0,0,0,0] #토양수분 10개의 값을 담을 리스트
temp=[0,0,0,0,0] #온도 리스트
hum=[0,0,0,0,0] #습도 리스트
illuminance=[0,0,0,0,0] #조도센서 리스트
State=[0,0,0] #현재상태리스트 [토양수분,온습도,빛]
preState=[0,0,0] #이전 사이클 상태리스트 [토양수분,온습도,빛]
LCD_State=[0,0,0] #LCD출력에 사용할 리스트(현재 과거 둘다이상시 1로기록)
#온도 평균계산용 
tempAvg=0
#습도 평균계산용
humAvg=0
#토양 평균계산용 
soilAvg=0
#illuminance avg
illumAvg=0
checkFlag=False #RGB LED용 센서값 읽는중인지 상태정리중인지 확인하는 변수
lock=Lock() #멀티쓰레드 lock기능
DHT11_sensor=True #센서상태가 정상인지 확인용
Soil_sensor=True
BH1750_sensor=True
DHT11=Adafruit_DHT.DHT11

#사용하는 핀 번호들(BCM)

GPIO.setmode(GPIO.BCM)

MOTER_A1 = 5 #팬1
MOTER_A2 = 6 #팬1

MOTER_B1 = 20 #팬2
MOTER_B2 = 21 #팬2

WATER_PUMP = 17 #워터펌프2

RGB_LED_R=18 #RGB LED
RGB_LED_G=23
RGB_LED_B=24
DHT11_PIN = 13 #온습도센서
RELAY=22 #22핀에 릴레이 연결

adcChannel=0 #adc채널 설정

lcd=RPi_I2C_driver.lcd(0x27) #LCD설정
lcd.clear()

I2C_CH = 1 #Light sensor 
BH1750_DEV_ADDR = 0x23
CONT_H_RES_MODE = 0X10
CONT_H_RES_MODE2 = 0X11
CONT_L_RES_MODE = 0X13
ONETIME_H_RES_MODE = 0x20
ONETIME_H_RES_MODE2 = 0x21
ONETIME_L_RES_MODE = 0x23
i2c = smbus.SMBus(I2C_CH)

spi=spidev.SpiDev() #아날로그컨버터(수분센서를 위함) 설정
spi.open(0,0)
spi.max_speed_hz=500000

#출력으로 설정

GPIO.setup(MOTER_A1,GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(MOTER_A2,GPIO.OUT, initial = GPIO.LOW)

GPIO.setup(MOTER_B1,GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(MOTER_B2,GPIO.OUT, initial = GPIO.LOW)

GPIO.setup(RGB_LED_R,GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(RGB_LED_G,GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(RGB_LED_B,GPIO.OUT, initial = GPIO.LOW)

GPIO.setup(WATER_PUMP,GPIO.OUT, initial = GPIO.LOW)
GPIO.setup(RELAY,GPIO.OUT, initial = GPIO.LOW)

#사용하는 클래스들
class temp_hum(Thread): #온습도 클레스
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        global temp,hum, tempAvg,humAvg,DHT11_sensor,DHT11_PIN
        try:
            if DHT11_sensor is True:
                for i in range(5):
                    
                    #DHT11 sensor read 10times
                    h, t = Adafruit_DHT.read_retry(DHT11, DHT11_PIN) #센서정보를 읽어오기 위한 코드
                    
                    if h is None and t is None:
                        print("Read Err")
                        raise Exception
                    
                    print("temp&hum read")
                    
                    hum[i]=h #리스트에 저장
                    temp[i]=t            
                    time.sleep(1) #센서 읽는 주기. 
                    if i==4:
                        tsum=0 #온도 합산용 지역변수
                        hsum=0 #습도 합산용 지역변수
                        for j in range(5):
                            tsum+=temp[j]
                            hsum+=hum[j]
                        tempAvg=tsum/5
                        humAvg=hsum/5
                        DHT11_sensor=True    #정상작동
                
        except :
            print("DHT11 sensor Error")
            DHT11_sensor=False #센서 에러
            s=smtplib.SMTP('smtp.gmail.com',587)
            s.starttls()
            s.login('pytest7674@gmail.com','kupuztoiqjdydsiy')
            msg = MIMEText('라즈베리파이 센서 오류!!')
            msg['Subject'] = '제목 : DHT11센서의 오류 발생'
            s.sendmail("pytest7674@gmail.com","hyunji7674@gmail.com",msg.as_string())
            s.quit()
            #############
            tempAvg=0
            humAvg=0
            preState[1]=1 #빠르게 오류를 출력하기 위해 preState값 변경

            
class soil(Thread): #토양수분 클레스
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        global soil_moist,soilAvg,Soil_sensor
        try:
            if Soil_sensor is True: 
                for i in range(5):
                    #lock.acquire() #lock
                    
                    adcValue=read_spi_adc(adcChannel) #수분값 adc 읽기
                    shum=100-int(map(adcValue,0,1023,0,100)) #몇퍼센트인지 변환
                    #soil sensor read 10time
                    
                    print("soilHum read ")
                    
                    soil_moist[i]=shum #리스트에 저장
                    #lock.release() #락 해제
                    
                    if i==4:
                        ssum=0 #토양수분 합산용 지역변수
                        for j in range(5):
                            ssum+=soil_moist[j]
                        soilAvg=ssum/5
                        Soil_sensor=True #토양수분센서 작동 정상
                    time.sleep(1) #센서 주기    
        except:
            Soil_sensor=False #토양수분센서 작동 비정상
            preState[0]=1 #빠르게 표시하기 위해 preState값 바꾸기
            s=smtplib.SMTP('smtp.gmail.com',587)
            s.starttls()
            s.login('pytest7674@gmail.com','kupuztoiqjdydsiy')
            msg = MIMEText('라즈베리파이 soil센서 오류!!')
            msg['Subject'] = '제목 : 토양수분센서의 오류 발생'
            s.sendmail("pytest7674@gmail.com","hyunji7674@gmail.com",msg.as_string())
            s.quit()

#빛센서 클레스
class light(Thread): 
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        global illuminance, BH1750_sensor, illumAvg
        try: 
            for i in range(5):
                #lock.acquire() #lock
                luxBytes = i2c.read_i2c_block_data(BH1750_DEV_ADDR, CONT_H_RES_MODE,2)
                lux = int.from_bytes(luxBytes, byteorder='big')
                
                
                #bh1750 sensor read 5time
                
                print("illuminance read ")
                print('{0} lux'.format(lux))
                illuminance[i]=lux #리스트에 저장
                #lock.release() #락 해제
                
                if i==4:
                    illum =0 #illuminance 합산용 지역변수
                    for j in range(5):
                        illum+= illuminance[j]
                    illumAvg=illum/5
                    if illumAvg <=1 :
                        BH1750_sensor=False
                        raise ValueError()
                    else :
                        BH1750_sensor=True #센서 작동 정상    
                    
                time.sleep(1) #센서 주기    
        except ValueError :
            BH1750_sensor=False #토양수분센서 작동 비정상
            preState[0]=1 #빠르게 표시하기 위해 preState값 바꾸기
            s=smtplib.SMTP('smtp.gmail.com',587)
            s.starttls()
            s.login('pytest7674@gmail.com','kupuztoiqjdydsiy')
            msg = MIMEText('라즈베리파이 센서 오류')
            msg['Subject'] = '제목 : 조도센서의 오류 발생'
            s.sendmail("pytest7674@gmail.com","hyunji7674@gmail.com",msg.as_string())
            s.quit()
     
#사용되는 함수

def read_spi_adc(adcChannel): #adc 읽는 함수
    adcValue=0
    buff=spi.xfer2([1,(8+adcChannel)<<4,0])
    adcValue = ((buff[1]&3)<<8)+buff[2]
    return adcValue
def map(value,min_adc,max_adc,min_hum,max_hum): #0에서1024를 보기편하게 퍼센트로 변환
    adc_range=max_adc-min_adc
    hum_range=max_hum-min_hum
    scale_factor=float(adc_range)/float(hum_range)
    return min_hum+((value-min_adc)/scale_factor)

def prt(): #테스트 출력
    global soilAvg,tempAvg,humAvg
    print('DHT11 :',DHT11_sensor)
    print('moist :',Soil_sensor)
    print('Light :',BH1750_sensor)
    print('soil moist avg is: {}'.format(soilAvg))
    print('temp is: {} hum is: {}'.format(tempAvg,humAvg))
    

def led_bar(mode): #LED 바 설정함수
    if mode == 1:
        #ON
        GPIO.output(RELAY,GPIO.HIGH) 
        print("led bar: ON")
        
    else : 
        #OFF
        GPIO.output(RELAY,GPIO.LOW)
        print("led bar: OFF")
        
    
def RGB_LED_light( soil, air, lighting): #RGBLED 함수
    while True:
        
        GPIO.output(RGB_LED_R,GPIO.LOW) #초기화
        GPIO.output(RGB_LED_G,GPIO.LOW) #불끄기
        GPIO.output(RGB_LED_B,GPIO.LOW)
        
        if checkFlag==False: #모두 join될때 중지
            print("RGB function Break!")
            break
        else:
            if(LCD_State[0]==1 and LCD_State[1]==1 and LCD_State[2]==1):
                #빨강
                
                GPIO.output(RGB_LED_R,GPIO.HIGH)
                GPIO.output(RGB_LED_G,GPIO.LOW)
                GPIO.output(RGB_LED_B,GPIO.LOW)
                
                print("RGB: RED")
                time.sleep(1)
            elif(LCD_State[0]==0 and LCD_State[1]==0 and LCD_State[2]==0):
                #초록(정상)
                
                GPIO.output(RGB_LED_R,GPIO.LOW)
                GPIO.output(RGB_LED_G,GPIO.HIGH)
                GPIO.output(RGB_LED_B,GPIO.LOW)
                
                print("RGB: GREEN")
                time.sleep(1) 
            elif(LCD_State[0]==1 and LCD_State[1]==0 and LCD_State[2]==0):
                #파랑
                
                GPIO.output(RGB_LED_R,GPIO.LOW)
                GPIO.output(RGB_LED_G,GPIO.LOW)
                GPIO.output(RGB_LED_B,GPIO.HIGH)
                
                print("RGB: BLUE")
                time.sleep(1)
            elif(LCD_State[0]==0 and LCD_State[1]==1 and LCD_State[2]==0):
                #노랑
                    
                GPIO.output(RGB_LED_R,GPIO.HIGH)
                GPIO.output(RGB_LED_G,GPIO.HIGH)
                GPIO.output(RGB_LED_B,GPIO.LOW)
                
                print("RGB: YELLOW")
                time.sleep(1)   
            elif(LCD_State[0]==0 and LCD_State[1]==0 and LCD_State[2]==1):
                #하양
                
                GPIO.output(RGB_LED_R,GPIO.HIGH)
                GPIO.output(RGB_LED_G,GPIO.HIGH)
                GPIO.output(RGB_LED_B,GPIO.HIGH)
                
                print("RGB: WHITE")
                time.sleep(1)
            else: #두가지 문제
                print("RGB: 2 Problem")
                if(LCD_State[0]==1):
                    #파랑
                    
                    GPIO.output(RGB_LED_R,GPIO.LOW)
                    GPIO.output(RGB_LED_G,GPIO.LOW)
                    GPIO.output(RGB_LED_B,GPIO.HIGH)
                    
                    print("RGB: BLUE")
                    time.sleep(1)
                    
                    GPIO.output(RGB_LED_R,GPIO.LOW) #초기화
                    GPIO.output(RGB_LED_G,GPIO.LOW) #불끄기
                    GPIO.output(RGB_LED_B,GPIO.LOW)
                    
                    print("RGB: OFF")
                    time.sleep(1)
                if(LCD_State[1]==1):
                    #노랑
                    
                    GPIO.output(RGB_LED_R,GPIO.HIGH)
                    GPIO.output(RGB_LED_G,GPIO.HIGH)
                    GPIO.output(RGB_LED_B,GPIO.LOW)
                    
                    print("RGB: YELLOW")
                    time.sleep(1)
                    
                    GPIO.output(RGB_LED_R,GPIO.LOW) #초기화
                    GPIO.output(RGB_LED_G,GPIO.LOW) #불끄기
                    GPIO.output(RGB_LED_B,GPIO.LOW)
                    
                    print("RGB: OFF")
                    time.sleep(1)
                if(LCD_State[2]==1):
                    #하양
                    
                    GPIO.output(RGB_LED_R,GPIO.HIGH)
                    GPIO.output(RGB_LED_G,GPIO.HIGH)
                    GPIO.output(RGB_LED_B,GPIO.HIGH)
                    
                    print("RGB: WHITE")
                    time.sleep(1)
                    print("RGB: OFF")
                    
                    GPIO.output(RGB_LED_R,GPIO.LOW) #초기화
                    GPIO.output(RGB_LED_G,GPIO.LOW) #불끄기
                    GPIO.output(RGB_LED_B,GPIO.LOW)
                    time.sleep(1)
                    

def WaterPump (): #워터펌프 함수
    #n초간 워터펌프 작동==급수
    
    GPIO.output(WATER_PUMP,GPIO.HIGH) #작동
    print("WaterPump: ON")
    time.sleep(3) #임의의 값. 이후 식물 흙 량에 맞추어 조정 필요
    GPIO.output(WATER_PUMP,GPIO.LOW) #멈춤
    print("WaterPump: OFF")

#실질적인 동작부분 코드
while True: #실행
    try:
        sensor_list=[] #두 센서를 넣을 리스트
        soil_ss=soil() #토양수분센서
        tempHum_ss=temp_hum() #온습도센서
        illum_ss=light() #조도센서
        sensor_list.append(soil_ss) #센서리스트에 추가
        sensor_list.append(tempHum_ss) #센서리스트에 추가
        sensor_list.append(illum_ss) #센서리스트에 추가
        soil_ss.start() #시작
        tempHum_ss.start() #시작
        illum_ss.start() #시작
        checkFlag=True #RGB LED 체크확인용

        #RGBLED 표시 시작 (LCD상태를 기반, 첫 표시는 초록)
        RGBLED=threading.Thread(target=RGB_LED_light, args=(LCD_State[0],LCD_State[1],LCD_State[2]))
        RGBLED.start()

        for sensor in sensor_list: #센서 일끝날때까지 기다리기 (RGB LED도 종료될 것)
            sensor.join()
        checkFlag=False #RGB LED 체크확인용
        
        prt() #터미널로 확인하기위한 함수(테스트용)
        
        if (soilAvg<10.0) or Soil_sensor==False : #평균값과 기준값 비교, 센서이상여부
            State[0]=1 # 이상있음
        else:
            State[0]=0 #이상없음
        
        if DHT11_sensor==False: #센서이상
            State[1]=1    
        elif (tempAvg<30.0) and (humAvg<30.0) :
            # 정상
            State[1]=0
        elif (humAvg>=60) or (tempAvg>=30) :
            State[1]=1

        if BH1750_sensor == False : #센서이상
            State[2]=1 
            
        elif illumAvg < 500 :
            # 어두움
            State[2]=1
        elif illumAvg >= 5000 :
            #충분히 밝음
            State[2]=1
        else :
            State[2]=0
   
        #state 리스트 정리
        for i in range(3):
            if State[i]==1 and preState[i]==1: #과거도 이상,현재도 이상이면 ,LCD 상태배열에 갱신
                #Error
                LCD_State[i]=1
            else: #둘중에 하나라도 아니면 잠시 오류라 생각하고 패스, LCD 상태배열에 갱신
                LCD_State[i]=0
        
        print('State Update State[0]:{},[1]:{},[2]:{}'.format(State[0],State[1],State[2]))    
        print('LCD Update LCD State[0]:{},[1]:{},[2]:{}'.format(LCD_State[0],LCD_State[1],LCD_State[2]))    
        
        #lcd 작동
        lcd.clear()
        #lcd.setCursor(0,0) #윗줄에 상태출력
        
        print('LCD: T:{}, H:{}'.format(tempAvg,humAvg))
        if LCD_State[1]==1 and LCD_State[0]==1 and LCD_State[2]==1 : #토양습도,온습도,빛
            lcd.print("Total Error")
            print("LCD: TOTAL Error")
            led_bar(1)#LED Bar On 
            if(Soil_sensor==True): #센서가 정상인 경우에만 워터펌프 작동
                     WaterPump()
            if(DHT11_sensor==True): #센서가 정상일 경우
                    #출력값 차이로 팬 가동
                    print("MOTOR: A1&A2 ON")
                    
                    GPIO.output(MOTER_A1,GPIO.HIGH)
                    GPIO.output(MOTER_A2,GPIO.LOW)
                    
                    GPIO.output(MOTER_B1, GPIO.HIGH)
                    GPIO.output(MOTER_B2, GPIO.LOW)
        elif LCD_State[1]==0 and LCD_State[0]==0 and LCD_State[2]==0:
            #정상인 경우 조도값 출력
            lcd.print(" Lux:"+str(illumAvg))
            led_bar(0)#LED Bar On =>OFF
            #출력값을 같게하여 팬 멈춤, 정상
            print("MOTOR: A1&A2 OFF")
                
            GPIO.output(MOTER_A1,GPIO.LOW)
            GPIO.output(MOTER_A2,GPIO.LOW)
            GPIO.output(MOTER_B1, GPIO.LOW)
            GPIO.output(MOTER_B2, GPIO.LOW)    
                
            print("LCD: ALL OK")
            
            
        else:
            if LCD_State[0]==1 :
                lcd.print("Soil ")
                print("LCD: Soil ")
                #water pump fuction
                
                if(Soil_sensor==True): #센서가 정상인 경우에만 워터펌프 작동
                     WaterPump()
                
            if LCD_State[1]==1 :
                lcd.print("Air ")
                print("LCD: Air ")
                #fan function
                if(DHT11_sensor==True): #센서가 정상일 경우
                    #출력값 차이로 팬 가동
                    print("MOTOR: A1&A2 ON")
                    
                    GPIO.output(MOTER_A1,GPIO.HIGH)
                    GPIO.output(MOTER_A2,GPIO.LOW)
                    
                    GPIO.output(MOTER_B1, GPIO.HIGH)
                    GPIO.output(MOTER_B2, GPIO.LOW)
                    
                else: #센서가 비정상인 경우 중지
                    print("tempS Err?")
                    GPIO.output(MOTER_A1,GPIO.LOW)
                    GPIO.output(MOTER_A2,GPIO.LOW)
                    
                    GPIO.output(MOTER_B1, GPIO.LOW)
                    GPIO.output(MOTER_B2, GPIO.LOW)    
                    

            else:
                #출력값을 같게하여 팬 멈춤, 정상
                print("MOTOR: A1&A2 OFF")
                
                GPIO.output(MOTER_A1,GPIO.LOW)
                GPIO.output(MOTER_A2,GPIO.LOW)
                
                GPIO.output(MOTER_B1, GPIO.LOW)
                GPIO.output(MOTER_B2, GPIO.LOW)    
                

            if LCD_State[2]==1 :
                lcd.print("Light ")
                print("LCD: Light")
                #led bar function
                led_bar(1) #LED바 작동
            else:
                led_bar(0) #LED바 끄기
            
            lcd.print("Err")
            print("LCD: Err")

        lcd.setCursor(0,1) #아랫줄에 온도출력
        lcd.print("T:"+str(tempAvg)+" H:"+str(humAvg))
        
#move
        #move 현재상태를 과거상태로 옮기고 다음 사이클 준비
        print("       State --> preState")
        for k in range(3): 
            preState[k]=State[k]
        time.sleep(3) #한 사이클 후 잠시 휴식(?)
    except KeyboardInterrupt: #ctrl+C 누르면 긴급 종료
        print("KeyboardInterrupt")
        break
#중지
print("STOP")
GPIO.cleanup() #all stop

