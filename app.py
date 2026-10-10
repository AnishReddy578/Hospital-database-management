"""
Hospital Management System - Interactive CLI
Author: Database Management Project
RDBMS: MySQL & SQLite
"""

import sys
from db_manager import HospitalDB

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)

def print_table(rows, headers):
    if not rows:
        print("  No records found.")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            widths[idx] = max(widths[idx], len(str(val) if val is not None else ""))

    header_line = " | ".join(f"{h:<{widths[i]}}" for i, h in enumerate(headers))
    separator = "-+-".join("-" * widths[i] for i in range(len(headers)))

    print(" " + header_line)
    print(" " + separator)
    for row in rows:
        line = " | ".join(f"{str(val if val is not None else ''):<{widths[i]}}" for i, val in enumerate(row))
        print(" " + line)

def show_dashboard(db: HospitalDB):
    stats = db.get_dashboard_stats()
    print_header("Hospital Operations Overview")
    print(f"  * Registered Patients   : {stats['total_patients']}")
    print(f"  * Active Medical Staff  : {stats['total_doctors']} Doctors")
    print(f"  * Scheduled Appointments: {stats['active_appointments']}")
    print(f"  * Admitted In-Patients  : {stats['current_admissions']}")
    print(f"  * Bed Occupancy Rate    : {stats['occupancy_rate']}% ({stats['occupied_rooms']}/{stats['total_rooms']} Beds)")
    print(f"  * Total Revenue Paid    : ${stats['total_revenue']:,.2f}")
    print(f"  * Outstanding Bills     : ${stats['pending_bills_amount']:,.2f}")

def list_patients(db: HospitalDB):
    print_header("Patient Directory")
    rows = db.query("SELECT patient_id, (first_name || ' ' || last_name) AS name, dob, gender, blood_group, phone, emergency_contact_name FROM patients ORDER BY patient_id")
    data = [[r['patient_id'], r['name'], r['dob'], r['gender'], r['blood_group'], r['phone'], r['emergency_contact_name']] for r in rows]
    print_table(data, ["ID", "Patient Name", "DOB", "Gender", "Blood", "Phone", "Emergency Contact"])

def register_patient(db: HospitalDB):
    print_header("Register New Patient")
    try:
        first = input("  First Name: ").strip()
        last = input("  Last Name: ").strip()
        dob = input("  Date of Birth (YYYY-MM-DD): ").strip()
        gender = input("  Gender (Male/Female/Other): ").strip()
        blood = input("  Blood Group (e.g. O+, A+, B-): ").strip()
        phone = input("  Phone Number: ").strip()
        email = input("  Email (optional): ").strip()
        addr = input("  Address: ").strip()
        em_name = input("  Emergency Contact Name: ").strip()
        em_phone = input("  Emergency Contact Phone: ").strip()

        if not first or not last or not phone:
            print("  [!] Error: First name, last name, and phone are required.")
            return

        pid = db.add_patient(first, last, dob, gender, blood, phone, email, addr, em_name, em_phone)
        print(f"\n  [✓] Patient registered successfully with Patient ID: {pid}")
    except Exception as e:
        print(f"  [!] Failed to register patient: {e}")

def list_doctors(db: HospitalDB):
    print_header("Medical Staff & Doctors")
    sql = """
    SELECT s.staff_id, ('Dr. ' || s.first_name || ' ' || s.last_name) AS name,
           s.specialization, d.department_name, s.phone, s.email, s.status
    FROM staff s
    JOIN departments d ON s.department_id = d.department_id
    WHERE s.role = 'Doctor'
    """
    rows = db.query(sql)
    data = [[r['staff_id'], r['name'], r['specialization'], r['department_name'], r['phone'], r['email'], r['status']] for r in rows]
    print_table(data, ["ID", "Doctor Name", "Specialization", "Department", "Phone", "Email", "Status"])

def list_appointments(db: HospitalDB):
    print_header("Appointments Schedule")
    rows = db.query("SELECT * FROM vw_patient_appointments ORDER BY appointment_date, appointment_time")
    data = [[r['appointment_id'], r['patient_name'], r['doctor_name'], r['department_name'], r['appointment_date'], r['appointment_time'], r['appointment_status'], r['reason']] for r in rows]
    print_table(data, ["Appt ID", "Patient", "Doctor", "Department", "Date", "Time", "Status", "Reason"])

