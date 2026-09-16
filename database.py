import sqlite3
import os
from datetime import datetime
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """إنشاء الجداول إذا لم تكن موجودة"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # جدول الأشخاص
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                role TEXT DEFAULT 'student',
                face_encoding_path TEXT,
                photo_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول سجلات الحضور
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time_in TEXT,
                time_out TEXT,
                status TEXT DEFAULT 'present',
                method TEXT DEFAULT 'face_recognition',
                FOREIGN KEY (person_id) REFERENCES persons(id)
            )
        """)

        conn.commit()
        conn.close()

    # === إدارة الأشخاص ===

    def add_person(self, name, email=None, phone=None, role="student", 
                   face_encoding_path=None, photo_path=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO persons (name, email, phone, role, face_encoding_path, photo_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, email, phone, role, face_encoding_path, photo_path))
            conn.commit()
            person_id = cursor.lastrowid
            conn.close()
            return person_id
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def get_all_persons(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM persons ORDER BY name")
        persons = cursor.fetchall()
        conn.close()
        return [dict(row) for row in persons]

    def get_person_by_id(self, person_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM persons WHERE id = ?", (person_id,))
        person = cursor.fetchone()
        conn.close()
        return dict(person) if person else None

    def delete_person(self, person_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM persons WHERE id = ?", (person_id,))
        cursor.execute("DELETE FROM attendance WHERE person_id = ?", (person_id,))
        conn.commit()
        conn.close()

    # === إدارة الحضور ===

    def mark_attendance(self, person_id, method="face_recognition"):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # الحصول على تاريخ ووقت اليوم
        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")    # YYYY-MM-DD
        current_time = now.strftime("%H:%M:%S")  # HH:MM:SS
        
        # 1. التحقق هل الشخص محضر اليوم مسبقاً؟
        cursor.execute(
            "SELECT id FROM attendance WHERE person_id = ? AND date = ?", 
            (person_id, today_date)
        )
        already_marked = cursor.fetchone()
        
        if already_marked:
            conn.close()
            return False  # محضر مسبقاً اليوم، لن يتم إدخال سجل جديد

        # 2. إدخال سجل الحضور الجديد
        cursor.execute(
            """
            INSERT INTO attendance (person_id, date, time_in, status, method)
            VALUES (?, ?, ?, 'present', ?)
            """, 
            (person_id, today_date, current_time, method)
        )
        conn.commit()
        conn.close()
        return True

    # def mark_attendance(self, person_id, status="present", method="face_recognition"):
    #     """تسجيل حضور أو مغادرة"""
    #     conn = self.get_connection()
    #     cursor = conn.cursor()

    #     today = datetime.now().strftime("%Y-%m-%d")
    #     now_time = datetime.now().strftime("%H:%M:%S")

    #     # التحقق من وجود سجل اليوم
    #     cursor.execute("""
    #         SELECT * FROM attendance 
    #         WHERE person_id = ? AND date = ?
    #     """, (person_id, today))

    #     record = cursor.fetchone()

    #     if record is None:
    #         # تسجيل دخول جديد
    #         cursor.execute("""
    #             INSERT INTO attendance (person_id, date, time_in, status, method)
    #             VALUES (?, ?, ?, ?, ?)
    #         """, (person_id, today, now_time, status, method))
    #     else:
    #         # تحديث وقت الخروج
    #         cursor.execute("""
    #             UPDATE attendance 
    #             SET time_out = ?
    #             WHERE person_id = ? AND date = ?
    #         """, (now_time, person_id, today))

    #     conn.commit()
    #     conn.close()
    #     return True

    def get_attendance_logs(self, date=None, person_id=None):
        """جلب سجلات الحضور"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT a.*, p.name, p.photo_path 
            FROM attendance a
            JOIN persons p ON a.person_id = p.id
            WHERE 1=1
        """
        params = []

        if date:
            query += " AND a.date = ?"
            params.append(date)

        if person_id:
            query += " AND a.person_id = ?"
            params.append(person_id)

        query += " ORDER BY a.date DESC, a.time_in DESC"

        cursor.execute(query, params)
        logs = cursor.fetchall()
        conn.close()
        return [dict(row) for row in logs]

    def get_today_stats(self):
        """إحصائيات اليوم"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT COUNT(*) as total_present 
            FROM attendance 
            WHERE date = ? AND time_in IS NOT NULL
        """, (today,))

        present = cursor.fetchone()["total_present"]

        cursor.execute("SELECT COUNT(*) as total FROM persons")
        total_persons = cursor.fetchone()["total"]

        conn.close()
        return {
            "present": present,
            "total": total_persons,
            "absent": total_persons - present
        }

    def get_monthly_report(self, year, month):
        """تقرير شهري"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.name, 
                   COUNT(a.id) as days_present,
                   GROUP_CONCAT(DISTINCT a.date) as dates
            FROM persons p
            LEFT JOIN attendance a ON p.id = a.person_id 
                AND strftime('%Y-%m', a.date) = ?
            GROUP BY p.id
        """, (f"{year:04d}-{month:02d}",))

        report = cursor.fetchall()
        conn.close()
        return [dict(row) for row in report]

# كائن عام لقاعدة البيانات
db = Database()
