from HumanDetection import DetectorAPI
import threading
import json
from newVideoCap import MyVideoCapture
from database import Database


def analyze():
    model_path = './faster_rcnn_inception_v2_coco_2018_01_28/frozen_inference_graph.pb'
    odapi = DetectorAPI(path_to_ckpt=model_path)


    with open('config.json') as f:
        config = json.load(f)

    video_sources = config["video_sources"]
    points_sources = config["points_sources"]


    videos = []
    alert_queue = [[]]
    for i, video_source in enumerate(video_sources):
        videos.append(MyVideoCapture(video_source, points_sources[i], i, config, odapi))


    def analyzeVid(idx):
        cap = videos[idx]
        while cap.cap.isOpened():
            cap.getFrame()
            if(len(alert_queue[0]) > 0):
                print("Alert")
                alert_queue[0] = []

    jobs = []
    for idx in range( len(videos)):
        process = threading.Thread(target= analyzeVid, args=(idx,))
        process.start()
        jobs.append(process)

    for job in jobs:
        job.join()