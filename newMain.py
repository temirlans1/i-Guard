from HumanDetection import DetectorAPI
import threading
import json
from newVideoCap import MyVideoCapture
from database import Database
import cv2


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
            frame_out = cap.getFrame()
            if(frame_out is None):
                continue
            if(len(alert_queue[0]) > 0):
                print("Alert")
                alert_queue[0] = []
            if(frame_out.shape[0] > 0):
                frame_out = cv2.resize(frame_out, (0, 0), fx = 0.5, fy = 0.5)
                cv2.imshow("IGUARD", frame_out)

                k = cv2.waitKey(1)
                if k == ord('q'):
                    print("Cap is closed")
                    cv2.destroyAllWindows()
                    break


    analyzeVid(0)
    #jobs = []
    #for idx in range( len(videos)):
    #    analyzeVid(idx)
        #process = threading.Thread(target= analyzeVid, args=(idx,))
        #process.start()
        #jobs.append(process)

    #for job in jobs:
    #    job.join()

if __name__ == "__main__":
    analyze()