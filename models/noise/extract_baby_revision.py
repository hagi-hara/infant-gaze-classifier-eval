import pandas as pd
import os
import cv2
import numpy as np

def calc_angle(img, frame):
    # left_eye = (int(frame[" eye_lmk_x_23"]), int(frame[" eye_lmk_y_23"]))
    # cv2.circle(img, left_eye, 10, (0, 255, 0), -1)
    # right_eye = (int(frame[" eye_lmk_x_55"]), int(frame[" eye_lmk_y_55"]))
    # cv2.circle(img, right_eye, 10, (0, 255, 0), -1)

    # tan = (frame[" eye_lmk_y_23"] - frame[" eye_lmk_y_55"])/(frame[" eye_lmk_x_23"] - frame[" eye_lmk_x_55"])
    # angle = np.arctan(tan)
    # cv2.line(img, left_eye, right_eye, (100, 100, 100), 10)
    return float(frame[" pose_Rz"].iloc[0])

def calc_face_pixel(img, frame):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0]
    left_points = [0, 3, 5, 8, 33, 27, 21, 19, 17]
    right_points = [16, 13, 11, 8, 33, 27, 22, 24, 26]

    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    left_face = np.array([[int(frame[" x_{}".format(idx)].iloc[0]), int(frame[" y_{}".format(idx)].iloc[0])] for idx in left_points])
    cv2.fillConvexPoly(mask, left_face, 255)
    right_face = np.array([[int(frame[" x_{}".format(idx)].iloc[0]), int(frame[" y_{}".format(idx)].iloc[0])] for idx in right_points])
    cv2.fillConvexPoly(mask, right_face, 255)
    mu, std = cv2.meanStdDev(L, mask=mask)

    area = cv2.countNonZero(mask)

    cv2.fillConvexPoly(img, left_face, (255, 255, 255))
    cv2.fillConvexPoly(img, right_face, (255, 255, 255))
    cv2.putText(img, str(int(area)), (int(frame[" x_4"].iloc[0]), int(frame[" y_4"].iloc[0])), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,0))

    return mu[0][0], std[0][0], area

def calc_offset(img, frame):
    h, w, c = img.shape
    offset = int(frame[" x_28"].iloc[0])
    cv2.line(img, (offset, 0), (offset, h), (155, 255, 0), 5)
    return frame[" pose_Tx"].iloc[0], frame[" pose_Ty"].iloc[0]

def calc_distance(img, frame):
    distance = int(frame[" pose_Tz"].iloc[0])
    cv2.putText(img, "Z: " + str((distance)), (50, 100), cv2.FONT_HERSHEY_PLAIN, 5, (0,0,200), thickness=4)
    return frame[" pose_Tz"].iloc[0]

# def detection_rate(frame):
#     count = frame.isnull().sum(axis=1)
#     return frame[" "]

# folders = ["Public_brighterAI/", "Scientific_brighterAI/", "Private_brighterAI/"]
folders = ["Public/", "Scientific/", "Private/", 
           "Public_brighterAI/", "Scientific_brighterAI/", "Private_brighterAI/"]
# folders = ["Public/"]

for folder in folders:
    of_folder = "results/" + folder.replace("_", "")
    video_folder = "../InputData/" + folder
    files = os.listdir(of_folder)
    for file in files:
        print(file)
        df = pd.read_csv(of_folder + file + "/" + file + ".csv")
        min_df = df.loc[df.groupby("frame")[" y_33"].idxmax()]
        min_df = min_df.astype({"frame": "int"})

        video_data = cv2.VideoCapture(video_folder + file + ".mp4")
        video_width = int(video_data.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_hight = int(video_data.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video_fps = video_data.get(cv2.CAP_PROP_FPS)

        print('FPS:',video_data.get(cv2.CAP_PROP_FPS))
        print('Dimensions:',video_width,video_hight)

        video_data_array = []

        print("VideoFrame:", int(video_data.get(cv2.CAP_PROP_FRAME_COUNT)))

        # #ファイルが正常に読み込めている間ループする
        while video_data.isOpened():
            #1フレームごとに読み込み
            success, image = video_data.read()
            if success:
            #フレームの画像を追加
                video_data_array.append(image)
            else:
                break
        video_data.release()

        output_file = cv2.VideoWriter(of_folder + file + "/" + file + ".mp4",cv2.VideoWriter_fourcc(*'MP4V'),video_fps,(video_width,video_hight))

        frames = []
        values = []
        pre_ox = None
        pre_oy = None
        for counter, image_data in enumerate(video_data_array):

            frame = min_df[min_df["frame"] == counter + 1]
            h, w, c = image_data.shape
            total = h * w
            print(counter)
            if len(frame) == 1 and float(frame[" confidence"].iloc[0])>0.5:  
                angle = calc_angle(image_data, frame)
                mu, std, area = calc_face_pixel(image_data, frame)
                pixel_rate = area/total
                ox, oy = calc_offset(image_data, frame)
                distance = calc_distance(image_data, frame) #location of 3D landmarks in millimetres, the landmark index can be seen below.
                # print(frame[" Y_33"], frame[" X_33"])
                if ox and oy:
                    if pre_ox and pre_oy:
                        move = np.sqrt((ox-pre_ox)**2 + (oy-pre_oy)**2)
                    else:
                        move = None
                    pre_ox = ox
                    pre_oy = oy               
                else:
                    move = None
                    pre_ox = None
                    pre_oy = None 
                values.append([counter, ox, oy, move, mu, std, angle, distance, pixel_rate, area, total, float(frame[" confidence"].iloc[0])])
            else:
                pre_ox = None
                pre_oy = None
                values.append([counter, None, None, None, None, None, None, None, None, None, None, None])           
            output_file.write(image_data)

        output_file.release()
        

        # d1 = {"frame": frames}
        # d2 = dict(zip(values, positions))
        # d = dict(**d1, **d2)
        df = pd.DataFrame(values, columns=["frame", "offset_x", "offset_y", "move", "mu", "std", "angle", "distance", "pixel_rate", "area", "total", "occlusion"])
        df.to_csv(of_folder + file + "/" + file + "_extracted.csv", index=False)