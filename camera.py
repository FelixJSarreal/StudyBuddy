#!/usr/bin/env python3
from flask import Flask, Response
from picamera2 import Picamera2
import cv2

app = Flask(__name__)
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (600, 1080)}))
picam2.start()

def generate():
    while True:
        frame = picam2.capture_array()
        rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        ret, jpeg = cv2.imencode('.jpg', rotated_frame)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

@app.route('/video')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
    