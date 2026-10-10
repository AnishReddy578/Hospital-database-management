"""
Database Manager for Hospital Management System.
Supports both SQLite (local out-of-the-box demo) and MySQL (production RDBMS).
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospital_local.db")

class HospitalDB:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Creates tables, views, and loads seed data if database is empty."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create Schema
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name TEXT NOT NULL UNIQUE,
            building TEXT NOT NULL,
            floor INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS staff (
            staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT CHECK(role IN ('Doctor', 'Nurse', 'Admin', 'Pharmacist', 'Receptionist')) NOT NULL,
            department_id INTEGER NOT NULL,
            specialization TEXT,
            phone TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            hire_date TEXT NOT NULL,
            salary REAL NOT NULL CHECK(salary > 0),
            status TEXT CHECK(status IN ('Active', 'On Leave', 'Resigned')) DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')) NOT NULL,
            blood_group TEXT CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')) NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            address TEXT NOT NULL,
            emergency_contact_name TEXT NOT NULL,
            emergency_contact_phone TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL UNIQUE,
            room_type TEXT CHECK(room_type IN ('General', 'Semi-Private', 'Private', 'ICU')) NOT NULL,
            daily_rate REAL NOT NULL CHECK(daily_rate >= 0),
            status TEXT CHECK(status IN ('Available', 'Occupied', 'Maintenance')) DEFAULT 'Available'
        );

        CREATE TABLE IF NOT EXISTS admissions (
            admission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            attending_doctor_id INTEGER NOT NULL,
            admission_date TEXT NOT NULL,
            discharge_date TEXT,
            diagnosis_on_admission TEXT NOT NULL,
            status TEXT CHECK(status IN ('Admitted', 'Discharged')) DEFAULT 'Admitted',
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
            FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE RESTRICT,
            FOREIGN KEY (attending_doctor_id) REFERENCES staff(staff_id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT CHECK(status IN ('Scheduled', 'Completed', 'Cancelled', 'No-Show')) DEFAULT 'Scheduled',
            reason TEXT NOT NULL,
            consultation_fee REAL NOT NULL DEFAULT 500.00 CHECK(consultation_fee >= 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES staff(staff_id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS medical_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_id INTEGER,
            diagnosis TEXT NOT NULL,
            treatment_plan TEXT NOT NULL,
            prescription TEXT NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES staff(staff_id) ON DELETE RESTRICT,
            FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS bills (
            bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            appointment_id INTEGER,
            admission_id INTEGER,
            total_amount REAL NOT NULL DEFAULT 0.0 CHECK(total_amount >= 0),
            discount REAL NOT NULL DEFAULT 0.0 CHECK(discount >= 0),
            tax REAL NOT NULL DEFAULT 0.0 CHECK(tax >= 0),
            net_amount REAL NOT NULL,
            payment_status TEXT CHECK(payment_status IN ('Pending', 'Partial', 'Paid')) DEFAULT 'Pending',
            bill_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
            FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE SET NULL,
            FOREIGN KEY (admission_id) REFERENCES admissions(admission_id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            amount_paid REAL NOT NULL CHECK(amount_paid > 0),
            payment_method TEXT CHECK(payment_method IN ('Cash', 'Credit Card', 'Debit Card', 'Insurance', 'UPI')) NOT NULL,
            transaction_reference TEXT UNIQUE,
            FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_staff_dept ON staff(role, department_id);
        CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);
        CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date, status);
        CREATE INDEX IF NOT EXISTS idx_admissions_status ON admissions(status);
        CREATE INDEX IF NOT EXISTS idx_bills_status ON bills(payment_status);

        -- Views
        DROP VIEW IF EXISTS vw_patient_appointments;
        CREATE VIEW vw_patient_appointments AS
        SELECT 
            a.appointment_id,
            p.patient_id,
            (p.first_name || ' ' || p.last_name) AS patient_name,
            p.phone AS patient_phone,
            s.staff_id AS doctor_id,
            ('Dr. ' || s.first_name || ' ' || s.last_name) AS doctor_name,
            d.department_name,
            a.appointment_date,
            a.appointment_time,
            a.status AS appointment_status,
            a.reason,
            a.consultation_fee
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN staff s ON a.doctor_id = s.staff_id
        JOIN departments d ON s.department_id = d.department_id;

        DROP VIEW IF EXISTS vw_active_admissions;
        CREATE VIEW vw_active_admissions AS
        SELECT 
            adm.admission_id,
            p.patient_id,
            (p.first_name || ' ' || p.last_name) AS patient_name,
            p.blood_group,
            r.room_number,
            r.room_type,
            r.daily_rate,
            adm.admission_date,
            ('Dr. ' || s.first_name || ' ' || s.last_name) AS attending_doctor,
            adm.diagnosis_on_admission
        FROM admissions adm
        JOIN patients p ON adm.patient_id = p.patient_id
        JOIN rooms r ON adm.room_id = r.room_id
        JOIN staff s ON adm.attending_doctor_id = s.staff_id
        WHERE adm.status = 'Admitted';

        DROP VIEW IF EXISTS vw_billing_summary;
        CREATE VIEW vw_billing_summary AS
        SELECT 
            b.bill_id,
            b.patient_id,
            (p.first_name || ' ' || p.last_name) AS patient_name,
            b.bill_date,
            b.total_amount,
            b.discount,
            b.tax,
            b.net_amount,
            COALESCE(SUM(pm.amount_paid), 0.0) AS total_paid,
            (b.net_amount - COALESCE(SUM(pm.amount_paid), 0.0)) AS outstanding_balance,
            b.payment_status
        FROM bills b
        JOIN patients p ON b.patient_id = p.patient_id
        LEFT JOIN payments pm ON b.bill_id = pm.bill_id
        GROUP BY b.bill_id, b.patient_id, p.first_name, p.last_name, b.bill_date, b.total_amount, b.discount, b.tax, b.net_amount, b.payment_status;
        """)

        # Check if seed data exists
        cursor.execute("SELECT COUNT(*) FROM departments;")
        if cursor.fetchone()[0] == 0:
            self._seed_data(cursor)

        conn.commit()
        conn.close()

    def _seed_data(self, cursor):
        """Populate initial mock data."""
        cursor.executescript("""
        INSERT INTO departments (department_id, department_name, building, floor) VALUES
        (1, 'Cardiology', 'Block A', 2),
        (2, 'Neurology', 'Block A', 3),
        (3, 'Orthopedics', 'Block B', 1),
        (4, 'Pediatrics', 'Block B', 2),
        (5, 'General Medicine', 'Block C', 1);

        INSERT INTO staff (staff_id, first_name, last_name, role, department_id, specialization, phone, email, hire_date, salary, status) VALUES
        (1, 'Robert', 'Miller', 'Doctor', 1, 'Cardiologist', '+1-555-0101', 'rmiller@hospital.org', '2019-03-15', 185000.00, 'Active'),
        (2, 'Sarah', 'Jenkins', 'Doctor', 2, 'Neurologist', '+1-555-0102', 'sjenkins@hospital.org', '2020-06-01', 190000.00, 'Active'),
        (3, 'David', 'Kim', 'Doctor', 3, 'Orthopedic Surgeon', '+1-555-0103', 'dkim@hospital.org', '2018-11-20', 175000.00, 'Active'),
        (4, 'Emily', 'Chen', 'Doctor', 4, 'Pediatrician', '+1-555-0104', 'echen@hospital.org', '2021-01-10', 150000.00, 'Active'),
        (5, 'Marcus', 'Taylor', 'Doctor', 5, 'Internal Medicine', '+1-555-0105', 'mtaylor@hospital.org', '2017-08-05', 160000.00, 'Active'),
        (6, 'Jessica', 'Alvarez', 'Nurse', 1, 'Cardiac Care', '+1-555-0106', 'jalvarez@hospital.org', '2021-04-12', 72000.00, 'Active'),
        (7, 'Rachel', 'Green', 'Nurse', 4, 'Pediatric Care', '+1-555-0107', 'rgreen@hospital.org', '2022-09-01', 68000.00, 'Active'),
        (8, 'James', 'Wilson', 'Receptionist', 5, 'Front Desk', '+1-555-0108', 'jwilson@hospital.org', '2023-02-15', 45000.00, 'Active');

        INSERT INTO patients (patient_id, first_name, last_name, dob, gender, blood_group, phone, email, address, emergency_contact_name, emergency_contact_phone) VALUES
        (1, 'Alice', 'Johnson', '1985-04-12', 'Female', 'O+', '+1-555-1101', 'alice.j@email.com', '742 Evergreen Terr, Springfield', 'Mark Johnson', '+1-555-9101'),
        (2, 'Brian', 'Clark', '1972-09-28', 'Male', 'A+', '+1-555-1102', 'brian.clark@email.com', '124 Conch St, Springfield', 'Linda Clark', '+1-555-9102'),
        (3, 'Catherine', 'Davis', '1995-12-03', 'Female', 'B-', '+1-555-1103', 'cat.davis@email.com', '456 Oak Lane, Shelbyville', 'Paul Davis', '+1-555-9103'),
        (4, 'Daniel', 'Evans', '1960-07-19', 'Male', 'AB+', '+1-555-1104', 'd.evans@email.com', '89 Elm Blvd, Capital City', 'Martha Evans', '+1-555-9104'),
        (5, 'Ella', 'White', '2016-03-22', 'Female', 'O-', '+1-555-1105', 'ella.parents@email.com', '321 Maple Ave, Springfield', 'Susan White', '+1-555-9105'),
        (6, 'Frank', 'Moore', '1988-10-15', 'Male', 'A-', '+1-555-1106', 'frank.m@email.com', '654 Pine Rd, Ogdenville', 'Grace Moore', '+1-555-9106'),
        (7, 'Grace', 'Hall', '1990-05-30', 'Female', 'B+', '+1-555-1107', 'grace.hall@email.com', '15 Cedar Way, North Haverbrook', 'Tom Hall', '+1-555-9107'),
        (8, 'Henry', 'Baker', '1955-01-14', 'Male', 'O+', '+1-555-1108', 'hbaker@email.com', '78 Birch Ct, Springfield', 'Alice Baker', '+1-555-9108');

        INSERT INTO rooms (room_id, room_number, room_type, daily_rate, status) VALUES
        (101, 'R-101', 'General', 150.00, 'Available'),
        (102, 'R-102', 'General', 150.00, 'Occupied'),
        (201, 'R-201', 'Semi-Private', 300.00, 'Available'),
        (202, 'R-202', 'Semi-Private', 300.00, 'Occupied'),
        (301, 'R-301', 'Private', 600.00, 'Occupied'),
        (401, 'ICU-1', 'ICU', 1500.00, 'Available');

        INSERT INTO admissions (admission_id, patient_id, room_id, attending_doctor_id, admission_date, discharge_date, diagnosis_on_admission, status) VALUES
        (1, 2, 102, 1, '2025-04-01 10:30:00', '2025-04-05 14:00:00', 'Mild Myocardial Infarction', 'Discharged'),
        (2, 4, 301, 3, '2025-04-06 08:15:00', NULL, 'Fractured Femur Post-Surgery', 'Admitted'),
        (3, 8, 202, 2, '2025-04-08 16:45:00', NULL, 'Ischemic Stroke Monitoring', 'Admitted');

        INSERT INTO appointments (appointment_id, patient_id, doctor_id, appointment_date, appointment_time, status, reason, consultation_fee) VALUES
        (1, 1, 1, '2025-04-10', '09:00', 'Completed', 'Routine Cardiac Checkup', 500.00),
        (2, 3, 3, '2025-04-10', '10:30', 'Completed', 'Knee Joint Pain Consultation', 450.00),
        (3, 5, 4, '2025-04-10', '11:15', 'Completed', 'Pediatric Vaccination & Wellness', 350.00),
        (4, 6, 5, '2025-04-11', '09:30', 'Scheduled', 'Persistent Fever & Fatigue', 400.00),
        (5, 7, 2, '2025-04-11', '14:00', 'Scheduled', 'Chronic Migraine Assessment', 550.00),
        (6, 1, 1, '2025-04-15', '11:00', 'Scheduled', 'Follow-up ECG Review', 500.00),
        (7, 3, 5, '2025-04-08', '15:30', 'Cancelled', 'General Health Screening', 400.00);

        INSERT INTO medical_records (record_id, patient_id, doctor_id, appointment_id, diagnosis, treatment_plan, prescription, recorded_at) VALUES
        (1, 1, 1, 1, 'Mild Hypertension (Stage 1)', 'Low sodium diet, moderate cardio 30m daily', 'Amlodipine 5mg OD x 30 days', '2025-04-10 09:35:00'),
        (2, 3, 3, 2, 'Patellofemoral Pain Syndrome', 'Quadriceps strengthening exercises, avoid stairs', 'Ibuprofen 400mg PRN, Glucosamine', '2025-04-10 11:00:00'),
        (3, 5, 4, 3, 'Normal Pediatric Growth & MMR Booster', 'Next vaccination due in 12 months', 'Paracetamol oral drops PRN for fever', '2025-04-10 11:45:00'),
        (4, 2, 1, NULL, 'Coronary Artery Disease', 'Stent placement completed, cardiac rehab', 'Aspirin 75mg, Atorvastatin 40mg', '2025-04-05 13:00:00');

        INSERT INTO bills (bill_id, patient_id, appointment_id, admission_id, total_amount, discount, tax, net_amount, payment_status, bill_date) VALUES
        (1, 1, 1, NULL, 500.00, 50.00, 22.50, 472.50, 'Paid', '2025-04-10 09:40:00'),
        (2, 3, 2, NULL, 450.00, 0.00, 22.50, 472.50, 'Paid', '2025-04-10 11:05:00'),
        (3, 5, 3, NULL, 350.00, 0.00, 17.50, 367.50, 'Pending', '2025-04-10 11:50:00'),
        (4, 2, NULL, 1, 3200.00, 200.00, 150.00, 3150.00, 'Paid', '2025-04-05 14:30:00'),
        (5, 4, NULL, 2, 4500.00, 300.00, 210.00, 4410.00, 'Partial', '2025-04-09 10:00:00');

        INSERT INTO payments (payment_id, bill_id, payment_date, amount_paid, payment_method, transaction_reference) VALUES
        (1, 1, '2025-04-10 09:45:00', 472.50, 'UPI', 'UPI-TXN-984210'),
        (2, 2, '2025-04-10 11:10:00', 472.50, 'Credit Card', 'CC-AUTH-773124'),
        (3, 4, '2025-04-05 14:35:00', 3150.00, 'Insurance', 'INS-CLAIM-554109'),
        (4, 5, '2025-04-09 10:15:00', 2000.00, 'Debit Card', 'DC-AUTH-119832');
        """)

    # Query methods
    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def execute(self, sql: str, params: tuple = ()) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    # Business operations
    def add_patient(self, first_name: str, last_name: str, dob: str, gender: str,
                    blood_group: str, phone: str, email: str, address: str,
                    emergency_name: str, emergency_phone: str) -> int:
        sql = """
        INSERT INTO patients (first_name, last_name, dob, gender, blood_group, phone, email, address, emergency_contact_name, emergency_contact_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute(sql, (first_name, last_name, dob, gender, blood_group, phone, email, address, emergency_name, emergency_phone))

    def book_appointment(self, patient_id: int, doctor_id: int, date: str, time: str, reason: str, fee: float = 500.0) -> int:
        sql = """
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, consultation_fee)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute(sql, (patient_id, doctor_id, date, time, reason, fee))

    def admit_patient(self, patient_id: int, room_id: int, doctor_id: int, admission_date: str, diagnosis: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO admissions (patient_id, room_id, attending_doctor_id, admission_date, diagnosis_on_admission, status)
            VALUES (?, ?, ?, ?, ?, 'Admitted')
        """, (patient_id, room_id, doctor_id, admission_date, diagnosis))
        admission_id = cursor.lastrowid
        cursor.execute("UPDATE rooms SET status = 'Occupied' WHERE room_id = ?", (room_id,))
        conn.commit()
        conn.close()
        return admission_id

    def discharge_patient(self, admission_id: int, discharge_date: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT room_id FROM admissions WHERE admission_id = ?", (admission_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        room_id = row['room_id']
        cursor.execute("UPDATE admissions SET status = 'Discharged', discharge_date = ? WHERE admission_id = ?", (discharge_date, admission_id))
        cursor.execute("UPDATE rooms SET status = 'Available' WHERE room_id = ?", (room_id,))
        conn.commit()
        conn.close()
        return True

    def create_bill(self, patient_id: int, total_amount: float, discount: float = 0.0, tax: float = 0.0, appointment_id: Optional[int] = None, admission_id: Optional[int] = None) -> int:
        net_amount = total_amount - discount + tax
        sql = """
        INSERT INTO bills (patient_id, appointment_id, admission_id, total_amount, discount, tax, net_amount, payment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
        """
        return self.execute(sql, (patient_id, appointment_id, admission_id, total_amount, discount, tax, net_amount))

    def record_payment(self, bill_id: int, amount: float, method: str, ref: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO payments (bill_id, amount_paid, payment_method, transaction_reference)
            VALUES (?, ?, ?, ?)
        """, (bill_id, amount, method, ref))
        payment_id = cursor.lastrowid

        # Update bill status
        cursor.execute("SELECT net_amount FROM bills WHERE bill_id = ?", (bill_id,))
        bill = cursor.fetchone()
        if bill:
            net = bill['net_amount']
            cursor.execute("SELECT SUM(amount_paid) as total_paid FROM payments WHERE bill_id = ?", (bill_id,))
            total_paid = cursor.fetchone()['total_paid'] or 0.0
            if total_paid >= net:
                status = 'Paid'
            elif total_paid > 0:
                status = 'Partial'
            else:
                status = 'Pending'
            cursor.execute("UPDATE bills SET payment_status = ? WHERE bill_id = ?", (status, bill_id))

        conn.commit()
        conn.close()
        return payment_id

    def get_dashboard_stats(self) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM patients")
        total_patients = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM staff WHERE role = 'Doctor'")
        total_doctors = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Scheduled'")
        active_appointments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM admissions WHERE status = 'Admitted'")
        current_admissions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) FROM rooms")
        total_rooms, occupied_rooms = cursor.fetchone()
        occupancy_rate = round((occupied_rooms / total_rooms * 100), 1) if total_rooms else 0.0

        cursor.execute("SELECT COALESCE(SUM(amount_paid), 0.0) FROM payments")
        total_revenue = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(net_amount), 0.0) FROM bills WHERE payment_status != 'Paid'")
        pending_bills_amount = cursor.fetchone()[0]

        conn.close()
        return {
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "active_appointments": active_appointments,
            "current_admissions": current_admissions,
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_rooms,
            "occupancy_rate": occupancy_rate,
            "total_revenue": total_revenue,
            "pending_bills_amount": pending_bills_amount
        }
