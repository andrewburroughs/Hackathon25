from fastapi import FastAPI, File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
import cv2
import dlib
import numpy as np
import os

app = FastAPI()

# CORS for extension access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all. Lock down in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup
detector = dlib.get_frontal_face_detector()
trackers = []
tracking_states = []
bboxes = []
tracker_type = 'CSRT'
detection_interval = 30
frame_count = 0
expected_frame_size = None
frames_since_lost_list = []
grace_period = 10
face_saved = False
output_directory = "saved_faces"
os.makedirs(output_directory, exist_ok=True)

if tracker_type == 'KCF':
    tracker_algorithm_type = cv2.TrackerKCF_create
elif tracker_type == 'CSRT':
    tracker_algorithm_type = cv2.TrackerCSRT_create
elif tracker_type == 'MOSSE':
    tracker_algorithm_type = cv2.TrackerMOSSE_create
else:
    tracker_algorithm_type = None

def getBlurredImage(frame):
    global frame_count, expected_frame_size, trackers, tracking_states, bboxes, frames_since_lost_list, face_saved

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width = frame.shape[:2]
    current_frame_size = frame.shape[:2]

    if expected_frame_size is None:
        expected_frame_size = current_frame_size
    elif current_frame_size != expected_frame_size:
        trackers.clear()
        tracking_states.clear()
        bboxes.clear()
        frames_since_lost_list.clear()
        expected_frame_size = current_frame_size
        return frame

    frame_count += 1

    # Face detection
    if not any(tracking_states) or frame_count % detection_interval == 0:
        faces = detector(gray_frame, 1)
        for face in faces:
            x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()
            new_bbox = (x1, y1, x2 - x1, y2 - y1)

            is_new_face = True
            for i, existing_bbox in enumerate(bboxes):
                ex, ey, ew, eh = existing_bbox
                nx, ny, nw, nh = new_bbox
                if abs(nx - ex) < 50 and abs(ny - ey) < 50 and abs(nw - ew) < 50 and abs(nh - eh) < 50 and tracking_states[i]:
                    is_new_face = False
                    break

            if is_new_face and tracker_algorithm_type is not None:
                tracker = tracker_algorithm_type()
                tracker.init(frame, new_bbox)
                trackers.append(tracker)
                tracking_states.append(True)
                bboxes.append(new_bbox)
                frames_since_lost_list.append(0)
                frame_count = 0

    # Update trackers
    updated_trackers, updated_states, updated_bboxes, updated_lost = [], [], [], []

    for i, tracker_obj in enumerate(trackers):
        success, bbox = tracker_obj.update(frame)
        if success:
            x, y, w, h = [int(v) for v in bbox]
            x, y, w, h = max(0, x), max(0, y), min(w, width - x), min(h, height - y)

            if w > 40 and h > 40 and 0.7 < w / h < 1.3:
                face_roi = frame[y:y+h, x:x+w]
                if face_roi.size > 0:
                    if not face_saved:
                        filename = os.path.join(output_directory, f"first_face_{cv2.getTickCount()}.png")
                        cv2.imwrite(filename, face_roi)
                        face_saved = True
                    blurred_face = cv2.GaussianBlur(face_roi, (81, 81), 0)
                    frame[y:y+h, x:x+w] = blurred_face
                    updated_trackers.append(tracker_obj)
                    updated_states.append(True)
                    updated_bboxes.append((x, y, w, h))
                    updated_lost.append(0)
                    continue
        updated_states.append(False)
        updated_lost.append(frames_since_lost_list[i] + 1)

    trackers[:] = updated_trackers
    tracking_states[:] = updated_states
    bboxes[:] = updated_bboxes
    frames_since_lost_list[:] = updated_lost

    return frame

@app.post("/blur")
async def blur_image(file: UploadFile = File(...)):
    content = await file.read()
    np_arr = np.frombuffer(content, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return Response("Invalid image", status_code=400)

    blurred = getBlurredImage(frame)
    _, encoded = cv2.imencode(".jpg", blurred)
    return Response(encoded.tobytes(), media_type="image/jpeg")
