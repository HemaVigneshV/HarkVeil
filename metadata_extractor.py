# modules/metadata_extractor.py

import uuid
import random
from datetime import datetime
import requests
from geopy.distance import geodesic

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

MAP_RADIUS_KM = 10

def get_current_ip():
    """Get the current public IP address."""
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "0.0.0.0"

def get_device_location():
    """
    Simulate device (callie's) location.
    In real apps, this would come from Android GPS.
    Here, it's hardcoded or randomly generated.
    """
    # Example: Bangalore coordinates
    return {"latitude": 16.485475, "longitude": 80.691727}

def spoof_caller_location(callie_coords, radius_km=MAP_RADIUS_KM):
    """
    Generate a random point within a radius of the callie.
    """
    radius_deg = radius_km / 111  # ~111 km per degree lat/lon
    lat_offset = random.uniform(-radius_deg, radius_deg)
    lon_offset = random.uniform(-radius_deg, radius_deg)
    return {
        "latitude": callie_coords["latitude"] + lat_offset,
        "longitude": callie_coords["longitude"] + lon_offset
    }

def extract_metadata():
    """
    Returns a metadata dict with simulated IPs and GPS.
    """
    call_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    callie_location = get_device_location()
    caller_location = spoof_caller_location(callie_location)

    return {
        "call_id": call_id,
        "timestamp": timestamp,
        "device_ip": get_current_ip(),
        "callie_location": callie_location,
        "caller_location": caller_location
    }

'''
if __name__ == "__main__":
    metadata = extract_metadata()
    print("[Metadata Extracted]")
    print(metadata)
'''