#OLED src: https://randomnerdtutorials.com/raspberry-pi-pico-ssd1306-oled-micropython/
#PMS7003 src: https://github.com/pkucmus/micropython-pms7003
#Async web server: https://gist.github.com/aallan/3d45a062f26bc425b22a17ec9c81e3b6
from machine import Pin, SoftI2C
import machine
import ssd1306
import dht
import time
from pms7003 import Pms7003
import gc
import network, ntptime
import uasyncio as asyncio
from machine import WDT

#####################################################
# Configs
#####################################################

from config import *


#HTML Template
html = """<!DOCTYPE html>
<html>
    <head> <title>ESP8266 Node</title> <meta http-equiv="refresh" content="5"> </head>
    <body> <h1> PIAI 321</h1>
        <p>%s</p>
    </body>
</html>
"""

#####################################################
# Sensor init
#####################################################
OLED_I2C = SoftI2C(scl=OLED_SCL, sda=OLED_SDA)

oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, OLED_I2C)
dht22 = dht.DHT22(DHT22_PIN)
cds = machine.ADC(CDS_ADC_PIN)
pms = Pms7003(UART_TX,UART_RX)
    
if(WIFI_ENABLE):
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(SSID, WPA_PASSKEY)
        cnt = 0
        while not sta_if.isconnected() and cnt < 10:
            time.sleep(1)
            cnt += 1
            
    if not sta_if.isconnected():
        WIFI_ENABLE = False
        print('no network.')
    else:
        print('network config:', sta_if.ifconfig())
        ntptime.settime()	

#wdt = WDT(timeout=UPDATE_INTERVAL*1000*4) #ESP8266 won't do it
wdt = WDT()

####################################################
# Main loop
#####################################################
cds_read = None
pms_data = None
time_current = None

async def serve_client(reader, writer):
    global WIFI_ENABLE;
    
    if( not(WIFI_ENABLE)):
        pass
    
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    request = str(request_line)
    year, month, day, hour, _min, sec, _, _ = (time_current)
    date_format = "{:04d}/{:02d}/{:02d}"    
    time_format = "{:02d}:{:02d}:{:02d}"    
    stateis='date: '+date_format.format(year,month,day) +"<br>"
    stateis+= 'time: '+time_format.format(hour, _min, sec)+"<br>"
    stateis+= 'temp: '+str(dht22.temperature())+" C <br>"
    stateis+= 'hum: '+str(dht22.humidity())+"% <br>"
    stateis+= 'cds: '+str(cds_read) + "<br>"
    stateis+='PM10.0: '+str(pms_data['PM10_0_ATM'])+ "<br>"
    stateis+='PM2.5 : '+str(pms_data['PM2_5_ATM'])+ "<br>"
    stateis+='PM1.0 : '+str(pms_data['PM1_0_ATM'])+ "<br>"

        
    response = html % stateis
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")
    
async def main():
    global cds_read, pms_data, time_current
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    
    cnt = 0
    while True:
        dht22.measure()
        cds_read = cds.read()
        pms_data = pms.read()
        time_current = time.localtime(time.time() + TIMEZONE)
        if(cnt % NTP_SYNC_INTERVAL == 0 and WIFI_ENABLE):
            try:
                ntptime.settime()
            except:
                pass
         
        oled.fill(0)
        #oled.text('dat: '+str(time_current[0])+"/"+str(time_current[1])+"/"+str(time_current[2]), 0, 0)
        
        _, _, _, hour, _min, sec, _, _ = (time_current)
        time_format = "{:02d}:{:02d}:{:02d}"
        oled.text('time: '+time_format.format(hour, _min, sec) , 0, 0)
         
        oled.text('temp: '+str(dht22.temperature())+"C", 0, 10)
        oled.text('hum: '+str(dht22.humidity())+"%", 0, 20)
        #oled.text('cds: '+str(cds_read), 0, 30)
        oled.text('PM10.0: '+str(pms_data['PM10_0_ATM']), 0, 30)
        oled.text('PM2.5 : '+str(pms_data['PM2_5_ATM']), 0, 40)
        oled.text('PM1.0 : '+str(pms_data['PM1_0_ATM']), 0, 50)

        oled.show()
        await asyncio.sleep(UPDATE_INTERVAL)
        cnt += 1
        gc.collect()
        print(gc.mem_free())
        wdt.feed()


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
