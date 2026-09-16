# إعدادات نظام الحضور
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# قاعدة البيانات
DATABASE_PATH = os.path.join(BASE_DIR, "attendance.db")

# مجلد الصور
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "faces")
KNOWN_FACES_DIR = os.path.join(BASE_DIR, "known_faces")

# إعدادات الكاميرا
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# إعدادات التعرف على الوجوه
FACE_TOLERANCE = 0.6  # كلما قلّت القيمة = دقة أعلى (صعوبة أكبر في التطابق)

# إعدادات التطبيق
SECRET_KEY = "attendance_system_secret_key_2024"
DEBUG = True
