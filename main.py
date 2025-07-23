# main.py - EnerGreen ESP32 MicroPython Code with SIMULATED PZEM-004T Data for Testing

import time
import random # For generating random data (re-added for simulation)
import network # To check WiFi status
import urequests
import json # Needed to convert dictionary to JSON string
# from machine import UART # COMMENTED OUT: Not needed when using simulated data
import utime # For utime.time() to get accurate timestamps

# --- Configuration ---
# Set this to True to test sending malformed data to your Cloud Function.
# Set to False for normal operation.
SEND_MALFORMED_DATA = False
# --- End Configuration ---

# --- Import Cloud Function URL from config.py ---
try:
    from config import CLOUD_FUNCTION_URL, WIFI_SSID, WIFI_PASSWORD
except ImportError:
    print("Error: config.py not found or incomplete. Please create it with CLOUD_FUNCTION_URL, WIFI_SSID, WIFI_PASSWORD.")
    # These fallbacks are for main.py's reconnection logic, if config.py fails.
    # In a real scenario, you would halt execution or implement robust error handling.
    CLOUD_FUNCTION_URL = 'http://default_cloud_function_url_if_not_found' 
    WIFI_SSID = 'default_ssid'
    WIFI_PASSWORD = 'default_password'
# --- End Import config ---

# Ensure Wi-Fi is connected from boot.py
sta_if = network.WLAN(network.STA_IF)
try:
    if not sta_if.isconnected():
        print("Wi-Fi not connected in main.py. Attempting initial connection...")
        # This initial connection attempt is a fallback if boot.py somehow failed
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 0
        while not sta_if.isconnected() and timeout < 20: # Wait up to 20 seconds
            print('.', end='')
            time.sleep(1)
            timeout += 1
        if sta_if.isconnected():
            print("\nWi-Fi connected in main.py fallback!")
            print('Network config:', sta_if.ifconfig())
        else:
            print("\nFailed to connect to Wi-Fi in main.py fallback. Data sending will not occur.")
except OSError as e:
    print(f"\nOS Error during initial Wi-Fi check/connection in main.py: {e}")
    print("Wi-Fi functionality might be unavailable. Data sending will not occur until resolved.")


# --- PZEM-004T V3.0 Command and Parsing Configuration ---
# Standard read command for PZEM-004T V3.0 (read registers 0x00 to 0x07)
# For slave address 0x01, function code 0x03, start address 0x0000, 8 registers
# PZEM_READ_COMMAND = bytearray([0x01, 0x04, 0x00, 0x00, 0x00, 0x08, 0x31, 0xCC]) # COMMENTED OUT for simulation

# Initialize UART for PZEM communication
# Using UART2 (default pins GPIO16 for RX, GPIO17 for TX)
# Make sure these pins are not used by anything else.
# pzem_uart = UART(2, baudrate=9600, tx=17, rx=16) # COMMENTED OUT for simulation

# --- Function to read data from PZEM-004T (COMMENTED OUT for simulation) ---
# def pzem_data():
#     """
#     Reads real-time data from the PZEM-004T module via UART.
#     Returns a dictionary of energy parameters or None on failure.
#     """
#     print("Attempting to read from PZEM-004T...")
#     try:
#         # Clear any old data in the buffer
#         pzem_uart.read()
#         time.sleep_ms(50) # Small delay before sending command

#         # Send the read command
#         pzem_uart.write(PZEM_READ_COMMAND)
#         time.sleep_ms(500) # Give PZEM time to respond (increased for robustness)

#         # Read the response (expected 21 bytes for V3.0: Addr+Func+ByteCount+16DataBytes+CRC)
#         response = pzem_uart.read()

#         if response and len(response) >= 21: # Check for a valid response length for V3.0
#             print(f"PZEM raw response: {response.hex()}")

#             # Extract data bytes (registers 0x00 to 0x07)
#             # Data starts at index 3 and is 16 bytes long (8 registers * 2 bytes/register)
#             data_bytes = response[3:19] 
            
#             # Parse the response based on PZEM-004T V3.0 Modbus RTU protocol
#             # Register addresses (hex) and scaling factors:
#             # 0x0000: Voltage (0.1V)
#             # 0x0001: Current (0.001A)
#             # 0x0002 & 0x0003: Active Power (0.1W) - combined 32-bit
#             # 0x0004 & 0x0005: Energy (1Wh) - combined 32-bit
#             # 0x0006: Frequency (0.1Hz)
#             # 0x0007: Power Factor (0.01)

#             voltage_raw = (data_bytes[0] << 8) | data_bytes[1]
#             current_raw = (data_bytes[2] << 8) | data_bytes[3]
#             # Power is a 32-bit value across two registers (0x0002 and 0x0003)
#             power_raw   = (data_bytes[4] << 8) | data_bytes[5] # Register 0x0002 (High word)
#             power_raw   = (power_raw << 8) | data_bytes[6]     # Register 0x0003 (Low word)
#             # Energy is a 32-bit value across two registers (0x0004 and 0x0005)
#             energy_raw  = (data_bytes[8] << 8) | data_bytes[9] # Register 0x0004 (High word)
#             energy_raw  = (energy_raw << 8) | data_bytes[10]   # Register 0x0005 (Low word)
#             frequency_raw = (data_bytes[12] << 8) | data_bytes[13]
#             power_factor_raw = (data_bytes[14] << 8) | data_bytes[15]

#             # Apply scaling factors from datasheet
#             voltage = voltage_raw / 10.0
#             current = current_raw / 1000.0
#             power = power_raw / 10.0
#             kwh = energy_raw / 1000.0 # PZEM reports in Wh, convert to kWh for consistency
#             frequency = frequency_raw / 10.0
#             power_factor = power_factor_raw / 100.0
            
