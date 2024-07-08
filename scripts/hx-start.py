#Read data from HX711. To be called upon, and filtered by Node-RED.
try:
    #import logging
    import RPi.GPIO as gpio
    gpio.setwarnings(False)
    gpio.cleanup() 
    gpio.setmode(gpio.BOARD)

    from hx711 import HX711
    hx = HX711(dout_pin=29, pd_sck_pin=31)
    hx.reset()

    while True: #Infinite loop...
        hx_reading = hx._read()
        print(hx_reading) #Echo reading to Standard Out Stream. May include "False" and otherwise weird readings
except: 
    gpio.cleanup() #Node-RED will PKILL this process, so Except clause will never clean up GPIO :(
    