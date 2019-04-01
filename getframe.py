import cv2
import json
import os
cur_path = os.path.dirname(os.path.abspath(__file__))
with open('config.json') as f:
    config = json.load(f)

path_list = []

for (i, cam_ip) in enumerate(config["video_sources"]):
    cap = cv2.VideoCapture(cam_ip)
    ret, frame = cap.read()
    path = cur_path + r"\CamFrames\frame_cam{}.jpg".format(i)
    path_list.append(path)
    cv2.imwrite(path, frame)
    cap.release()
config["cam_frame_paths"] = path_list
with open('config.json', 'w') as f:
    json.dump(config, f, indent = 4)
