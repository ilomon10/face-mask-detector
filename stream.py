from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template, send_from_directory
from flask_socketio import SocketIO
import tflite_runtime.interpreter as tflite
import numpy as np
import calendar
import imutils
import threading
import argparse
import time
import cv2
import os
import board
import busio as io
import RPi.GPIO as GPIO
import adafruit_mlx90614

from debounce import debounce
from timeout import timeout

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

buzzerPin = 21
GPIO.setup(buzzerPin, GPIO.OUT)
GPIO.output(buzzerPin, GPIO.LOW)

PATH = os.getcwd()

outputFrame = None
lock = threading.Lock()
scannedState = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True, cors_allowed_origins="*")

vs = VideoStream(usePiCamera=1).start()
# vs = VideoStream(src=0).start()
time.sleep(2.0)

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/faces/<path:filename>")
def faces_page(filename):
    return send_from_directory('database', filename)

@app.route("/deleteFaces")
def delete_faces():
    DatabasePATH = "{0}/database".format(PATH)
    for f in os.listdir(DatabasePATH):
        os.remove(os.path.join(DatabasePATH, f))

    return "OK"

@socketio.on('connect')
def counter_connect():
    return None

def beep():
    GPIO.output(buzzerPin, GPIO.HIGH)
    print("Beep")
    time.sleep(0.1)
    GPIO.output(buzzerPin, GPIO.LOW)
    print("No Beep")

@debounce(3)
def simpan_gambar(frame):
    global scannedState
    timestamp = calendar.timegm(time.gmtime())
    cv2.imwrite("{0}/database/{1}.jpg".format(PATH, timestamp), frame)
    socketio.emit('new_face', {"image": "{0}.jpg".format(timestamp), "timestamp": timestamp})
    scannedState = False

def detect_mask(frameCount):
    
    global vs, outputFrame, lock, scannedState
    
    i2c = io.I2C(board.SCL, board.SDA, frequency=100000)
    mlx = adafruit_mlx90614.MLX90614(i2c)

    with open('lbl.txt', 'r') as f:
        labels = [line.strip() for line in f.readlines()]
    
    interpreter = tflite.Interpreter(model_path='model4.tflite')
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=480)
        frame_org = frame.copy()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imH, imW = frame.shape[:2]
        frame_resized = cv2.resize(frame_rgb, (width, height))
        input_data = np.expand_dims(frame_resized, axis=0)
        
        interpreter.set_tensor(input_details[0]['index'],input_data)
        interpreter.invoke()

        boxes = interpreter.get_tensor(output_details[0]['index'])[0] # Bounding box coordinates of detected objects
        classes = interpreter.get_tensor(output_details[1]['index'])[0] # Class index of detected objects
        scores = interpreter.get_tensor(output_details[2]['index'])[0] # Confidence of detected objects

        for i in range(len(scores)):
            if((scores[i]>0.3) and (scores[i]<=1.0)):
                ymin = int(max(1,(boxes[i][0] * imH)))
                xmin = int(max(1,(boxes[i][1] * imW)))
                ymax = int(min(imH,(boxes[i][2] * imH)))
                xmax = int(min(imW,(boxes[i][3] * imW)))

                temp = mlx.object_temperature
                err = 16.8
                cal = 3.8
                temp = ((temp * (err/100)) + temp) + cal

                color = (10, 255, 0)

                if classes[i] :
                    color = (10, 120, 255)

                if temp > 38.0:
                    color = (10, 0, 255)

                # cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), color, 2)
                cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), color, 2)

                object_name = labels[int(classes[i])] # Look up object name from "labels" array using class index
                label = "{0}: {1}C".format(object_name, str(round(temp, 1))) # Example: 'person: 72%'7
                labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size
                label_ymin = max(ymin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
                cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), color, cv2.FILLED) # Draw white box to put label text in
                cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text

                save_frame = frame_org.copy()
                
                cv2.putText(save_frame, "{0}".format(object_name), (xmin, label_ymin+12), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2) # Draw label text
                cv2.putText(save_frame, "{0}C".format(str(round(temp, 1))), (xmin, ymax-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2) # Draw label text

                if not scannedState:
                    time.sleep(1)
                    beep()

                scannedState = True
                simpan_gambar(save_frame[ymin:ymax, xmin:xmax])
        
        cv2.circle(frame, (int(imW/2), int(imH/3)), 2, (0, 0, 255), 2)

        with lock:
            outputFrame = frame.copy()

def generate():
	global outputFrame, lock

	while True:
		with lock:
			if outputFrame is None:
				continue

			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

			if not flag:
				continue

		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
	# return the response generated along with the specific media
	# type (mime type)
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
	# construct the argument parser and parse command line arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--ip", type=str, required=True,
		help="ip address of the device")
	ap.add_argument("-o", "--port", type=int, required=True,
		help="ephemeral port number of the server (1024 to 65535)")
	ap.add_argument("-f", "--frame-count", type=int, default=32,
		help="# of frames used to construct the background model")
	args = vars(ap.parse_args())

	# start a thread that will perform motion detection
	t = threading.Thread(target=detect_mask, args=(
		args["frame_count"],))
	t.daemon = True
	t.start()
    # socketio.run(app)

	# start the flask app
	socketio.run(app, host=args["ip"], port=args["port"], debug=True, use_reloader=False)

GPIO.cleanup()
vs.stop()