# خطة مشروع نظام الحضور الذكي
## Face Recognition Attendance System

---

## 1. نظرة عامة
نظام ويب متكامل للحضور يعتمد على التعرف على الوجوه باستخدام Python و Flask و OpenCV و face_recognition.

## 2. هيكل المشروع
```
attendance_system/
├── app.py                      # التطبيق الرئيسي (Flask)
├── config.py                   # الإعدادات
├── database.py                 # قاعدة البيانات (SQLite)
├── face_recognition_utils.py   # التعرف على الوجوه
├── requirements.txt            # المتطلبات
├── README.md                   # الشرح
├── plan.md                     # هذه الوثيقة
├── attendance.db               # قاعدة البيانات (تنشأ تلقائياً)
├── known_faces/                # ترميزات الوجوه
│   └── person_1.pkl
├── static/
│   ├── css/style.css          # التنسيقات
│   ├── js/main.js             # الجافاسكربت
│   └── uploads/faces/         # صور الأشخاص
└── templates/
    ├── base.html
    ├── index.html
    ├── register.html
    ├── attendance.html
    └── logs.html
```

## 3. المتطلبات التقنية

### 3.1 متطلبات النظام
- نظام تشغيل: Windows 10/11 أو Ubuntu 20.04+
- Python: 3.8 - 3.11 (لا يدعم 3.12 بشكل كامل)
- RAM: 4GB كحد أدنى (8GB مفضل)
- كاميرا ويب (Webcam)

### 3.2 المتطلبات البرمجية
| المكتبة | الإصدار | الغرض |
|---------|---------|-------|
| Flask | 3.0.0 | خادم الويب |
| opencv-python | 4.8.1.78 | معالجة الفيديو والصور |
| face-recognition | 1.3.0 | التعرف على الوجوه |
| dlib | 19.24.2 | مكتبة التعرف الأساسية |
| numpy | 1.24.3 | العمليات الرياضية |
| Pillow | 10.1.0 | معالجة الصور |
| pandas | 2.0.3 | التقارير |

## 4. خطوات التنصيب بالتفصيل

### الخطوة 1: تثبيت Python
1. حمل Python من: https://python.org/downloads
2. **مهم جداً**: اختر "Add Python to PATH" أثناء التثبيت
3. تحقق من التثبيت:
   ```bash
   python --version
   pip --version
   ```

### الخطوة 2: إنشاء بيئة افتراضية (venv)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### الخطوة 3: تثبيت CMake و Build Tools (لـ dlib)
**Windows:**
1. حمل CMake من: https://cmake.org/download/
2. حمل Visual Studio Build Tools من:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/
3. اختر "Desktop development with C++"

**Ubuntu/Debian:**
```bash
sudo apt-get install cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
```

### الخطوة 4: تثبيت المكتبات
```bash
pip install --upgrade pip
pip install dlib
pip install face-recognition
pip install Flask opencv-python numpy pandas Pillow Werkzeug
```

> ملاحظة: تثبيت dlib قد يستغرق 5-10 دقائق

### الخطوة 5: تشغيل المشروع
```bash
python app.py
```
افتح المتصفح على: http://127.0.0.1:5000

## 5. دليل الاستخدام

### 5.1 تسجيل شخص جديد
1. اذهب لصفحة "تسجيل شخص"
2. أدخل الاسم والبيانات
3. ارفع صورة واضحة للوجه
4. اضغط "تسجيل"

### 5.2 تسجيل الحضور
**الطريقة الأولى - الكاميرا:**
1. اذهب لصفحة "الحضور"
2. وقف أمام الكاميرا
3. النظام يتعرف تلقائياً

**الطريقة الثانية - رفع صورة:**
1. اسحب صورة أو اختر ملف
2. اضغط "التعرف وتسجيل الحضور"

### 5.3 عرض السجلات
1. اذهب لصفحة "السجلات"
2. اختر التاريخ
3. اضغط "تصدير CSV" للتحميل

## 6. استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| `No module named 'dlib'` | أعد تثبيت CMake ثم `pip install dlib` |
| الكاميرا لا تعمل | جرب `CAMERA_INDEX = 1` في config.py |
| خطأ في face_recognition | تأكد من وجود وجه واحد فقط في الصورة |
| البطء الشديد | قلل دقة الكاميرا في config.py |

## 7. التحسينات المستقبلية
- [ ] دعم متعدد الكاميرات
- [ ] تقرير شهري تلقائي
- [ ] إشعارات البريد الإلكتروني
- [ ] تسجيل الدخول بالصلاحيات
- [ ] قاعدة بيانات MySQL
- [ ] Docker للنشر السريع
