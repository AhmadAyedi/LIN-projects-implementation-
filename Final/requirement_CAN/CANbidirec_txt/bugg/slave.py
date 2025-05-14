#!/usr/bin/env python3
import can
import os
import RPi.GPIO as GPIO
import time
import threading
import logging
import re

# GPIO setup
FRONT_LEDS = [23, 24, 26]  # Right to left
BACK_LEDS = [16, 20, 21]   # Right to left

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wiper_slave.log'),
        logging.StreamHandler()
    ]
)

class CANWiperSlave:
    def __init__(self):
        # Initialize CAN
        try:
            os.system('sudo /sbin/ip link set can0 up type can bitrate 500000')
            time.sleep(0.5)
            self.can_bus = can.interface.Bus(channel='can0', bustype='socketcan',
                                          receive_own_messages=False)
        except Exception as e:
            logging.error(f"CAN initialization failed: {e}")
            raise
        
        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        for pin in FRONT_LEDS + BACK_LEDS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            
        # Thread control
        self.stop_event = threading.Event()
        self.active_threads = []
        self.operation_lock = threading.Lock()
        self.running = True
        self.back_wiper_active = False
        
        # Status file monitoring
        self.status_file = "respond2.txt"
        self.last_status_mtime = 0
        
        # Initialize status signals
        self.status_signals = {
            # These will be updated from received commands
            'WiperStatus': 1,
            'wiperCurrentSpeed': 0,
            'wiperCurrentPosition': 0,
            'currentWiperMode': 0,
            
            # These will be loaded from respond2.txt
            'consumedPower': 5,
            'isWiperBlocked': 0,
            'blockageReason': 0,
            'hwError': 0
        }
        
        # Load manual status signals
        self.load_manual_status()
        
        # Start threads
        self.can_thread = threading.Thread(target=self.monitor_can, daemon=True)
        self.status_thread = threading.Thread(target=self.send_status_updates, daemon=True)
        self.file_monitor_thread = threading.Thread(target=self.monitor_status_file, daemon=True)
        self.can_thread.start()
        self.status_thread.start()
        self.file_monitor_thread.start()
        
        logging.info("Wiper slave initialized")

    def load_manual_status(self):
        """Load only manual status signals from respond2.txt"""
        try:
            with open(self.status_file, 'r') as f:
                content = f.read()
                matches = re.finditer(r'(\w+)\s*=\s*(\d+)', content)
                
                manual_signals = ['consumedPower', 'isWiperBlocked', 'blockageReason', 'hwError']
                with self.operation_lock:
                    for match in matches:
                        key = match.group(1)
                        if key in manual_signals:
                            self.status_signals[key] = int(match.group(2))
                    
                    logging.info("Loaded manual status signals:")
                    for key in manual_signals:
                        logging.info(f"{key} = {self.status_signals[key]}")
        except Exception as e:
            logging.warning(f"Could not load status file, using defaults: {e}")

    def monitor_status_file(self):
        """Monitor respond2.txt for changes to manual signals"""
        logging.info(f"Monitoring {self.status_file} for manual signal changes...")
        while self.running:
            try:
                current_mtime = os.path.getmtime(self.status_file)
                if current_mtime != self.last_status_mtime:
                    self.load_manual_status()
                    self.last_status_mtime = current_mtime
                    logging.info("Manual status signals updated from file")
                time.sleep(0.5)
            except Exception as e:
                logging.error(f"File monitor error: {e}")
                time.sleep(1)

    def create_status_frame(self):
        """Create CAN frame from current status values"""
        with self.operation_lock:
            data = bytearray([
                self.status_signals['WiperStatus'],
                self.status_signals['wiperCurrentSpeed'],
                self.status_signals['wiperCurrentPosition'],
                self.status_signals['consumedPower'],
                self.status_signals['currentWiperMode'],
                self.status_signals['isWiperBlocked'],
                self.status_signals['blockageReason'],
                self.status_signals['hwError']
            ])
        return data

    def send_status_with_retry(self, max_retries=3, retry_delay=0.1):
        """Send status with retry logic"""
        data = self.create_status_frame()
        msg = can.Message(
            arbitration_id=0x101,
            data=data,
            is_extended_id=False
        )
        
        for attempt in range(max_retries):
            try:
                self.can_bus.send(msg, timeout=0.2)
                logging.debug(f"Sent status update: {[hex(b) for b in data]}")
                return True
            except can.CanError as e:
                logging.warning(f"Status send attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logging.error("Max retries reached for status update")
                    return False
                time.sleep(retry_delay)
    
    def send_status_updates(self):
        """Periodically send status updates"""
        while self.running:
            try:
                success = self.send_status_with_retry()
                time.sleep(1.0)  # Send status every second
            except Exception as e:
                logging.error(f"Status update error: {e}")
                time.sleep(1)

    def _wiper_sweep(self, leds, speed, stop_event):
        """Perform a complete wiper sweep with position tracking"""
        delay = 0.3 if speed == 1 else 0.15  # Fast speed has shorter delay
        
        steps = len(leds) * 2  # Forward and backward
        step_size = 100 / steps
        
        # Forward sweep (right to left)
        for i, led in enumerate(leds):
            if stop_event.is_set():
                with self.operation_lock:
                    self.status_signals['wiperCurrentPosition'] = 0
                return False
            GPIO.output(led, GPIO.HIGH)
            with self.operation_lock:
                self.status_signals['wiperCurrentPosition'] = min(100, int((i + 1) * step_size * len(leds)))
            time.sleep(delay/len(leds))
        
        # Backward sweep (left to right)
        for i, led in enumerate(reversed(leds)):
            if stop_event.is_set():
                with self.operation_lock:
                    self.status_signals['wiperCurrentPosition'] = 0
                return False
            GPIO.output(led, GPIO.LOW)
            with self.operation_lock:
                self.status_signals['wiperCurrentPosition'] = min(100, int((len(leds) + i + 1) * step_size * len(leds)))
            time.sleep(delay/len(leds))
        
        with self.operation_lock:
            self.status_signals['wiperCurrentPosition'] = 0
        return True

    def _activate_wiper(self, leds, speed, cycles, is_intermittent=False):
        """Wiper operation with status updates"""
        count = 0
        with self.operation_lock:
            self.status_signals['wiperCurrentSpeed'] = speed
            self.status_signals['currentWiperMode'] = self.wiper_mode
            self.status_signals['WiperStatus'] = 1  # Ready when receiving commands
        
        try:
            while cycles == 0 or count < cycles:
                if self.stop_event.is_set():
                    break
                
                if not self._wiper_sweep(leds, speed, self.stop_event):
                    break
                
                if cycles > 0:
                    count += 1
                
                if is_intermittent:
                    if not (self.wiper_mode == 2 and 
                           self.wiper_speed == 1 and 
                           self.wiper_intermittent == 1):
                        break
                    time.sleep(1.7)
        finally:
            for led in leds:
                GPIO.output(led, GPIO.LOW)
            with self.operation_lock:
                self.status_signals['wiperCurrentSpeed'] = 0
                self.status_signals['wiperCurrentPosition'] = 0

    def _stop_wipers(self):
        """Immediately stop all wiper activity"""
        with self.operation_lock:
            self.stop_event.set()
            for t in self.active_threads:
                t.join(timeout=0.1)
            for pin in FRONT_LEDS + BACK_LEDS:
                GPIO.output(pin, GPIO.LOW)
            self.stop_event.clear()
            self.active_threads = []
            self.back_wiper_active = False
            self.status_signals['wiperCurrentSpeed'] = 0
            self.status_signals['wiperCurrentPosition'] = 0
            logging.info("Wipers fully stopped")

    def process_can_signals(self, signals):
        """Process received CAN signals and update status accordingly"""
        logging.info(f"Processing signals: {signals}")
        self._stop_wipers()
        
        # Update status from received commands
        with self.operation_lock:
            self.wiper_mode = signals.get('wiperMode', 0)
            self.wiper_speed = signals.get('wiperSpeed', 0)
            self.wiper_intermittent = signals.get('WiperIntermittent', 0)
            
            self.status_signals['currentWiperMode'] = self.wiper_mode
            self.status_signals['WiperStatus'] = 1  # Ready when receiving commands
        
        if self.wiper_mode == 0:
            return
        
        if self.wiper_mode == 1:
            thread = threading.Thread(
                target=self._activate_wiper,
                args=(FRONT_LEDS, self.wiper_speed, 1),
                daemon=True
            )
            self.active_threads = [thread]
            thread.start()
            logging.info("Started touch mode (single wipe)")
        
        elif self.wiper_mode in [2, 4]:
            front_thread = threading.Thread(
                target=self._activate_wiper,
                args=(FRONT_LEDS, self.wiper_speed, 0),
                daemon=True
            )
            self.active_threads = [front_thread]
            front_thread.start()
            
            if (self.wiper_mode == 2 and 
                self.wiper_speed == 1 and 
                self.wiper_intermittent == 1):
                self.back_wiper_active = True
                back_thread = threading.Thread(
                    target=self._activate_wiper,
                    args=(BACK_LEDS, 1, 0, True),
                    daemon=True
                )
                self.active_threads.append(back_thread)
                back_thread.start()
                logging.info("Started intermittent rear wiper")
            else:
                with self.operation_lock:
                    for led in BACK_LEDS:
                        GPIO.output(led, GPIO.LOW)
                logging.debug("Ensured rear wipers are off")
            
            logging.info(f"Started continuous front wiper (speed={'fast' if self.wiper_speed == 2 else 'normal'})")

    def parse_can_frame(self, data):
        """Convert CAN data back to signals"""
        signals = {}
        if data[0] > 0:
            signals['wiperMode'] = data[0]
        if data[1] > 0:
            signals['wiperSpeed'] = data[1]
        if data[2] > 0:
            signals['wiperCycleCount'] = data[2]
        if data[3] > 0:
            signals['WiperIntermittent'] = data[3]
        if data[4] > 0 or data[5] > 0:
            signals['wipingCycle'] = data[4] | (data[5] << 8)
        return signals

    def monitor_can(self):
        """Monitor CAN bus for messages"""
        logging.info("Listening for CAN messages...")
        try:
            while self.running:
                msg = self.can_bus.recv(timeout=1.0)
                if msg and msg.arbitration_id == 0x100:
                    signals = self.parse_can_frame(msg.data)
                    self.process_can_signals(signals)
        except Exception as e:
            logging.error(f"CAN monitoring error: {e}")

    def shutdown(self):
        """Clean up resources"""
        logging.info("Shutting down...")
        self.running = False
        self._stop_wipers()
        
        if self.can_thread.is_alive():
            self.can_thread.join(timeout=0.5)
        if self.status_thread.is_alive():
            self.status_thread.join(timeout=0.5)
        if self.file_monitor_thread.is_alive():
            self.file_monitor_thread.join(timeout=0.5)
        
        if self.can_bus:
            self.can_bus.shutdown()
        os.system('sudo /sbin/ip link set can0 down')
        GPIO.cleanup()
        logging.info("Shutdown complete")

if __name__ == "__main__":
    try:
        slave = CANWiperSlave()
        while slave.running:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
    finally:
        slave.shutdown()