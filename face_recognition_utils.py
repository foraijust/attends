import face_recognition
import cv2
import numpy as np
import pickle
import os
from config import KNOWN_FACES_DIR, FACE_TOLERANCE
from database import db

class FaceRecognitionSystem:
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []
        self.load_known_faces()

    def load_known_faces(self):
        """تحميل الوجوه المعروفة من قاعدة البيانات"""
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []

        persons = db.get_all_persons()

        for person in persons:
            encoding_path = person.get("face_encoding_path")
            if encoding_path and os.path.exists(encoding_path):
                try:
                    with open(encoding_path, "rb") as f:
                        encoding = pickle.load(f)
                    self.known_encodings.append(encoding)
                    self.known_names.append(person["name"])
                    self.known_ids.append(person["id"])
                except Exception as e:
                    print(f"خطأ في تحميل الوجه {person['name']}: {e}")

        print(f"✅ تم تحميل {len(self.known_encodings)} وجه معروف")

    def encode_face_from_image(self, image_path):
        """استخراج ترميز الوجه من صورة"""
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) == 0:
            return None, "لم يتم العثور على وجه في الصورة"

        if len(encodings) > 1:
            return None, "تم العثور على أكثر من وجه في الصورة"

        return encodings[0], None

    def save_face_encoding(self, person_id, encoding):
        """حفظ ترميز الوجه"""
        encoding_path = os.path.join(KNOWN_FACES_DIR, f"person_{person_id}.pkl")
        with open(encoding_path, "wb") as f:
            pickle.dump(encoding, f)
        return encoding_path

    def recognize_faces(self, frame):
        """التعرف على الوجوه في إطار الفيديو"""
        # تصغير الإطار لسرعة المعالجة
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # اكتشاف الوجوه
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        results = []

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown"
            person_id = None
            confidence = 0

            if len(self.known_encodings) > 0:
                matches = face_recognition.compare_faces(
                    self.known_encodings, face_encoding, tolerance=FACE_TOLERANCE
                )
                face_distances = face_recognition.face_distance(
                    self.known_encodings, face_encoding
                )

                if True in matches:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_names[best_match_index]
                        person_id = self.known_ids[best_match_index]
                        confidence = 1 - face_distances[best_match_index]

            # تكبير الإحداثيات للإطار الأصلي
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            results.append({
                "name": name,
                "person_id": person_id,
                "confidence": round(confidence * 100, 2),
                "location": (top, right, bottom, left)
            })

        return results

    def draw_faces(self, frame, results):
        """رسم مربعات حول الوجوه"""
        for result in results:
            top, right, bottom, left = result["location"]
            name = result["name"]
            confidence = result["confidence"]

            # لون المربع
            if name == "Unknown":
                color = (0, 0, 255)  # أحمر
            else:
                color = (0, 255, 0)  # أخضر

            # رسم المربع
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # رسم الخلفية للنص
            label = f"{name} ({confidence}%)"
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 6, bottom - 6),
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

        return frame

    def capture_face_image(self, camera_index=0, save_path=None):
        """التقاط صورة وجه من الكاميرا"""
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return None, "لا يمكن فتح الكاميرا"

        captured_image = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # عرض الإطار
            display_frame = frame.copy()
            cv2.putText(display_frame, "اضغط 'C' للالتقاط | 'Q' للخروج",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.imshow("Capture Face", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('c') or key == ord('C'):
                captured_image = frame.copy()
                break
            elif key == ord('q') or key == ord('Q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        if captured_image is not None and save_path:
            cv2.imwrite(save_path, captured_image)
            return save_path, None

        return captured_image, None

# كائن عام
face_system = FaceRecognitionSystem()