def book_appointment(db: HospitalDB):
    print_header("Book New Appointment")
    try:
        pid = int(input("  Patient ID: ").strip())
        doc_id = int(input("  Doctor ID: ").strip())
        date = input("  Appointment Date (YYYY-MM-DD): ").strip()
        time = input("  Appointment Time (HH:MM): ").strip()
        reason = input("  Reason / Symptoms: ").strip()
        fee_in = input("  Consultation Fee (Default 500.00): ").strip()
        fee = float(fee_in) if fee_in else 500.00

        aid = db.book_appointment(pid, doc_id, date, time, reason, fee)
        print(f"\n  [✓] Appointment booked successfully with Appointment ID: {aid}")
    except Exception as e:
        print(f"  [!] Failed to book appointment: {e}")

def list_rooms_and_admissions(db: HospitalDB):
    print_header("Wards & Room Occupancy")
    rooms = db.query("SELECT room_id, room_number, room_type, daily_rate, status FROM rooms ORDER BY room_id")
    rdata = [[r['room_id'], r['room_number'], r['room_type'], f"${r['daily_rate']:.2f}", r['status']] for r in rooms]
    print_table(rdata, ["Room ID", "Room #", "Type", "Daily Rate", "Status"])

    print("\n  CURRENTLY ADMITTED PATIENTS:")
    adms = db.query("SELECT * FROM vw_active_admissions")
    adata = [[a['admission_id'], a['patient_name'], a['blood_group'], a['room_number'], a['room_type'], a['admission_date'], a['attending_doctor'], a['diagnosis_on_admission']] for a in adms]
    print_table(adata, ["Adm ID", "Patient", "Blood", "Room", "Type", "Admission Date", "Doctor", "Diagnosis"])

def list_billing(db: HospitalDB):
    print_header("Billing & Payments Summary")
    rows = db.query("SELECT * FROM vw_billing_summary ORDER BY bill_id")
    data = [[r['bill_id'], r['patient_name'], f"${r['total_amount']:.2f}", f"${r['discount']:.2f}", f"${r['tax']:.2f}", f"${r['net_amount']:.2f}", f"${r['total_paid']:.2f}", f"${r['outstanding_balance']:.2f}", r['payment_status']] for r in rows]
    print_table(data, ["Bill ID", "Patient", "Total", "Discount", "Tax", "Net Amount", "Paid", "Balance", "Status"])

def record_payment_cli(db: HospitalDB):
    print_header("Record Bill Payment")
    try:
        bill_id = int(input("  Bill ID: ").strip())
        amount = float(input("  Amount to Pay: ").strip())
        print("  Payment Methods: Cash, Credit Card, Debit Card, Insurance, UPI")
        method = input("  Method: ").strip()
        ref = input("  Transaction Ref (optional): ").strip() or f"TXN-{bill_id}-{int(amount)}"

        pay_id = db.record_payment(bill_id, amount, method, ref)
        print(f"\n  [✓] Payment recorded! Payment ID: {pay_id}")
    except Exception as e:
        print(f"  [!] Payment processing error: {e}")

