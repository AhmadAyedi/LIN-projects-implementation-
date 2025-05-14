# -*- coding: utf-8 -*-
# import the nessecery library
from time import sleep # imports the sleep function from the time module
import RPi.GPIO as GPIO # imports the RPi.GPIO module to use the functions associated with it
import cantools # import the cantools module to manipulate the DBC file
import can # import the can module to establishe the can bus to send and recieve can messages
import subprocess # import the subprocess module to start the can communication
import threading # import the threading module to parallelize execution 
from time import sleep
import logging

# Create a logging object
logger = logging.getLogger('my_can_listener')
logger.setLevel(logging.INFO)

def my_message_handler(msg):
    logger.info(msg)

# Define Connections to 74HC165
data = 31 # sets the data to the GPIO pin 31
Shift_Load_Bar = 16 # sets the Shift/Load Bar to the GPIO pin 16
Clock_inhibit = 29 # sets the Clock_inhibit to the GPIO pin 29
Clock = 18 # sets the Clock to the GPIO pin 18
# Note:
# We cannot change the pins number as this is how they were 
# configured on the connector board made by Primatec. 

# setup gpio config and initialize the pins for the 74HC165 of the Buttons
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

# Define Connections to 74HC595
Latch = 13 # sets the RCLK (Register Clock / Latch) to the GPIO pin 15
SRClock = 15 # sets the SRCLK (Shift Register Clock) to the GPIO pin 13
Serial_Input = 11 # sets the Serial_Input to the GPIO pin 11
Clear = 7 # sets the Shift Register Clear to the GPIO pin 7
# Note:
# We cannot change the pins number as this is how they were 
# configured on the connector board made by Primatec. 

# setup gpio config and initialize the pins for the 74HC595 of the LEDs
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(SRClock, GPIO.OUT)
GPIO.setup(Latch, GPIO.OUT)
GPIO.setup(Clear, GPIO.OUT)
GPIO.setup(Serial_Input, GPIO.OUT)

# Clear the Shift Register (Reset) by pulling the Clear to low
GPIO.output(Clear, 0)
GPIO.output(Clear, 1)

# List of the buttons name with respect to their position in the status table
button_names = ['CS_DRW_open_level_2',
                'CS_DRW_open_level_1',
                'CS_PRW_close_level_2',
                'CS_PRW_close_level_1',
                'CS_DRW_close_level_2',
                'CS_DRW_close_level_1',
                'CSFAW_open_level_2',
                'CSFAW_open_level_1',
                'safety_Button',
                'CSFAW_close_level_2',
                'CSFAW_close_level_1',
                'LS_PW_close_level_2',
                'LS_PW_open_level_2',
                'LS_PW_close_level_1',
                'LS_PW_open_level_1',
                'LS_PRW_open_level_2',
                'LS_PRW_open_level_1',
                'LS_DRW_open_level_2',
                'LS_DRW_open_level_1',
                'LS_PRW_close_level_2',
                'LS_PRW_close_level_1',
                'LS_DRW_close_level_2',
                'LS_DRW_close_level_1',
                'CS_PW_open_level_2',
                'CS_PW_open_level_1',
                'CS_DW_open_level_2',
                'CS_DW_open_level_1',
                'CS_PW_close_level_2',
                'CS_PW_close_level_1',
                'CS_DW_close_level_2',
                'CS_DW_close_level_1',
                'CS_PRW_open_level_2',
                'CS_PRW_open_level_1']

########################################################################################################################
# Create an emtry Dictionary to store all the signals and initialize thier values as 0
all_slave_signals = dict()

# Loading the DBC file
db = cantools.database.load_file(r'/home/pi/Desktop/code_RPI_slave/my_can_data_base.dbc') # <-- a Database object

