from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
import os
import cv2
import numpy as np
from datetime import datetime
from werkzeug.utils import secure_filename

from config import UPLOAD_FOLDER, CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT
from database import db
from face_recognition_utils import face_system

app = Flask(__name__)
app.secret_key = "attendance_system_secret_key_2024"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# التأكد من وجود مجلد الصور
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== الصفحات الرئيسية ====================

@app.route("/")
def index():
    stats = db.get_today_stats()
    persons = db.get_all_persons()
    return render_template("index.html", stats=stats, persons=persons)

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/attendance")
def attendance_page():
    return render_template("attendance.html")

@app.route("/logs")
def logs_page():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    logs = db.get_attendance_logs(date=date)
    return render_template("logs.html", logs=logs, selected_date=date)

# ==================== API - الأشخاص ====================

@app.route("/api/persons", methods=["GET"])
def get_persons():
    persons = db.get_all_persons()
    return jsonify({"success": True, "persons": persons})

@app.route("/api/persons", methods=["POST"])
def add_person():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    role = request.form.get("role", "student")

    if not name:
        return jsonify({"success": False, "error": "الاسم مطلوب"})

    # معالجة الصورة
    photo_path = None
    if "photo" in request.files:
        file = request.files["photo"]
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            photo_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(photo_path)

    # استخراج ترميز الوجه
    face_encoding_path = None
    if photo_path:
        encoding, error = face_system.encode_face_from_image(photo_path)
        if encoding is not None:
            # إضافة الشخص أولاً
            person_id = db.add_person(name, email, phone, role, None, photo_path)
            if person_id:
                face_encoding_path = face_system.save_face_encoding(person_id, encoding)
                # تحديث المسار
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE persons SET face_encoding_path = ? WHERE id = ?",
                    (face_encoding_path, person_id)
                )
                conn.commit()
                conn.close()
                face_system.load_known_faces()
                return jsonify({"success": True, "person_id": person_id})
            else:
                return jsonify({"success": False, "error": "البريد الإلكتروني موجود مسبقاً"})
        else:
            return jsonify({"success": False, "error": error})

    person_id = db.add_person(name, email, phone, role, None, photo_path)
    if person_id:
        return jsonify({"success": True, "person_id": person_id})
    else:
        return jsonify({"success": False, "error": "البريد الإلكتروني موجود مسبقاً"})

@app.route("/api/persons/<int:person_id>", methods=["DELETE"])
def delete_person(person_id):
    db.delete_person(person_id)
    face_system.load_known_faces()
    return jsonify({"success": True})

# ==================== API - الحضور ====================

@app.route("/api/attendance/mark", methods=["POST"])
def mark_attendance():
    data = request.get_json()
    person_id = data.get("person_id")

    if not person_id:
        return jsonify({"success": False, "error": "معرف الشخص مطلوب"})

    success = db.mark_attendance(person_id)
    return jsonify({"success": success})

@app.route("/api/attendance/logs")
def get_logs():
    date = request.args.get("date")
    person_id = request.args.get("person_id", type=int)
    logs = db.get_attendance_logs(date=date, person_id=person_id)
    return jsonify({"success": True, "logs": logs})

@app.route("/api/attendance/stats")
def get_stats():
    stats = db.get_today_stats()
    return jsonify({"success": True, "stats": stats})

# ==================== كاميرا التعرف على الوجوه ====================


already_checked_today = set()
current_day = datetime.now().strftime("%Y-%m-%d")

# def generate_frames():
#     """توليد إطارات الفيديو مع التعرف على الوجوه"""
#     camera = cv2.VideoCapture(CAMERA_INDEX)
#     camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
#     camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

#     while True:
#         success, frame = camera.read()
#         if not success:
#             break

#         # التعرف على الوجوه
#         results = face_system.recognize_faces(frame)
#         frame = face_system.draw_faces(frame, results)

#         # تحويل إلى JPEG
#         ret, buffer = cv2.imencode(".jpg", frame)
#         frame_bytes = buffer.tobytes()

#         yield (b"--frame\r\n"
#                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

#     camera.release()

def generate_frames():
    global already_checked_today, current_day

    camera = cv2.VideoCapture(CAMERA_INDEX)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    while True:
        success, frame = camera.read()
        if not success:
            break

        # إعادة إعادة ضبط القائمة إذا تغير اليوم (عند منتصف الليل)
        today_now = datetime.now().strftime("%Y-%m-%d")
        if today_now != current_day:
            already_checked_today.clear()
            current_day = today_now

        # التعرف على الوجوه
        results = face_system.recognize_faces(frame)

        for result in results:
            person_id = result.get("person_id")
            confidence = result.get("confidence", 0)

            # الشرط: معرف موجود + نسبة الثقة > 50 + لم يتم فحصه مسبقاً اليوم
            # if person_id and confidence > 50:
            #     if person_id not in already_checked_today:
            #         # محاولة التسجيل في قاعدة البيانات
            #         success = db.mark_attendance(person_id)
            #         # إضافته للقائمة سواء سجل الآن أو كان محضراً مسبقاً لمنع التكرار
            #         already_checked_today.add(person_id)
            if person_id and confidence > 50:
                if person_id not in already_checked_today:
                    db.mark_attendance(person_id)
                    already_checked_today.add(person_id)

        # رسم المربعات والأسماء
        frame = face_system.draw_faces(frame, results)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

    camera.release()

@app.route("/video_feed")
def video_feed():
    try:
     return Response(generate_frames(),
                   mimetype="multipart/x-mixed-replace; boundary=frame")
    except Exception as e:
        print(e)

@app.route("/api/recognize", methods=["POST"])
def recognize_from_frame():
    """التعرف على وجه من صورة مرفوعة"""
    if "image" not in request.files:
        return jsonify({"success": False, "error": "لا توجد صورة"})

    file = request.files["image"]
    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "صيغة الملف غير مدعومة"})

    # حفظ مؤقت
    temp_path = os.path.join(UPLOAD_FOLDER, "temp_recognize.jpg")
    file.save(temp_path)

    # قراءة الصورة
    frame = cv2.imread(temp_path)
    if frame is None:
        return jsonify({"success": False, "error": "لا يمكن قراءة الصورة"})

    # التعرف
    results = face_system.recognize_faces(frame)

    # تسجيل الحضور تلقائياً
    recognized = []
    for result in results:
        if result["person_id"] and result["confidence"] > 50:
            db.mark_attendance(result["person_id"])
            recognized.append(result)

    # حذف الملف المؤقت
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return jsonify({
        "success": True,
        "results": results,
        "recognized": recognized
    })

# ==================== تشغيل التطبيق ====================

if __name__ == "__main__":
    print("🚀 تشغيل نظام الحضور...")
    print("📍 افتح المتصفح على: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