#             # Get current timestamp (MicroPython epoch is Jan 1, 2000)
#             current_timestamp_esp32_raw = utime.time()

#             # Construct the data dictionary
#             pzem_readings = {
#                 "deviceId": "energreen_esp32_001", # Your unique device ID
#                 "timestamp_esp32_raw": current_timestamp_esp32_raw, # Raw timestamp from ESP32
#                 "voltageVolt": voltage,
#                 "currentAmp": current,
#                 "powerWatt": power,
#                 "kwhConsumed": kwh,
#                 "frequencyHz": frequency,
#                 "powerFactor": power_factor,
#                 "energySource": "Grid" # Or dynamically set based on your setup
#             }
#             print("PZEM data read successfully!")
#             return pzem_readings

#         else:
#             print(f"No valid response from PZEM-004T or response too short. Response length: {len(response) if response else 'None'}")
#             return None

#     except Exception as e:
#         print(f"Error reading from PZEM-004T: {e}")
#         return None

# --- Simulated PZEM Data Function (for testing without AC power) ---
def simulate_pzem_data():
    """
    Generates sample and random data to mimic PZEM-004T readings.
    """
    # EnerGreen Device Unique ID
    device_id = "energreen_esp32_001" # Choose a unique ID for your device

    # Simulate typical household values with some randomness
    voltage = round(random.uniform(220.0, 240.0), 1) # Volts (e.g., 220V - 240V in PH)
    current = round(random.uniform(0.1, 5.0), 3)     # Amps (e.g., 0.1A to 5.0A)
    power = round(voltage * current * random.uniform(0.8, 1.0), 1) # Watts (P = V * I * PF)
    energy = round(random.uniform(100.0, 500.0), 3) # kWh (cumulative, so it should increase in real scenario)
    frequency = round(random.uniform(59.8, 60.2), 1) # Hz (e.g., 60Hz in PH)
    power_factor = round(random.uniform(0.7, 0.99), 2)

    return {
        "deviceId": device_id,
        "voltageVolt": voltage,
        "currentAmp": current,
        "powerWatt": power,
        "kwhConsumed": energy,
        "frequencyHz": frequency,
        "powerFactor": power_factor,
        "energySource": "Grid",
        "timestamp": utime.time() # Use utime.time() for consistency with real data
    }


print("EnerGreen ESP32 Ready! Starting data collection loop (using simulator)...")

# Main application loop
while True:
    try:
        if sta_if.isconnected():
            print("\nWi-Fi is connected. Simulating data...")
            # Call the simulate_pzem_data function to get test data
            energy_data = simulate_pzem_data()

            if energy_data:
                print("--- Simulated Readings ---")
                for key, value in energy_data.items():
                    print(f"{key}: {value}")
                print("---------------------")

                # --- HTTP POST to Cloud Function ---
                headers = {'Content-Type': 'application/json'}
                payload = json.dumps(energy_data) # Default: send valid JSON

                # --- MALFORMED DATA INJECTION POINT ---
                if SEND_MALFORMED_DATA:
                    print("!!! WARNING: Sending MALFORMED DATA for testing !!!")
                    
                    # Option 1: Remove a required field (e.g., 'deviceId')
                    # This will result in an invalid JSON payload if 'deviceId' is expected
                    # Uncomment this block to activate this test
                    # if 'deviceId' in energy_data:
                    #     del energy_data['deviceId']
                    #     payload = json.dumps(energy_data)
                    #     print(f"Malformed Payload (missing deviceId): {payload}")
                    
                    # Option 2: Send a completely non-JSON string
                    # This will cause the Cloud Function to fail JSON parsing
                    # Uncomment this block to activate this test
                    # payload = "This is not JSON data."
                    # headers = {'Content-Type': 'text/plain'} # Change header for non-JSON
                    # print(f"Malformed Payload (non-JSON): {payload}")


                try:
                    print(f"Sending data to Cloud Function: {payload}")
                    response = urequests.post(CLOUD_FUNCTION_URL, headers=headers, data=payload)

                    print(f"Cloud Function Response Status: {response.status_code}")
                    print(f"Cloud Function Response Text: {response.text}")

                    if response.status_code == 200:
                        print("Data successfully sent to Cloud Function!")
                    else:
                        print(f"Failed to send data. Status: {response.status_code}, Response: {response.text}")

                    response.close() # Close the response object to free up resources
                    
                    # Add a small delay here to allow network stack to settle
                    time.sleep(0.5) 

                except Exception as e:
                    print(f"Error sending data to Cloud Function: {e}")
                # ----------------------------------------------------

            else:
                print("Simulated PZEM data could not be generated. Skipping data send.")
                # Optionally, you might want to log this or send an error notification

        else:
            # Only attempt reconnection if not connected
            print("\nWi-Fi disconnected. Attempting to reconnect...")
            sta_if.active(True) # Ensure interface is active
            sta_if.connect(WIFI_SSID, WIFI_PASSWORD) # Use credentials from config.py
            timeout = 0
            while not sta_if.isconnected() and timeout < 10:
                print('.', end='')
                time.sleep(1)
                timeout += 1
            if sta_if.isconnected():
                print("\nReconnected!")
            else:
                print("\nStill unable to connect to Wi-Fi. Will retry next loop iteration.")
    except OSError as e:
        print(f"\nOS Error during Wi-Fi check/reconnection in main loop: {e}")
        print("Wi-Fi functionality might be unavailable. Retrying connection in next loop.")
        # Add a longer sleep here if an OSError occurs to prevent rapid retries
        time.sleep(5) # Sleep for 5 seconds before next attempt to avoid hammering the network stack


    # This sleep is for the main loop iteration, allowing time between readings/sends
    time.sleep(10) # Send data every 10 seconds (adjust as needed)