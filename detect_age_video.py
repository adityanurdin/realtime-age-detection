# USAGE
# python detect_age_video.py --face face_detector --age age_detector

# import the necessary packages
from imutils.video import VideoStream
# from gpiozero import LED
from time import sleep
import numpy as np
import argparse
import imutils
import time
import cv2
import os

def detect_and_predict_age(frame, faceNet, ageNet, minConf=0.5):
	# define the list of age buckets our age detector will predict
	AGE_BUCKETS = ["(0-2)", "(3-6)", "(7-12)", "(13-20)", "(21-32)",
		"(33-43)", "(44-53)", "(54-100)"]

	# initialize our results list
	results = []

	# grab the dimensions of the frame and then construct a blob
	# from it
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
		(104.0, 177.0, 123.0))

	# pass the blob through the network and obtain the face detections
	faceNet.setInput(blob)
	detections = faceNet.forward()

	# loop over the detections
	for i in range(0, detections.shape[2]):
		# extract the confidence (i.e., probability) associated with
		# the prediction
		confidence = detections[0, 0, i, 2]

		# filter out weak detections by ensuring the confidence is
		# greater than the minimum confidence
		if confidence > minConf:
			# compute the (x, y)-coordinates of the bounding box for
			# the object
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")

			# extract the ROI of the face
			face = frame[startY:endY, startX:endX]

			# ensure the face ROI is sufficiently large
			if face.shape[0] < 20 or face.shape[1] < 20:
				continue

			# construct a blob from *just* the face ROI
			faceBlob = cv2.dnn.blobFromImage(face, 1.0, (227, 227),
				(78.4263377603, 87.7689143744, 114.895847746),
				swapRB=False)

			# make predictions on the age and find the age bucket with
			# the largest corresponding probability
			ageNet.setInput(faceBlob)
			preds = ageNet.forward()
			i = preds[0].argmax()
			age = AGE_BUCKETS[i]
			ageConfidence = preds[0][i]

			# construct a dictionary consisting of both the face
			# bounding box location along with the age prediction,
			# then update our results list
			d = {
				"loc": (startX, startY, endX, endY),
				"age": (age, ageConfidence)
			}
			results.append(d)

	# return our results to the calling function
	return results

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--face", required=True,
	help="path to face detector model directory")
ap.add_argument("-a", "--age", required=True,
	help="path to age detector model directory")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
	help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

print("==========WELCOME TO SMART TRAFFIC LIGHT==========")

# load our serialized face detector model from disk
print("[INFO] loading face detector model...")
prototxtPath = os.path.sep.join([args["face"], "deploy.prototxt"])
weightsPath = os.path.sep.join([args["face"],
	"res10_300x300_ssd_iter_140000.caffemodel"])
faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)

# load our serialized age detector model from disk
print("[INFO] loading age detector model...")
prototxtPath = os.path.sep.join([args["age"], "age_deploy.prototxt"])
weightsPath = os.path.sep.join([args["age"], "age_net.caffemodel"])
ageNet = cv2.dnn.readNet(prototxtPath, weightsPath)

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(2.0)

print("[INFO] Turn on red light...")

# used to record the time when we processed last frame
prev_frame_time = 0
 
# used to record the time at which we processed current frame
new_frame_time = 0

# LED Red connect to GPIO-17
# led_red = LED(17)
# led_red.on()
# # LED Green connect to GPIO-22
# led_green = LED(22)

# define the countdown func.
def countdown(t):
    
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1

