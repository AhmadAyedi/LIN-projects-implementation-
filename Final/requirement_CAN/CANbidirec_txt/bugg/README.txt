the master send frames to control leds(act as wipers)
the other node receive those frames and forward back signals (describing 
wiper's status) to master as a response 

the signals sent by master are actually the signals being checked and returned 
by the requirement code 

req.py will read and parse input.txt(by the user) then return signals 
the signals returned by req.py will be read and parased by main.py 
main.py will forward them through CAN bus 

then slave send back response signals to inducate the status of wiper system