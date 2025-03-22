from machine import Pin
import machine

#Pins
OLED_SCL = Pin(13)
OLED_SDA = Pin(12)
OLED_WIDTH = 128

OLED_HEIGHT = 64
DHT22_PIN = Pin(16)
CDS_ADC_PIN = 0
UPDATE_INTERVAL = 0.5 # Seconds 
UART_TX = machine.Pin(4)
UART_RX = machine.Pin(5)

TIMEZONE = 9 * 60 * 60

#WiFi
WIFI_ENABLE=True
SSID="" # CHANGEME
WPA_PASSKEY="" # CHANGEME
NTP_SYNC_INTERVAL = 86400 #each tick = UPDATE_INTERVAL