def run_analytical_reports(db: HospitalDB):
    print_header("Hospital Operational & Financial Analytics")
    print("  1. Department Revenue & Consultation Performance")
    print("  2. Doctor Workload & Completed Consultations")
    print("  3. Room & Ward Utilization Rate")
    print("  4. Outstanding Balances / Overdue Bills")

    choice = input("\n  Select report (1-4): ").strip()
    if choice == "1":
        sql = """
        SELECT d.department_name,
               COUNT(DISTINCT a.appointment_id) AS consultations,
               COALESCE(SUM(b.net_amount), 0.0) AS billed,
               COALESCE(SUM(p.amount_paid), 0.0) AS collected
        FROM departments d
        JOIN staff s ON d.department_id = s.department_id
        LEFT JOIN appointments a ON s.staff_id = a.doctor_id
        LEFT JOIN bills b ON a.appointment_id = b.appointment_id
        LEFT JOIN payments p ON b.bill_id = p.bill_id
        GROUP BY d.department_id, d.department_name
        ORDER BY collected DESC
        """
        rows = db.query(sql)
        data = [[r['department_name'], r['consultations'], f"${r['billed']:.2f}", f"${r['collected']:.2f}"] for r in rows]
        print_table(data, ["Department", "Consultations", "Total Billed", "Total Collected"])

    elif choice == "2":
        sql = """
        SELECT ('Dr. ' || s.first_name || ' ' || s.last_name) AS doctor_name,
               d.department_name,
               COUNT(a.appointment_id) AS total_appts,
               SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
               COALESCE(SUM(a.consultation_fee), 0.0) AS revenue
        FROM staff s
        JOIN departments d ON s.department_id = d.department_id
        JOIN appointments a ON s.staff_id = a.doctor_id
        GROUP BY s.staff_id
        ORDER BY total_appts DESC
        """
        rows = db.query(sql)
        data = [[r['doctor_name'], r['department_name'], r['total_appts'], r['completed'], f"${r['revenue']:.2f}"] for r in rows]
        print_table(data, ["Doctor", "Department", "Appointments", "Completed", "Revenue"])

    elif choice == "3":
        sql = """
        SELECT room_type,
               COUNT(room_id) AS total_rooms,
               SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) AS occupied,
               SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) AS available,
               ROUND((SUM(CASE WHEN status = 'Occupied' THEN 1.0 ELSE 0.0 END) / COUNT(room_id)) * 100, 1) || '%' AS occupancy_rate
        FROM rooms
        GROUP BY room_type
        """
        rows = db.query(sql)
        data = [[r['room_type'], r['total_rooms'], r['occupied'], r['available'], r['occupancy_rate']] for r in rows]
        print_table(data, ["Room Type", "Total", "Occupied", "Available", "Occupancy %"])

    elif choice == "4":
        sql = """
        SELECT b.bill_id, (p.first_name || ' ' || p.last_name) AS patient_name,
               p.phone, b.net_amount, COALESCE(SUM(pm.amount_paid), 0.0) AS paid,
               (b.net_amount - COALESCE(SUM(pm.amount_paid), 0.0)) AS balance,
               b.payment_status
        FROM bills b
        JOIN patients p ON b.patient_id = p.patient_id
        LEFT JOIN payments pm ON b.bill_id = pm.bill_id
        WHERE b.payment_status != 'Paid'
        GROUP BY b.bill_id
        """
        rows = db.query(sql)
        data = [[r['bill_id'], r['patient_name'], r['phone'], f"${r['net_amount']:.2f}", f"${r['paid']:.2f}", f"${r['balance']:.2f}", r['payment_status']] for r in rows]
        print_table(data, ["Bill ID", "Patient", "Phone", "Net Amount", "Paid", "Balance Due", "Status"])

def execute_raw_sql(db: HospitalDB):
    print_header("Run Custom SQL Query")
    print("  Type your SQL query below (or 'exit' to return):")
    query_str = input("  SQL> ").strip()
    if not query_str or query_str.lower() == 'exit':
        return
    try:
        rows = db.query(query_str)
        if not rows:
            print("  Query executed. No rows returned (or affected rows committed).")
        else:
            headers = list(rows[0].keys())
            data = [[r[h] for h in headers] for r in rows]
            print_table(data, headers)
    except Exception as e:
        print(f"  [!] SQL Execution Error: {e}")

def main():
    db = HospitalDB()
    while True:
        print("\n" + "=" * 70)
        print("   HOSPITAL MANAGEMENT SYSTEM - RDBMS PROJECT")
        print("=" * 70)
        print("  1. Dashboard & Operational KPI Summary")
        print("  2. View Patient Directory")
        print("  3. Register New Patient")
        print("  4. View Doctors & Staff")
        print("  5. View Appointments Schedule")
        print("  6. Book New Appointment")
        print("  7. View Rooms & Admitted Patients")
        print("  8. View Billing & Financial Summary")
        print("  9. Record Bill Payment")
        print(" 10. Operational & Financial Analytics Reports")
        print(" 11. Run Custom SQL Query")
        print("  0. Exit")
        print("-" * 70)

        choice = input("  Select an option [0-11]: ").strip()
        if choice == "1":
            show_dashboard(db)
        elif choice == "2":
            list_patients(db)
        elif choice == "3":
            register_patient(db)
        elif choice == "4":
            list_doctors(db)
        elif choice == "5":
            list_appointments(db)
        elif choice == "6":
            book_appointment(db)
        elif choice == "7":
            list_rooms_and_admissions(db)
        elif choice == "8":
            list_billing(db)
        elif choice == "9":
            record_payment_cli(db)
        elif choice == "10":
            run_analytical_reports(db)
        elif choice == "11":
            execute_raw_sql(db)
        elif choice == "0":
            print("\n  Exiting Hospital Management System. Goodbye!\n")
            break
        else:
            print("  Invalid selection. Please choose an option from 0 to 11.")

if __name__ == "__main__":
    main()
