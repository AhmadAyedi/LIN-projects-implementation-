import can

# Reverse mappings for interpretation
LIGHT_NAMES = {
    0x101: "Low Beam",
    0x102: "High Beam",
    0x103: "Parking Left",
    0x104: "Parking Right",
    0x105: "Hazard Lights",
    0x106: "Right Turn",
    0x107: "Left Turn"
}

STATUS_NAMES = {
    0x01: "activated",
    0x00: "desactivated",
    0xFF: "FAILED"
}

def receive_messages():
    print("Listening for CAN messages...")
    try:
        bus = can.interface.Bus(channel='can0', bustype='socketcan')
        while True:
            msg = bus.recv(timeout=1.0)
            if msg:
                light = LIGHT_NAMES.get(msg.arbitration_id, f"Unknown ID: {hex(msg.arbitration_id)}")
                status = STATUS_NAMES.get(msg.data[0] if msg.data else 0xFF, "Unknown status")
                print(f"Received: {light} - {status}")
                
    except KeyboardInterrupt:
        print("\nStopped listening")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    receive_messages()