# accessing the messages of the Database object
my_messages = db.messages # <-- a List contain Message objets
#>>> [message('DriverRearWindowStatus_Slave', 0x34, False, 4, None), 
#     message('PassengerRearWindowStatus_Slave', 0x32, False, 4, None), 
#     message('PassengerWindowStatus_Slave', 0x31, False, 4, None), 
#     message('DriverWindowStatus_Slave', 0x30, False, 4, None), 
#     message('DriverRearWindowStatus_Master', 0x23, False, 3, None), 
#     message('PassengerRearWindowStatus_Master', 0x22, False, 3, None), 
#     message('PassengerWindowStatus_Master', 0x21, False, 3, None), 
#     message('DriverWindowStatus_Master', 0x20, False, 3, None), 
#     message('GlobalWindowStatus_Master', 0x15, False, 2, None), 
#     message('ChildSafetyLedStatus', 0x11, False, 1, None), 
#     message('CentralSwitchBlock', 0x10, False, 3, None)]

# loop over the messages list to get their signals and store them in the dict
for msg in my_messages:
    # test if the mesage belong  to the Slave 
    if msg.name.endswith(("Slave", "Block", "Status")):
        # add the message name to the slave_message_name list
        try:
            slave_message_name.append(msg.name)
        except:
            slave_message_name = []
            slave_message_name.append(msg.name)
        # get the signals list of the message
        signals_list =  msg.signal_tree
        # create a new dictionary with keys from your string list of the signals_list 
        # and set all their values to 0. using a dictionary comprehension 
        # my_dict = {key: 0 for key in signals_list}
        my_dict = dict.fromkeys(signals_list, 0)
        # add the created dictionary to all_signals dictionary
        all_slave_signals.update(my_dict)

########################################################################################################################
# difine a dictionary to fill it with the signals related to the buttons status
slave_signal_names_list_buttons_state = ["Central_Switch_Block_All_Window",
                                         "Central_Switch_Block_Driver",
                                         "Central_Switch_Block_Passenger",
                                         "Central_Switch_Block_Driver_Rear",
                                         "Central_Switch_Block_Passenger_Rear",
                                         "Rear_Window_Safety_Switch",
                                         "Passenger_Local_Switch",
                                         "DriverRear_Local_Switch",
                                         "PassengerRear_Local_Switch"]
                                                    
slave_signal_buttons_state = dict.fromkeys(slave_signal_names_list_buttons_state, 0)

########################################################################################################################
#configuration of can bus
commande = "sudo ip link set can0 up type can bitrate 500000"
resultat = subprocess.run(commande, shell=True, capture_output=True, text=True)
print(resultat.stdout)
bustype = 'socketcan'
channel = 'can0'
# setting up the can bus
bus = can.interface.Bus(channel=channel, bustype=bustype,bitrate=500000)

notifier = can.Notifier(bus, [can.Logger('./my_can.txt'), my_message_handler])

# function to get button status
def button_checker() -> list[int]:
    """
    this function checks the buttons status and return them if there is a button pressed

    Yields
    ------
    list(int): list with  0s and 1s indicating the buttons status.
    """
    # initialize the Buttons_state as not pressed
    Buttons_state = [0] * 40
    # Activate the load mode by putting the Shift_Load_Bar to low
    # to load the data and shift the first bit (the MSB bit)
    GPIO.output(Shift_Load_Bar, 0)
    # sleep(0.005)
    # Switch to the shift mode by putting the Shift_Load_Bar to high
    GPIO.output(Shift_Load_Bar ,1)
    # Start reading and shifting out
    for i in range(39,-1,-1):
        # Read the button state "data" and store it in the Buttons_state list
        Buttons_state[i] = GPIO.input(data)
        # shift out the next data
        GPIO.output(Clock, 0)
        # sleep(0.005)
        GPIO.output(Clock, 1)
    # Return the buttons_state
    return Buttons_state 

# function to get the indexes of the buttons pressed
def get_indexes(my_list: list[int], element: int = 1) -> list[int]:
    """
    Given a list of integers containing only 0s and 1s, and an integer element, 
    returns a list containing all the indexes of the occurrences of the given 
    element in the list.

    Parameters
    ----------
    - my_list : list(int)
        A list of integers containing only 0s and 1s.
    - element : int, optional
        A list of integers containing only 0s and 1s.

    Returns
    -------
    - list(int)
        A list containing all the indexes of the occurrences of the given element in the list.

    """
    return [index for index, value in enumerate(my_list) if value == element]

