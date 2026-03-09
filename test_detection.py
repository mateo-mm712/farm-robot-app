#!/usr/bin/env python3
"""Quick test of USB device detection"""
import sys
sys.path.insert(0, '/mnt/managed_home/farm-ng-user-mateomm2004/farm-robot-app/src')

from config.devices import find_device_by_vid_pid, SENSOR_VID, SENSOR_PID, RELAY_VID, RELAY_PID

print("=" * 60)
print("TESTING RELAY DETECTION")
print("=" * 60)
relay_port = find_device_by_vid_pid(RELAY_VID, RELAY_PID)
print(f"Result: {relay_port}\n")

print("=" * 60)
print("TESTING SENSOR DETECTION")
print("=" * 60)
sensor_port = find_device_by_vid_pid(SENSOR_VID, SENSOR_PID)
print(f"Result: {sensor_port}\n")
