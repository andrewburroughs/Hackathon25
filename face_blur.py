import cv2
import dlib
import numpy as np

def video_stream():
    detector = dlib.get_frontal_face_detector()
    video_capture = cv2.VideoCapture(0)

    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    trackers = []  # List to store trackers for each face
    tracking_states = [] # List to store the tracking state (True/False) for each tracker
    bboxes = []    # List to store bounding boxes for each face
    tracker_type = 'CSRT'
    detection_interval = 30
    frame_count = 0
    expected_frame_size = None
    frames_since_lost_list = [] # List to track frames since lost for each tracker
    grace_period = 10

    if tracker_type == 'KCF':
        tracker_algorithm_type = cv2.TrackerKCF_create
    elif tracker_type == 'CSRT':
        tracker_algorithm_type = cv2.TrackerCSRT_create
    elif tracker_type == 'MOSSE':
        tracker_algorithm_type = cv2.TrackerMOSSE_create
    else:
        tracker_algorithm_type = None

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        height, width = frame.shape[:2]

        current_frame_size = frame.shape[:2]
        if expected_frame_size is None:
            expected_frame_size = current_frame_size
        elif current_frame_size != expected_frame_size:
            print(f"Warning: Frame size changed from {expected_frame_size} to {current_frame_size}. Resetting trackers.")
            trackers = []
            tracking_states = []
            bboxes = []
            frames_since_lost_list = []
            expected_frame_size = current_frame_size
            continue

        frame_count += 1

        if not any(tracking_states) or frame_count % detection_interval == 0:
            faces = detector(gray_frame, 1)
            if len(faces) > 0:
                for face in faces:
                    x1 = face.left()
                    y1 = face.top()
                    x2 = face.right()
                    y2 = face.bottom()
                    new_bbox = (x1, y1, x2 - x1, y2 - y1)

                    # Check if this face is already being tracked (simple approach: proximity)
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
        updated_trackers = []
        updated_tracking_states = []
        updated_bboxes = []
        updated_frames_since_lost = []

        for i, tracker_obj in enumerate(trackers):
            success, bbox = tracker_obj.update(frame)
            if success:
                (x, y, w, h) = [int(v) for v in bbox]

                x = max(0, x)
                y = max(0, y)
                w = min(w, width - x)
                h = min(h, height - y)

                if w > 40 and h > 40 and 0.7 < w / h < 1.3:
                    face_roi = frame[y:y+h, x:x+w]
                    if face_roi.size > 0:
                        blurred_face = cv2.GaussianBlur(face_roi, (81, 81), 0)
                        frame[y:y+h, x:x+w] = blurred_face
                        updated_trackers.append(tracker_obj)
                        updated_tracking_states.append(True)
                        updated_bboxes.append((x, y, w, h))
                        updated_frames_since_lost.append(0)
                    else:
                        updated_tracking_states.append(False)
                        updated_frames_since_lost.append(frames_since_lost_list[i] + 1)
                else:
                    updated_tracking_states.append(False)
                    updated_frames_since_lost.append(frames_since_lost_list[i] + 1)
            else:
                updated_tracking_states.append(False)
                updated_frames_since_lost.append(frames_since_lost_list[i] + 1)

        trackers = updated_trackers
        tracking_states = updated_tracking_states
        bboxes = updated_bboxes
        frames_since_lost_list = updated_frames_since_lost

        for i, bbox in enumerate(bboxes):
            if tracking_states[i]:
                x, y, w, h = [int(v) for v in bbox]

        cv2.imshow('Video Face Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()