# function to update the signals which informs the buttons status
def update_button_signals(indexes: list[int]):
    for i in indexes:
        button = button_names[i]
        if button.endswith("open_level_1"):
            signal_value = 1
        elif button.endswith("close_level_1"):
            signal_value = 2
        elif button.endswith("open_level_2"):
            signal_value = 3
        elif button.endswith("close_level_2"):
            signal_value = 4
        elif button == 'safety_Button':
            signal_value = 1
        if button.startswith("CSFAW"):
            signals_name = "Central_Switch_Block_All_Window"
        elif button.startswith("CS_DW"):
            signals_name = "Central_Switch_Block_Driver"
        elif button.startswith("CS_PW"):
            signals_name = "Central_Switch_Block_Passenger"
        elif button.startswith("CS_DRW"):
            signals_name = "Central_Switch_Block_Driver_Rear"
        elif button.startswith("CS_PRW"):
            signals_name = "Central_Switch_Block_Passenger_Rear"
        elif button.startswith("safety"):
            signals_name = "Rear_Window_Safety_Switch"
        elif button.startswith("LS_PW"):
            signals_name = "Passenger_Local_Switch"
        elif button.startswith("LS_DRW"):
            signals_name = "DriverRear_Local_Switch"
        elif  button.startswith("LS_PRW"):
            signals_name = "PassengerRear_Local_Switch"    
        slave_signal_buttons_state[signals_name] = signal_value
    all_slave_signals.update(slave_signal_buttons_state)

# function to send the messages
def send_mesages():
    for msg_name in slave_message_name:
        the_message = db.get_message_by_name(msg_name)
        the_required_signals = the_message.gather_signals(all_slave_signals)
        data = the_message.encode(the_required_signals, msg_name)
        msg = can.Message(arbitration_id=the_message.frame_id, data=data, is_extended_id=False)
        bus.send(msg)
"""
from time import time       
while True:
    start1 = time()
    list_status = button_checker()
    end1 = time()
    if 1 in list_status:
        start2 = time()
        update_button_signals(get_indexes(list_status))
        end2 = time()
        send_mesages()
        end3 = time()
        print(f"elapsed time for the button_checker: {end1 - start1}")
        print(f"elapsed time for the update_button_signals: {end2 - start2}")
        print(f"elapsed time for the send_mesages: {end3 - end2}")
    else:
        pass
    
"""
# function to display the LEDs based on the LEDs_status
def display(LEDs_Status: list[int] = [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]):
    
    for state in LEDs_Status:
        GPIO.output(Serial_Input, state)
        # each loop generate a clock signal 
        # to shift the Serial input in the shift register
        GPIO.output(SRClock, 0)
        GPIO.output(SRClock, 1)

    # turn the LEDs
    GPIO.output(Latch, 0)
    GPIO.output(Latch, 1)

# function to do action based on the recieved message
def do_action(encoded: dict[str,int]):
    close_driver_window = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0]]
    Driver_msg = {'DriverRear_Window_Movement_Status': 0, 'DriverRear_Window_Movement_Type': 0, 'DriverRear_Window_Movement_Target_Position': 0, 'DriverRear_Window_Short_Long_Drop_Mode': 0, 'DriverRear_Window_Normalization_Mode': 0, 'DriverRear_Window_Movement_Mode': 0}
    # if encoded == Driver_msg:
    if encoded:   
        for step in close_driver_window:
            display(step)
            sleep(1) 
        # display()
        
def check_and_send():
    while True:
        list_status = button_checker()
        if 1 in list_status:
            update_button_signals(get_indexes(list_status))
            send_mesages()

def receive_and_do_action():
    while True:
        try:
            message = bus.recv()
            #encoded = message.data
            decoded = db.decode_message(message.arbitration_id, message.data, decode_choices=False)
            #print(decoded)
            do_action(decoded)
        except can.CanError:
            print("Error receiving CAN message")

# Start the listener using the notifier object

logging.basicConfig(filename='my_can_logging.txt', filemode='w',format='%(message)s')
notifier = can.Notifier(bus, [can.Logger('can_logger.txt')])

    
# Start the threads
check_and_send_thread = threading.Thread(target=check_and_send)
receive_and_do_action_thread = threading.Thread(target=receive_and_do_action)
check_and_send_thread.start()
receive_and_do_action_thread.start()

# Wait for the threads to finish
check_and_send_thread.join()
receive_and_do_action_thread.join()

notifier.stop()