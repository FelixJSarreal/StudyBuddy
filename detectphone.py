#!/usr/bin/env python3
import cv2
import time
import numpy as np
import urllib.request
import requests
from ultralytics import YOLO

# --- Configuration ---
PI_ZERO_STREAM = "http://<IPAddressHere>:8080/video"       # MJPEG camera stream
PI_ZERO_LED_ON = "http://<IPAddressHere>:5000/led/on"      # LED ON endpoint
PI_ZERO_LED_OFF = "http://<IPAddressHere>:5000/led/off"    # LED OFF endpoint

# --- YOLOv8 Model ---
model = YOLO("yolov8n.pt")  # Use yolov8s.pt for more accuracy

# --- MJPEG Stream Setup ---
stream = urllib.request.urlopen(PI_ZERO_STREAM)
bytes_buffer = b''

# --- State ---
frame_number = 0
detected_count = 0
ready_to_trigger = True
prev_time = time.time()
led_on = False

# --- Main Loop ---
try:
    while True:
        # Flush stale MJPEG chunks (to reduce lag)
        for _ in range(5):
            bytes_buffer += stream.read(1024)
            a_flush = bytes_buffer.find(b'\xff\xd8')
            b_flush = bytes_buffer.find(b'\xff\xd9')
            if a_flush != -1 and b_flush != -1:
                bytes_buffer = bytes_buffer[b_flush+2:]

        # Read frame
        bytes_buffer += stream.read(1024)
        a = bytes_buffer.find(b'\xff\xd8')
        b = bytes_buffer.find(b'\xff\xd9')

        if a != -1 and b != -1:
            jpg = bytes_buffer[a:b+2]
            bytes_buffer = bytes_buffer[b+2:]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Fix red/blue flip

            frame_number += 1
            current_time = time.time()
            fps = 1 / (current_time - prev_time)
            prev_time = current_time

            # YOLOv8 Inference
            results = model.predict(source=frame, classes=[67], conf=0.4, verbose=False)
            detections = results[0].boxes

            # Update detection streak count
            if detections and len(detections) > 0:
                detected_count += 1
            else:
                detected_count = 0
                ready_to_trigger = True  # Reset trigger when detections break

            # Turn LED ON after 5 consecutive detections
            if detected_count == 5 and ready_to_trigger and not led_on:
                try:
                    requests.get(PI_ZERO_LED_ON, timeout=1)
                    print("? LED ON command sent to Pi Zero")
                    led_on = True
                    ready_to_trigger = False
                except Exception as e:
                    print(f"?? Failed to trigger LED ON: {e}")

            # Turn LED OFF when no detections and LED is currently on
            if led_on and detected_count == 0:
                try:
                    requests.get(PI_ZERO_LED_OFF, timeout=1)
                    print("? LED OFF command sent to Pi Zero")
                    led_on = False
                except Exception as e:
                    print(f"?? Failed to trigger LED OFF: {e}")

            # Annotate and display
            annotated = results[0].plot()
            cv2.putText(annotated, f"Frame: {frame_number}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.putText(annotated, f"Detections: {detected_count}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            cv2.putText(annotated, f"FPS: {fps:.1f}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

            cv2.imshow("YOLOv8 Phone Detector (Remote)", annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

except KeyboardInterrupt:
    print("? Interrupted")

finally:
    cv2.destroyAllWindows()
