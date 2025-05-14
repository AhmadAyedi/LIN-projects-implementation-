# author: Heni Elloumi 
# you can contact me via my email: henii.elloumi@gmail.com
"""
To undrestand the code below we need to undrestand
how the 74HC165 shift register work.

                     | | | | | | | |
                    ++-+-+-+-+-+-+-++
                    |               |
                    |   74HC165    ++
                    |              ++
                    |               |
                    ++-+-+-+-+-+-+-++
                     | | | | | | | |

The 74HC165 is an 8-bit parallel-in/serial-out shift register, 
meaning that it can take in 8 bits of data in parallel (all at once) 
and then shift them out one at a time in serial (one after the other). 
It's commonly used to expand the number of input pins available 
on a microcontroller or other digital circuit.

Here's a step-by-step explanation of how the 74HC165 works:
                                       __
1.  The 74HC165 has two input pin, "SH/LD" (Shift/Load Bar) , 
    which determines whether the chip is in shift mode or load mode, 
    and "Clock", and one output pin, "data".       __
    To use the chip, you first need to set the "SH/LD" pin to low. 
    This tells the chip to load the 8 bits of data from its input pins 
    into its internal storage registers regardless of the "Clock" signal.
                                  __
2.  Next, you need to set the "SH/LD" pin to high. This tells the chip
    to start shifting out the data from its internal storage registers, 
    one bit at a time, with each rising edge of the clock. 
    The first bit to be shifted out will be the Most Significant Bit (MSB).

3.  The "Clock" pulse can be triggered by any suitable clock source, 
    such as an oscillator or a microcontroller output pin.
    But in our code we will generate the clock signal, we will not use an oscillator.

4.  The "data" output pin will reflect the current bit being shifted out. 
    After 8 clock pulses, all 8 bits will have been shifted out and the chip will be 
    ready to receive another load command to start the process over again.
                                                                           __
5.  Note that the load mode is asynchronous, which means that once the "SH/LD" 
    goes low, it immediately loads all 8 bits regardless of the "Clock" signal, 
    while the shift mode is synchronous with the clock signal.

For more information you can download the Datasheet by going to the link below
https://www.ti.com/lit/ds/symlink/sn74hc165.pdf
"""
# Note:
""" our shift register is 40-bit register formed by linking five 8-bit register in series """

# import the nessecery library
from time import sleep # imports the sleep function from the time module
import RPi.GPIO as GPIO # imports the RPi.GPIO module to use the functions associated with it

# Define Connections to 74HC165
data = 31 # sets the data to the GPIO pin 31
Shift_Load_Bar = 16 # sets the Shift/Load Bar to the GPIO pin 16
Clock_inhibit = 29 # sets the Clock_inhibit to the GPIO pin 29
Clock = 18 # sets the Clock to the GPIO pin 18
# Note:
# We cannot change the pins number as this is how they were 
# configured on the connector board made by Primatec. 

# initialize the Buttons_state as not pressed
# by creating a list of 40 elements containing zeros
Buttons_state = [0] * 40 

# setup gpio config and initialize the pins
def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(Shift_Load_Bar, GPIO.OUT)
    # Initialize the shift pin to high
    GPIO.output(Shift_Load_Bar, 1)
    GPIO.setup(Clock, GPIO.OUT)
    # Initialize the Clock pin to low
    GPIO.output(Clock, 0)
    GPIO.setup(Clock_inhibit, GPIO.OUT)
    # Enable the Clock by holding the Clock_inhibit low
    GPIO.output(Clock_inhibit, 0)
    GPIO.setup(data, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

# function to get button status
def get_button_status():
    # Activate the load mode by putting the Shift_Load_Bar to low
    # to load the data and shift the first bit (the MSB bit)
    GPIO.output(Shift_Load_Bar, 0)
    #sleep(0.005)
    # Switch to the shift mode by putting the Shift_Load_Bar to high
    GPIO.output(Shift_Load_Bar ,1)
    # Start reading and shifting out
    for i in range(39,-1,-1):
        # Read the button state "data"
        Buttons_state[i] = GPIO.input(data)
        # check if it's pressed, if so, print it to the screen
        if Buttons_state[i] == 1:
          print(f'Button "{i}" is pressed')
        # shift out the next data
        GPIO.output(Clock, 0)
        #sleep(0.005)
        GPIO.output(Clock, 1)

""" Here is the beginning of the main code """
# setup gpio config
setup()
print("Starting the program...\nPlease start pushing buttons on the board:")
while True:
    get_button_status()

#import time
#start_time = time.time()
#get_button_status()
#end_time = time.time()
#elapsed_time = end_time - start_time
#print(f"Elapsed time: {elapsed_time} seconds")