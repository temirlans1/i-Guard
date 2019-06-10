from VideoCap import MyVideoCapture
import cv2
import json

with open('config.json') as f:
    config = json.load(f)

vidCap = MyVideoCapture("../datasets/vid6.avi", "../datasets/coords1_17.yml", 0, config, [], [])

while True:
    frame = vidCap.get_frame([0], True)
    cv2.imshow("frame", frame)
    k = cv2.waitKey(1)
    if k == ord('q'):
        break