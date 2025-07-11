# pzem_test.py (or you can put this in main.py if you want it to run on boot)

from machine import UART, Pin
import time
import ubinascii # For converting bytes to hex for debugging

# --- Configuration ---
# UART pins for PZEM-004T (ESP32 UART2)
# Check your ESP32 board's pinout for GPIO16 (RX2) and GPIO17 (TX2)
UART_ID = 2
UART_TX_PIN = 17 # Connects to PZEM-004T RX
UART_RX_PIN = 16 # Connects to PZEM-004T TX
UART_BAUDRATE = 9600 # PZEM-004T default baud rate

# PZEM-004T (V3.0) read all data command (Modbus RTU format)
# Address: 0x01
# Function: 0x04 (Read Input Registers)
# Start Register: 0x0000 (Voltage)
# Number of Registers: 0x000A (10 registers for Voltage, Current, Power, Energy, Freq, PF)
# CRC (calculated): 0x70 0x0D
PZEM_READ_COMMAND = b'\x01\x04\x00\x00\x00\x0A\x70\x0D'

# --- Initialize UART ---
try:
    pzem_uart = UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
    print(f"UART{UART_ID} initialized on TX={UART_TX_PIN}, RX={UART_RX_PIN} at {UART_BAUDRATE} baud.")
except Exception as e:
    print(f"Error initializing UART: {e}")
    # If UART fails, try different pins or check for conflicts (e.g., if you're using UART0 for REPL)

def read_pzem_data():
    """
    Sends read command to PZEM-004T and parses the response.
    Returns a dictionary of parsed values or None if an error occurs.
    """
    pzem_uart.write(PZEM_READ_COMMAND)
    time.sleep(0.1) # Give PZEM time to respond

    if pzem_uart.any():
        response = pzem_uart.read()
        # print(f"Raw response: {ubinascii.hexlify(response).decode()}") # For debugging

        # Expected response length for 10 registers (2 bytes each) + 3 header + 2 CRC = 25 bytes
        # 0x01 (addr) 0x04 (func) 0x14 (byte count) [20 bytes data] 0xXX 0xXX (CRC)
        if response and len(response) >= 25:
            try:
                voltage = (response[3] << 8 | response[4]) / 10.0
                current = (response[5] << 8 | response[6] | response[7] << 24 | response[8] << 16) / 1000.0 # 4 bytes for current
                power = (response[9] << 8 | response[10] | response[11] << 24 | response[12] << 16) / 10.0 # 4 bytes for power
                energy = (response[13] << 8 | response[14] | response[15] << 24 | response[16] << 16) / 1000.0 # 4 bytes for energy
                frequency = (response[17] << 8 | response[18]) / 10.0
                power_factor = (response[19] << 8 | response[20]) / 100.0

                return {
                    "Voltage": voltage,
                    "Current": current,
                    "Power": power,
                    "Energy": energy, # Accumulated energy in kWh
                    "Frequency": frequency,
                    "PowerFactor": power_factor
                }
            except Exception as e:
                print(f"Error parsing response: {e}")
                return None
        else:
            print(f"Incomplete or invalid response length: {len(response) if response else 0} bytes.")
            return None
    else:
        print("No response from PZEM-004T.")
        return None

# --- Main loop to continuously read and print data ---
print("Starting PZEM-004T data collection loop...")
while True:
    data = read_pzem_data()
    if data:
        print("-" * 30)
        print(f"Voltage: {data['Voltage']:.1f}V")
        print(f"Current: {data['Current']:.3f}A")
        print(f"Power:   {data['Power']:.1f}W")
        print(f"Energy:  {data['Energy']:.3f}kWh")
        print(f"Freq:    {data['Frequency']:.1f}Hz")
        print(f"PF:      {data['PowerFactor']:.2f}")
    else:
        print("Failed to get PZEM data.")
    time.sleep(2) # Read every 2 seconds