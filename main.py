# main.py
import time
import random # For generating random data
import network # To check WiFi status
import urequests
import json # Needed to convert dictionary to JSON string

# --- Import Cloud Function URL from config.py ---
try:
    from config import CLOUD_FUNCTION_URL, WIFI_SSID, WIFI_PASSWORD
except ImportError:
    print("Error: config.py not found or incomplete. Please create it.")
    CLOUD_FUNCTION_URL = 'http://localhost:8080/default_url_if_not_found' # Fallback or error URL
    # These fallbacks are for main.py's reconnection logic, if config.py fails
    WIFI_SSID = 'default_ssid'
    WIFI_PASSWORD = 'default_password'
# --- End Import config ---

# Ensure Wi-Fi is connected from boot.py
sta_if = network.WLAN(network.STA_IF)
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


def simulate_pzem_data():
    """
    Generates sample and random data to mimic PZEM-004T readings.
    """
    # EnerGreen Device Unique ID
    device_id = "energreen_esp32_001" # Choose a unique ID for your device

    # Simulate typical household values with some randomness
    voltage = round(random.uniform(220.0, 240.0), 1) # Volts (e.g., 220V - 240V in PH)
    current = round(random.uniform(0.1, 5.0), 3)    # Amps (e.g., 0.1A to 5.0A)
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
        "timestamp": time.time()
    }

print("EnerGreen ESP32 Ready! Starting simulated data collection loop...")

# Main application loop
while True:
    # Check Wi-Fi status at the start of each loop iteration
    if sta_if.isconnected():
        print("\nWi-Fi is connected. Simulating data...")
        simulated_data = simulate_pzem_data()
        print("--- Simulated Data ---")
        for key, value in simulated_data.items():
            print(f"{key}: {value}")
        print("----------------------")

        # --- HTTP POST to Cloud Function (NOW CORRECTLY INDENTED) ---
        try:
            headers = {'Content-Type': 'application/json'}
            payload = json.dumps(simulated_data)

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


    # This sleep is for the main loop iteration, not just after a send
    time.sleep(10) # Changed to 10 seconds for less aggressive sending