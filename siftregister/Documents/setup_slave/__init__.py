from setup_slave.shift_register_595 import Display
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
