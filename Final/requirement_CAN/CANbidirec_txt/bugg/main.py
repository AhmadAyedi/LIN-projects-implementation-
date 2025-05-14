#!/usr/bin/env python3
import time
import can
import os
import re
from req import WiperSystem

class CANWiperMaster:
    def __init__(self):
        self.channel = 'can0'
        self.bustype = 'socketcan'
        self.bus = None
        self.wiper = WiperSystem("input.txt", "wiper_output.txt")
        self.CAN_MSG_ID = 0x100  # Master to slave (control)
        self.CAN_RESPONSE_ID = 0x101  # Slave to master (status)
        self.last_modified = 0
        self.last_status = None
        
        self.init_can_bus()
    
    def init_can_bus(self):
        try:
            os.system(f'sudo /sbin/ip link set {self.channel} up type can bitrate 500000')
            time.sleep(0.5)
            self.bus = can.interface.Bus(channel=self.channel, bustype=self.bustype, 
                                       receive_own_messages=False)
            print("CAN initialized")
        except Exception as e:
            print(f"CAN init failed: {e}")
            raise
    
    def extract_signals(self, content):
        """Extract only the signals that appear in the output"""
        signals = {}
        matches = re.finditer(r'(\w+)\s*=\s*(\d+)', content)
        for match in matches:
            signals[match.group(1)] = int(match.group(2))
        return signals
    
    def create_can_frame(self, signals):
        """Create CAN frame from exact output signals"""
        data = bytearray(8)  # Initialize with zeros
        
        # Map output signals to CAN frame bytes
        if 'wiperMode' in signals:
            data[0] = signals['wiperMode']
        if 'wiperSpeed' in signals:
            data[1] = signals['wiperSpeed']
        if 'wiperCycleCount' in signals:
            data[2] = signals['wiperCycleCount']
        if 'WiperIntermittent' in signals:
            data[3] = signals['WiperIntermittent']
        if 'wipingCycle' in signals:
            data[4] = signals['wipingCycle'] & 0xFF
            data[5] = (signals['wipingCycle'] >> 8) & 0xFF
        
        return data
    
    def send_signals(self):
        """Process input and send exact output signals"""
        try:
            # Process through requirements
            self.wiper.process_operation()
            
            # Read the generated output
            with open("wiper_output.txt", 'r') as f:
                content = f.read()
                print("\nGenerated Output:")
                print(content.strip())
                
                # Extract exact signals
                signals = self.extract_signals(content)
                print("\nSignals to transmit:", signals)
                
                # Create and send CAN frame
                can_data = self.create_can_frame(signals)
                self.send_can_with_retry(can_data, self.CAN_MSG_ID)
                
        except Exception as e:
            print(f"Error: {e}")
    
    def send_can_with_retry(self, data, can_id, max_retries=3):
        """Send CAN message with retry logic"""
        for attempt in range(max_retries):
            try:
                msg = can.Message(
                    arbitration_id=can_id,
                    data=data,
                    is_extended_id=False
                )
                self.bus.send(msg, timeout=0.2)
                print(f"Sent CAN ID {hex(can_id)}: {data.hex()}")
                return True
            except can.CanError as e:
                print(f"CAN send attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print("Max retries reached, giving up")
                    return False
                time.sleep(0.1)
    
    def file_changed(self):
        try:
            mod_time = os.path.getmtime("input.txt")
            if mod_time != self.last_modified:
                self.last_modified = mod_time
                return True
            return False
        except:
            return False
    
    def parse_status_frame(self, data):
        """Convert CAN status data to signals"""
        status = {
            'WiperStatus': data[0],
            'wiperCurrentSpeed': data[1],
            'wiperCurrentPosition': data[2],
            'consumedPower': data[3],
            'currentWiperMode': data[4],
            'isWiperBlocked': data[5],
            'blockageReason': data[6],
            'hwError': data[7]
        }
        return status
    
    def display_status(self, status):
        """Display the received status in detail"""
        if status == self.last_status:
            return  # Skip if status hasn't changed
            
        self.last_status = status
        
        print("\n=== Exact Wiper Status ===")
        print(f"1. Operational Status: {'READY (1)' if status['WiperStatus'] else 'FAULT (0)'}")
        print(f"2. Current Speed: {status['wiperCurrentSpeed']} (0=stopped, 1=slow, 2=fast)")
        print(f"3. Wiper Position: {status['wiperCurrentPosition']}%")
        print(f"4. Power Consumption: {status['consumedPower']}W")
        print(f"5. Current Mode: {status['currentWiperMode']}")
        
        if status['isWiperBlocked']:
            reasons = ["None", "Obstacle", "Motor Fault"]
            print(f"6. BLOCKAGE DETECTED! Reason: {reasons[status['blockageReason']]}")
        else:
            print("6. No Blockage Detected")
            
        if status['hwError']:
            print("7. HARDWARE ERROR DETECTED!")
        else:
            print("7. Hardware OK")
        
        print("="*30)
    
    def monitor(self):
        print("Monitoring input.txt and CAN bus...")
        try:
            while True:
                # Check for status messages
                msg = self.bus.recv(timeout=0.1)
                if msg and msg.arbitration_id == self.CAN_RESPONSE_ID:
                    status = self.parse_status_frame(msg.data)
                    self.display_status(status)
                    self.last_status_time = time.time()
                
                # Check for input file changes
                if self.file_changed():
                    print("\n=== Input Changed ===")
                    self.send_signals()
                
                # Small delay to prevent CPU overload
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        if self.bus:
            self.bus.shutdown()
        os.system(f'sudo /sbin/ip link set {self.channel} down')
        print("Shutdown complete")

if __name__ == "__main__":
    master = CANWiperMaster()
    master.monitor()