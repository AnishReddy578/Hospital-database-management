"""
MedPulse Hospital Management System - Web Dashboard
Zero-dependency HTTP Server using Python standard library.
Run: python web_app.py
Access: http://localhost:8000
"""

import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from db_manager import HospitalDB

INDEX_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MedPulse Hospital Management System</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #0284c7;
            --primary-hover: #0369a1;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --success: #16a34a;
            --warning: #d97706;
            --danger: #dc2626;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text-main); line-height: 1.5; }
        .header { background: #0f172a; color: white; padding: 1.25rem 2rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header h1 { font-size: 1.35rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem; }
        .header .badge { background: #38bdf8; color: #082f49; font-size: 0.75rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 9999px; }
        .header .rdbms { font-size: 0.85rem; color: #94a3b8; }
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem; }

        /* Stats Grid */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }
        .stat-card { background: var(--card-bg); padding: 1.25rem; border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .stat-card .label { font-size: 0.825rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.03em; }
        .stat-card .value { font-size: 1.75rem; font-weight: 700; color: var(--text-main); margin-top: 0.35rem; }
        .stat-card .subtext { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }

        /* Navigation Tabs */
        .nav-tabs { display: flex; gap: 0.5rem; border-bottom: 2px solid var(--border); margin-bottom: 1.5rem; overflow-x: auto; }
        .tab-btn { background: none; border: none; padding: 0.75rem 1.25rem; font-size: 0.95rem; font-weight: 600; color: var(--text-muted); cursor: pointer; border-bottom: 3px solid transparent; margin-bottom: -2px; transition: all 0.2s; white-space: nowrap; }
        .tab-btn:hover { color: var(--primary); }
        .tab-btn.active { color: var(--primary); border-bottom-color: var(--primary); }

        /* Tab Content */
        .tab-pane { display: none; }
        .tab-pane.active { display: block; }

        /* Table Card */
        .card { background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 1.5rem; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }
        .card-title { font-size: 1.15rem; font-weight: 700; }
        .table-responsive { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }
        th { background: #f1f5f9; padding: 0.75rem 1rem; font-weight: 600; color: #475569; border-bottom: 1px solid var(--border); }
        td { padding: 0.85rem 1rem; border-bottom: 1px solid var(--border); }
        tr:hover td { background: #f8fafc; }

        /* Badges */
        .status-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
        .status-Scheduled, .status-Pending, .status-Partial { background: #fef3c7; color: #b45309; }
        .status-Completed, .status-Paid, .status-Available { background: #dcfce7; color: #15803d; }
        .status-Cancelled, .status-Occupied { background: #fee2e2; color: #b91c1c; }
        .status-Admitted { background: #e0e7ff; color: #4338ca; }

        /* Forms & Inputs */
        .btn { background: var(--primary); color: white; border: none; padding: 0.55rem 1rem; border-radius: 6px; font-size: 0.875rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        .btn:hover { background: var(--primary-hover); }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem; }
        .form-group label { display: block; font-size: 0.8rem; font-weight: 600; color: var(--text-muted); margin-bottom: 0.35rem; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 0.55rem 0.75rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; font-family: inherit; }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus { outline: none; border-color: var(--primary); }

        /* SQL Console */
        .sql-box { width: 100%; height: 100px; font-family: monospace; font-size: 0.9rem; padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; margin-bottom: 0.75rem; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1><span>🏥</span> MedPulse Hospital Management System <span class="badge">MySQL Relational DB</span></h1>
            <div class="rdbms">Database Management Project for Hospital Operations & Administration</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.85rem; font-weight: 600;">System Online</div>
            <div style="font-size: 0.75rem; color: #38bdf8;">Port: 8000 | Active Engine: RDBMS</div>
        </div>
    </div>

    <div class="container">
        <!-- KPI Metrics -->
        <div class="stats-grid" id="statsContainer">
            <!-- Loaded dynamically via JS -->
        </div>

        <!-- Navigation -->
        <div class="nav-tabs">
            <button class="tab-btn active" onclick="switchTab('patients')">Patients Directory</button>
            <button class="tab-btn" onclick="switchTab('appointments')">Appointments</button>
            <button class="tab-btn" onclick="switchTab('doctors')">Doctors & Staff</button>
            <button class="tab-btn" onclick="switchTab('rooms')">Rooms & Wards</button>
            <button class="tab-btn" onclick="switchTab('billing')">Billing & Invoices</button>
            <button class="tab-btn" onclick="switchTab('analytics')">Operational Reports</button>
            <button class="tab-btn" onclick="switchTab('sql')">SQL Console</button>
        </div>

        <!-- TAB: PATIENTS -->
        <div id="tab-patients" class="tab-pane active">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Registered Patients Directory</h2>
                    <button class="btn" onclick="toggleForm('newPatientForm')">+ Register New Patient</button>
                </div>
                
                <div id="newPatientForm" style="display: none; background: #f8fafc; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; border: 1px dashed var(--border);">
                    <h3 style="font-size: 1rem; margin-bottom: 0.75rem;">New Patient Admission Form</h3>
                    <form onsubmit="submitPatient(event)">
                        <div class="form-grid">
                            <div class="form-group"><label>First Name</label><input type="text" id="p_first" required></div>
                            <div class="form-group"><label>Last Name</label><input type="text" id="p_last" required></div>
                            <div class="form-group"><label>Date of Birth</label><input type="date" id="p_dob" required></div>
                            <div class="form-group"><label>Gender</label><select id="p_gender"><option>Male</option><option>Female</option><option>Other</option></select></div>
                            <div class="form-group"><label>Blood Group</label><select id="p_blood"><option>O+</option><option>A+</option><option>B+</option><option>AB+</option><option>O-</option><option>A-</option><option>B-</option><option>AB-</option></select></div>
                            <div class="form-group"><label>Phone</label><input type="tel" id="p_phone" required></div>
                            <div class="form-group"><label>Address</label><input type="text" id="p_address" required></div>
                            <div class="form-group"><label>Emergency Contact</label><input type="text" id="p_em_name" required></div>
                            <div class="form-group"><label>Emergency Phone</label><input type="tel" id="p_em_phone" required></div>
                        </div>
                        <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                            <button type="submit" class="btn">Save Patient</button>
                            <button type="button" class="btn" style="background:#64748b;" onclick="toggleForm('newPatientForm')">Cancel</button>
                        </div>
                    </form>
                </div>

                <div class="table-responsive">
                    <table id="patientsTable">
                        <thead>
                            <tr><th>ID</th><th>Name</th><th>DOB</th><th>Gender</th><th>Blood</th><th>Phone</th><th>Emergency Contact</th></tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB: APPOINTMENTS -->
        <div id="tab-appointments" class="tab-pane">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Appointments & Outpatient Clinic</h2>
                    <button class="btn" onclick="toggleForm('newApptForm')">+ Book Appointment</button>
                </div>

                <div id="newApptForm" style="display: none; background: #f8fafc; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; border: 1px dashed var(--border);">
                    <h3 style="font-size: 1rem; margin-bottom: 0.75rem;">Schedule Consultation</h3>
                    <form onsubmit="submitAppointment(event)">
                        <div class="form-grid">
                            <div class="form-group"><label>Patient ID</label><input type="number" id="a_pid" required></div>
                            <div class="form-group"><label>Doctor ID</label><input type="number" id="a_docid" required></div>
                            <div class="form-group"><label>Date</label><input type="date" id="a_date" required></div>
                            <div class="form-group"><label>Time</label><input type="time" id="a_time" required></div>
                            <div class="form-group"><label>Reason</label><input type="text" id="a_reason" required></div>
                            <div class="form-group"><label>Fee ($)</label><input type="number" id="a_fee" value="500"></div>
                        </div>
                        <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                            <button type="submit" class="btn">Confirm Appointment</button>
                            <button type="button" class="btn" style="background:#64748b;" onclick="toggleForm('newApptForm')">Cancel</button>
                        </div>
                    </form>
                </div>

                <div class="table-responsive">
                    <table id="appointmentsTable">
                        <thead>
                            <tr><th>Appt ID</th><th>Patient</th><th>Doctor</th><th>Department</th><th>Date</th><th>Time</th><th>Status</th><th>Reason</th></tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB: DOCTORS -->
        <div id="tab-doctors" class="tab-pane">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Doctors & Medical Specialists</h2>
                </div>
                <div class="table-responsive">
                    <table id="doctorsTable">
                        <thead>
                            <tr><th>ID</th><th>Doctor Name</th><th>Specialization</th><th>Department</th><th>Phone</th><th>Email</th><th>Status</th></tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB: ROOMS & WARDS -->
        <div id="tab-rooms" class="tab-pane">
            <div class="card">
                <div class="card-header"><h2 class="card-title">Hospital Bed & Room Inventory</h2></div>
                <div class="table-responsive">
                    <table id="roomsTable">
                        <thead>
                            <tr><th>Room ID</th><th>Room Number</th><th>Room Type</th><th>Daily Rate</th><th>Status</th></tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header"><h2 class="card-title">Currently Admitted In-Patients</h2></div>
                <div class="table-responsive">
                    <table id="admissionsTable">
                        <thead>
                            <tr><th>Admission ID</th><th>Patient</th><th>Blood</th><th>Room #</th><th>Type</th><th>Admission Date</th><th>Attending Doctor</th><th>Diagnosis</th></tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB: BILLING -->
        <div id="tab-billing" class="tab-pane">
            <div class="card">
                <div class="card-header"><h2 class="card-title">Invoices & Billing Summary</h2></div>
                <div class="table-responsive">
                    <table id="billingTable">
                        <thead>
                            <tr><th>Bill ID</th><th>Patient</th><th>Total</th><th>Discount</th><th>Tax</th><th>Net Amount</th><th>Paid</th><th>Balance</th><th>Status</th></tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB: ANALYTICS -->
        <div id="tab-analytics" class="tab-pane">
            <div class="card">
                <div class="card-header"><h2 class="card-title">Department Revenue Performance</h2></div>
                <div class="table-responsive">
                    <table id="deptPerfTable">
                        <thead>
                            <tr><th>Department</th><th>Consultations</th><th>Total Billed</th><th>Total Collected</th></tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header"><h2 class="card-title">Doctor Consultation Workload</h2></div>
                <div class="table-responsive">
                    <table id="doctorWorkloadTable">
                        <thead>
                            <tr><th>Doctor</th><th>Department</th><th>Total Appointments</th><th>Completed</th><th>Consultation Revenue</th></tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB: SQL CONSOLE -->
        <div id="tab-sql" class="tab-pane">
            <div class="card">
                <div class="card-header"><h2 class="card-title">Live SQL Query Console</h2></div>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.75rem;">
                    Execute relational queries directly against the database tables: <code>departments</code>, <code>staff</code>, <code>patients</code>, <code>appointments</code>, <code>rooms</code>, <code>admissions</code>, <code>bills</code>, <code>payments</code>.
                </p>
                <textarea id="sqlQueryInput" class="sql-box" spellcheck="false">SELECT department_name, building, floor FROM departments;</textarea>
                <button class="btn" onclick="runSql()">Run Query</button>

                <div style="margin-top: 1.5rem;" class="table-responsive">
                    <table id="sqlResultsTable">
                        <thead></thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        function switchTab(name) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + name).classList.add('active');
        }

        function toggleForm(id) {
            const el = document.getElementById(id);
            el.style.display = el.style.display === 'none' ? 'block' : 'none';
        }

        async function loadData() {
            try {
                const res = await fetch('/api/data');
                const data = await res.json();

                // 1. Stats
                const s = data.stats;
                document.getElementById('statsContainer').innerHTML = `
                    <div class="stat-card">
                        <div class="label">Total Patients</div>
                        <div class="value">${s.total_patients}</div>
                        <div class="subtext">Registered in records</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Medical Doctors</div>
                        <div class="value">${s.total_doctors}</div>
                        <div class="subtext">Across 5 departments</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Active Appointments</div>
                        <div class="value">${s.active_appointments}</div>
                        <div class="subtext">Scheduled outpatients</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Bed Occupancy</div>
                        <div class="value">${s.occupancy_rate}%</div>
                        <div class="subtext">${s.occupied_rooms} of ${s.total_rooms} beds filled</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">Revenue Collected</div>
                        <div class="value">$${s.total_revenue.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                        <div class="subtext">Pending: $${s.pending_bills_amount.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    </div>
                `;

                // 2. Patients Table
                const pTbody = document.querySelector('#patientsTable tbody');
                pTbody.innerHTML = data.patients.map(p => `
                    <tr>
                        <td><strong>#${p.patient_id}</strong></td>
                        <td>${p.first_name} ${p.last_name}</td>
                        <td>${p.dob}</td>
                        <td>${p.gender}</td>
                        <td><span style="font-weight:700; color:var(--primary);">${p.blood_group}</span></td>
                        <td>${p.phone}</td>
                        <td>${p.emergency_contact_name} (${p.emergency_contact_phone})</td>
                    </tr>
                `).join('');

                // 3. Appointments Table
                const aTbody = document.querySelector('#appointmentsTable tbody');
                aTbody.innerHTML = data.appointments.map(a => `
                    <tr>
                        <td><strong>#${a.appointment_id}</strong></td>
                        <td>${a.patient_name}</td>
                        <td>${a.doctor_name}</td>
                        <td>${a.department_name}</td>
                        <td>${a.appointment_date}</td>
                        <td>${a.appointment_time}</td>
                        <td><span class="status-badge status-${a.appointment_status}">${a.appointment_status}</span></td>
                        <td>${a.reason}</td>
                    </tr>
                `).join('');

                // 4. Doctors Table
                const dTbody = document.querySelector('#doctorsTable tbody');
                dTbody.innerHTML = data.doctors.map(d => `
                    <tr>
                        <td><strong>#${d.staff_id}</strong></td>
                        <td>Dr. ${d.first_name} ${d.last_name}</td>
                        <td>${d.specialization}</td>
                        <td>${d.department_name}</td>
                        <td>${d.phone}</td>
                        <td>${d.email}</td>
                        <td><span class="status-badge status-Completed">${d.status}</span></td>
                    </tr>
                `).join('');

                // 5. Rooms & Admissions
                const rTbody = document.querySelector('#roomsTable tbody');
                rTbody.innerHTML = data.rooms.map(r => `
                    <tr>
                        <td>#${r.room_id}</td>
                        <td><strong>${r.room_number}</strong></td>
                        <td>${r.room_type}</td>
                        <td>$${r.daily_rate.toFixed(2)} / day</td>
                        <td><span class="status-badge status-${r.status}">${r.status}</span></td>
                    </tr>
                `).join('');

                const admTbody = document.querySelector('#admissionsTable tbody');
                admTbody.innerHTML = data.admissions.map(adm => `
                    <tr>
                        <td><strong>#${adm.admission_id}</strong></td>
                        <td>${adm.patient_name}</td>
                        <td>${adm.blood_group}</td>
                        <td>${adm.room_number}</td>
                        <td>${adm.room_type}</td>
                        <td>${adm.admission_date}</td>
                        <td>${adm.attending_doctor}</td>
                        <td>${adm.diagnosis_on_admission}</td>
                    </tr>
                `).join('');

                // 6. Billing Table
                const bTbody = document.querySelector('#billingTable tbody');
                bTbody.innerHTML = data.bills.map(b => `
                    <tr>
                        <td><strong>#${b.bill_id}</strong></td>
                        <td>${b.patient_name}</td>
                        <td>$${b.total_amount.toFixed(2)}</td>
                        <td>$${b.discount.toFixed(2)}</td>
                        <td>$${b.tax.toFixed(2)}</td>
                        <td><strong>$${b.net_amount.toFixed(2)}</strong></td>
                        <td>$${b.total_paid.toFixed(2)}</td>
                        <td style="color:${b.outstanding_balance > 0 ? 'var(--danger)' : 'var(--success)'}; font-weight:600;">$${b.outstanding_balance.toFixed(2)}</td>
                        <td><span class="status-badge status-${b.payment_status}">${b.payment_status}</span></td>
                    </tr>
                `).join('');

                // 7. Department Revenue Performance
                const dpTbody = document.querySelector('#deptPerfTable tbody');
                dpTbody.innerHTML = data.dept_perf.map(dp => `
                    <tr>
                        <td><strong>${dp.department_name}</strong></td>
                        <td>${dp.consultations}</td>
                        <td>$${dp.billed.toFixed(2)}</td>
                        <td style="color:var(--success); font-weight:700;">$${dp.collected.toFixed(2)}</td>
                    </tr>
                `).join('');

                // 8. Doctor Workload
                const dwTbody = document.querySelector('#doctorWorkloadTable tbody');
                dwTbody.innerHTML = data.doc_workload.map(dw => `
                    <tr>
                        <td><strong>${dw.doctor_name}</strong></td>
                        <td>${dw.department_name}</td>
                        <td>${dw.total_appts}</td>
                        <td>${dw.completed}</td>
                        <td>$${dw.revenue.toFixed(2)}</td>
                    </tr>
                `).join('');

            } catch (err) {
                console.error("Error loading dashboard data:", err);
            }
        }

        async function submitPatient(e) {
            e.preventDefault();
            const payload = {
                first: document.getElementById('p_first').value,
                last: document.getElementById('p_last').value,
                dob: document.getElementById('p_dob').value,
                gender: document.getElementById('p_gender').value,
                blood: document.getElementById('p_blood').value,
                phone: document.getElementById('p_phone').value,
                address: document.getElementById('p_address').value,
                em_name: document.getElementById('p_em_name').value,
                em_phone: document.getElementById('p_em_phone').value
            };
            const res = await fetch('/api/add_patient', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                alert('Patient registered successfully!');
                toggleForm('newPatientForm');
                loadData();
            } else {
                alert('Failed to add patient.');
            }
        }

        async function submitAppointment(e) {
            e.preventDefault();
            const payload = {
                pid: parseInt(document.getElementById('a_pid').value),
                doc_id: parseInt(document.getElementById('a_docid').value),
                date: document.getElementById('a_date').value,
                time: document.getElementById('a_time').value,
                reason: document.getElementById('a_reason').value,
                fee: parseFloat(document.getElementById('a_fee').value || 500)
            };
            const res = await fetch('/api/book_appointment', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                alert('Appointment booked successfully!');
                toggleForm('newApptForm');
                loadData();
            } else {
                alert('Failed to book appointment.');
            }
        }

        async function runSql() {
            const query = document.getElementById('sqlQueryInput').value;
            const res = await fetch('/api/execute_sql', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query})
            });
            const data = await res.json();
            const thead = document.querySelector('#sqlResultsTable thead');
            const tbody = document.querySelector('#sqlResultsTable tbody');
            thead.innerHTML = '';
            tbody.innerHTML = '';

            if (data.error) {
                tbody.innerHTML = `<tr><td style="color:var(--danger);">${data.error}</td></tr>`;
                return;
            }
            if (!data.rows || data.rows.length === 0) {
                tbody.innerHTML = `<tr><td style="color:var(--text-muted);">No records returned.</td></tr>`;
                return;
            }
            const keys = Object.keys(data.rows[0]);
            thead.innerHTML = '<tr>' + keys.map(k => `<th>${k}</th>`).join('') + '</tr>';
            tbody.innerHTML = data.rows.map(row => 
                '<tr>' + keys.map(k => `<td>${row[k] !== null ? row[k] : '<em style="color:#94a3b8">NULL</em>'}</td>`).join('') + '</tr>'
            ).join('');
        }

        loadData();
    </script>
</body>
</html>
"""

class HospitalHandler(BaseHTTPRequestHandler):
    db = HospitalDB()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/" or url.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if os.path.exists(INDEX_HTML_PATH):
                with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif url.path == "/api/data":
            stats = self.db.get_dashboard_stats()
            patients = self.db.query("SELECT * FROM patients ORDER BY patient_id DESC")
            appointments = self.db.query("SELECT * FROM vw_patient_appointments ORDER BY appointment_date, appointment_time")
            doctors = self.db.query("""
                SELECT s.*, d.department_name 
                FROM staff s 
                JOIN departments d ON s.department_id = d.department_id 
                WHERE s.role = 'Doctor'
            """)
            rooms = self.db.query("SELECT * FROM rooms ORDER BY room_id")
            admissions = self.db.query("SELECT * FROM vw_active_admissions")
            bills = self.db.query("SELECT * FROM vw_billing_summary ORDER BY bill_id DESC")
            dept_perf = self.db.query("""
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
            """)
            doc_workload = self.db.query("""
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
            """)

            payload = {
                "stats": stats,
                "patients": patients,
                "appointments": appointments,
                "doctors": doctors,
                "rooms": rooms,
                "admissions": admissions,
                "bills": bills,
                "dept_perf": dept_perf,
                "doc_workload": doc_workload
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = json.loads(body) if body else {}

        url = urllib.parse.urlparse(self.path)
        if url.path == "/api/add_patient":
            pid = self.db.add_patient(
                data['first'], data['last'], data['dob'], data['gender'],
                data['blood'], data['phone'], '', data['address'],
                data['em_name'], data['em_phone']
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "patient_id": pid}).encode('utf-8'))

        elif url.path == "/api/book_appointment":
            aid = self.db.book_appointment(
                data['pid'], data['doc_id'], data['date'], data['time'], data['reason'], data.get('fee', 500.0)
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "appointment_id": aid}).encode('utf-8'))

        elif url.path == "/api/execute_sql":
            query = data.get('query', '').strip()
            try:
                rows = self.db.query(query)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"rows": rows}).encode('utf-8'))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port: int = 8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, HospitalHandler)
    print("=" * 60)
    print(f" MedPulse Hospital Management System Dashboard")
    print(f" Server running at: http://localhost:{port}")
    print(f" Press Ctrl+C to stop the server.")
    print("=" * 60)
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
