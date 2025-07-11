# main.py
import time
import random # For generating random data
import network # To check WiFi status
import urequests
import json # Needed to convert dictionary to JSON string

# --- Import Cloud Function URL from secrets ---
try:
    from config import CLOUD_FUNCTION_URL
except ImportError:
    print("Error: CLOUD_FUNCTION_URL not found in secrets.py. Please check secrets.py.")
    CLOUD_FUNCTION_URL = 'http://localhost:8080/default_url_if_not_found' # Fallback or error URL
# --- End Import secrets ---

# Ensure Wi-Fi is connected from boot.py
sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print("Wi-Fi not connected in main.py. Please check boot.py.")
    # You might want to halt or retry connection here if necessary for your application
    # For now, we'll just continue but you won't be able to send data.

def simulate_pzem_data():
    """
    Generates sample and random data to mimic PZEM-004T readings.
    """
    # Simulate typical household values with some randomness
    voltage = round(random.uniform(220.0, 240.0), 1) # Volts (e.g., 220V - 240V in PH)
    current = round(random.uniform(0.1, 5.0), 3)   # Amps (e.g., 0.1A to 5.0A)
    power = round(voltage * current * random.uniform(0.8, 1.0), 1) # Watts (P = V * I * PF)
    energy = round(random.uniform(100.0, 500.0), 3) # kWh (cumulative, so it should increase in real scenario)
    frequency = round(random.uniform(59.8, 60.2), 1) # Hz (e.g., 60Hz in PH)
    power_factor = round(random.uniform(0.7, 0.99), 2)

    return {
        "Voltage": voltage,
        "Current": current,
        "Power": power,
        "Energy": energy,
        "Frequency": frequency,
        "PowerFactor": power_factor,
        "Timestamp": time.time() # Add a timestamp for when data was generated
    }

print("EnerGreen ESP32 Ready! Starting simulated data collection loop...")

# Main application loop
while True:
    if sta_if.isconnected():
        print("\nWi-Fi is connected. Simulating data...")
        simulated_data = simulate_pzem_data()
        print("--- Simulated Data ---")
        for key, value in simulated_data.items():
            print(f"{key}: {value}")
        print("----------------------")

        # --- Placeholder for HTTP POST to Cloud Function ---
        # In the next steps, we will add the code here to send 'simulated_data'
        # to your Cloud Function via HTTP POST.
        print("Placeholder: Data would be sent to Cloud Function here.")
        # ----------------------------------------------------

    else:
        print("\nWi-Fi disconnected. Attempting to reconnect...")
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD) # Use the same credentials from boot.py
        timeout = 0
        while not sta_if.isconnected() and timeout < 10:
            print('.', end='')
            time.sleep(1)
            timeout += 1
        if sta_if.isconnected():
            print("\nReconnected!")
        else:
            print("\nStill unable to connect to Wi-Fi.")


    time.sleep(2) # Simulate data every 2 seconds