# loop over the frames from the video stream
while True:
	# grab the frame from the threaded video stream and resize it
	# to have a maximum width of 400 pixels
	frame = vs.read()

	frame = imutils.resize(frame, width=400)

	#show FPS
	font_fps = cv2.FONT_HERSHEY_SIMPLEX
	new_frame_time = time.time()
	fps = 1/(new_frame_time-prev_frame_time)
	prev_frame_time = new_frame_time

	fps = int(fps)
	fps = 'fps: ' + str(fps)
	
	cv2.putText(frame, fps, (7,70), font_fps, 0.5, (100, 255, 0), 1, cv2.LINE_AA)

	# print(fps, end="\r")

	# detect faces in the frame, and for each face in the frame,
	# predict the age
	results = detect_and_predict_age(frame, faceNet, ageNet,
		minConf=args["confidence"])

	if not results:
		print('[Err] Please check your camera');
		exit(0)

	# loop over the results
	for r in results:

		# draw the bounding box of the face along with the associated
		# predicted age
		text = "{}: {:.2f}%".format(r["age"][0], r["age"][1] * 100)
		(startX, startY, endX, endY) = r["loc"]
		y = startY - 10 if startY - 10 > 10 else startY + 10
		cv2.rectangle(frame, (startX, startY), (endX, endY),
			(0, 0, 255), 2)
		cv2.putText(frame, text, (startX, y),
			cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)

	# show the output frame
	cv2.imshow("Smart Traffic Light ", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break

	#menambahkan kondisi umur 
	now_age = r["age"][0]
	print("umur sekarang: " + now_age)
	if now_age == "(0-2)":
		print('[INFO] Lampu merah akan mati dalam 10 detik');
		countdown(10)
		# led_red.off()
		print('[INFO] Lampu merah mati');
		sleep(1)
		print('[INFO] Lampu hijau menyala selama 20 detik');
		# led_green.on()
		countdown(20)
		# led_green.off()
		print('[INFO] Lampu hijau mati');
		sleep(1)
		print('[INFO] Lampu merah kembali menyala');
	elif now_age == "(3-6)":
		print('[INFO] Lampu merah akan mati dalam 10 detik');
		countdown(10)
		# led_red.off()
		print('[INFO] Lampu merah mati');
		sleep(1)
		print('[INFO] Lampu hijau menyala selama 25 detik');
		# led_green.on()
		countdown(15)
		# led_green.off()
		print('[INFO] Lampu hijau mati');
		sleep(1)
		print('[INFO] Lampu merah kembali menyala');
	elif now_age == "(7-12)":
		print('[INFO] Lampu merah akan mati dalam 10 detik');
		countdown(10)
		# led_red.off()
		print('[INFO] Lampu merah mati');
		sleep(1)
		print('[INFO] Lampu hijau menyala selama 20 detik');
		# led_green.on()
		countdown(15)
		# led_green.off()
		print('[INFO] Lampu hijau mati');
		sleep(1)
		print('[INFO] Lampu merah kembali menyala');
	elif now_age == "(13-20)":
		print('[INFO] Lampu merah akan mati dalam 10 detik');
		countdown(10)
		# led_red.off()
		print('[INFO] Lampu merah mati');
		sleep(1)
		print('[INFO] Lampu hijau menyala selama 15 detik');
		# led_green.on()
		countdown(15)
		# led_green.off()
		print('[INFO] Lampu hijau mati');
		sleep(1)
		print('[INFO] Lampu merah kembali menyala');
	elif now_age == "(21-32)":
		print('[INFO] Lampu merah akan mati dalam 10 detik');
		countdown(10)
		# led_red.off()
		print('[INFO] Lampu merah mati');
		sleep(1)
		print('[INFO] Lampu hijau menyala selama 15 detik');
		# led_green.on()
		countdown(15)
		# led_green.off()
		print('[INFO] Lampu hijau mati');
		sleep(1)
		print('[INFO] Lampu merah kembali menyala');
	elif now_age == "(33-43)":
		print('[INFO] Lampu merah akan mati dalam 10 detik');
		countdown(10)
		# led_red.off()
		print('[INFO] Lampu merah mati');
		sleep(1)
		print('[INFO] Lampu hijau menyala selama 25 detik');
		# led_green.on()
		countdown(15)
		# led_green.off()
		print('[INFO] Lampu hijau mati');
		sleep(1)
		print('[INFO] Lampu merah kembali menyala');
	elif now_age == "(44-53)":
		print('[INFO] Lampu merah akan mati dalam 10 detik');
		countdown(10)
		# led_red.off()
		print('[INFO] Lampu merah mati');
		sleep(1)
		print('[INFO] Lampu hijau menyala selama 35 detik');
		# led_green.on()
		countdown(15)
		# led_green.off()
		print('[INFO] Lampu hijau mati');
		sleep(1)
		print('[INFO] Lampu merah kembali menyala');
	elif now_age == "(54-100)":
		print('[INFO] Lampu merah akan mati dalam 10 detik');
		countdown(10)
		# led_red.off()
		print('[INFO] Lampu merah mati');
		sleep(1)
		print('[INFO] Lampu hijau menyala selama 45 detik');
		# led_green.on()
		countdown(15)
		# led_green.off()
		print('[INFO] Lampu hijau mati');
		sleep(1)
		print('[INFO] Lampu merah kembali menyala');
		
		
		
		
		
		
# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()