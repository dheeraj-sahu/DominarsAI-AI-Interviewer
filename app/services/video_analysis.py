import cv2
import numpy as np
import os
import json
from datetime import datetime

class VideoIntegrityAnalyzer:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.face_movement_threshold = 25
        self.eye_movement_threshold = 18
        self.analysis_frame_skip = 15  # Increased skip rate for performance on longer video
        self.face_centers = []
        self.eye_centers = []

    def get_center(self, rect):
        x, y, w, h = rect
        return (x + w//2, y + h//2)

    def calculate_distance(self, p1, p2):
        if p1 is None or p2 is None:
            return 0
        return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    def detect_eyes(self, face_roi):
        eyes = self.eye_cascade.detectMultiScale(
            face_roi,
            scaleFactor=1.15,
            minNeighbors=4,
            minSize=(12, 12),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        return eyes

    def analyze_frame(self, frame, prev_face_centers):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=4, minSize=(60,60), flags=cv2.CASCADE_SCALE_IMAGE)
        analysis = {
            'faces_detected': len(faces),
            'face_movement': 0,
            'eye_movement': 0,
            'looking_away': False,
            'multi_face': False,
            'eyes_detected': 0
        }
        face_center = None # Initialize face_center
        if len(faces) > 0:
            analysis['multi_face'] = len(faces) > 1
            largest_face = max(faces, key=lambda f: f[2]*f[3])
            x,y,w,h = largest_face
            face_center = self.get_center(largest_face)
            
            if prev_face_centers and prev_face_centers[-1]:
                prev_center = prev_face_centers[-1]
                face_movement = self.calculate_distance(face_center, prev_center)
                if face_movement > self.face_movement_threshold:
                    analysis['looking_away'] = True
                analysis['face_movement'] = face_movement

            face_roi = gray[y:y+h, x:x+w]
            eyes = self.detect_eyes(face_roi)
            analysis['eyes_detected'] = len(eyes)
            
            if len(eyes) >= 2:
                # This logic remains the same
                pass
            else:
                analysis['looking_away'] = True
        else:
            analysis['looking_away'] = True

        self.face_centers.append(face_center)
        return analysis

    def analyze_video(self, video_path, output_dir):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Cannot open video file: {video_path}")

        results = []
        suspicious_events = []
        
        self.face_centers = []
        self.eye_centers = []
        
        frame_index = 0
        last_processed_time = -500 # Initialize to ensure the first frame is processed
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # --- FIX APPLIED HERE ---
            # Get timestamp directly from the video frame in milliseconds
            current_time_msec = cap.get(cv2.CAP_PROP_POS_MSEC)

            # Process a frame roughly every 500 milliseconds (0.5 seconds)
            if current_time_msec - last_processed_time < 500:
                continue
            
            last_processed_time = current_time_msec
            timestamp = current_time_msec / 1000.0 # Convert to seconds

            analysis = self.analyze_frame(frame, self.face_centers)
            analysis['timestamp'] = timestamp
            results.append(analysis)

            if analysis['looking_away'] or analysis['multi_face']:
                suspicious_event = {
                    'timestamp': timestamp,
                    'type': 'multi_face' if analysis['multi_face'] else 'looking_away',
                    'details': {
                        'face_movement': analysis['face_movement'],
                        'eye_movement': analysis['eye_movement'],
                        'faces_detected': analysis['faces_detected'],
                        'eyes_detected': analysis['eyes_detected']
                    }
                }
                suspicious_events.append(suspicious_event)

        # Save the final log file
        scores = [{'timestamp': r['timestamp'], 'score': (r.get('face_movement', 0) + r.get('eye_movement', 0))} for r in results]
        log_data = {'scores_over_time': scores, 'suspicious_events': suspicious_events}
        
        with open(os.path.join(output_dir, 'proctoring_log.json'), 'w') as f:
            json.dump(log_data, f, indent=4)
            
        cap.release()
        print(f"Video analysis complete for {video_path}. Log saved.")
        return results, suspicious_events