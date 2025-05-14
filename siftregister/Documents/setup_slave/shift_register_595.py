"""
this file intialize the pins of the 74hc595 shift register (Serial to Parallel), 
which allow us to extend the LEDs in our mockup.
To undrestand how the 74hc595 works you can refer to the python file below
/test/LEDs.py
"""
import RPi.GPIO as GPIO

# Define Connections to 74HC595
Latch = 13 # sets the RCLK (Register Clock / Latch) to the GPIO pin 15
Clock = 15 # sets the SRCLK (Shift Register Clock) to the GPIO pin 13
Serial_Input = 11 # sets the Serial_Input to the GPIO pin 11
Clear = 7 # sets the Shift Register Clear to the GPIO pin 7

# Setup gpio config
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(Clock, GPIO.OUT)
GPIO.setup(Latch, GPIO.OUT)
GPIO.setup(Clear, GPIO.OUT)
GPIO.setup(Serial_Input, GPIO.OUT)

def Display(LEDs_status: list[int] = [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]):
    
    for state in LEDs_status:
        GPIO.output(Serial_Input, state)
        # each loop generate a clock signal 
        # to shift the Serial input in the shift register
        GPIO.output(Clock, 0)
        GPIO.output(Clock, 1)

    # turn the LEDs
    GPIO.output(Latch, 0)
    GPIO.output(Latch, 1)