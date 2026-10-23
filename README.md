# Hostel Management System (HMS)

A complete, production-grade **Hostel Management System** web application connected to a local **MySQL** database.

---

## 🌟 Key Features

- **Executive Analytics Dashboard**: Real-time KPI counters (Occupancy, Available Beds, Active Residents, Total Fees Collected, Pending Dues, Open Complaints), occupancy doughnut chart (Chart.js), and floor-wise progress bars.
- **Room & Bed Allocation Management**:
  - Add, edit, view, and manage rooms across different floors.
  - Room types: Single, Double, Triple, Dormitory.
  - Real-time occupancy tracking and dynamic status badges (`Available`, `Full`, `Maintenance`).
  - Automatic capacity enforcement preventing overbooking.
- **Student Admissions & Resident Directory**:
  - Full student registration (ID/Roll No, Name, Phone, Email, Gender, Blood Group, Address, Guardian Details).
  - Room allocation with automated first-month rent invoice generation.
  - Comprehensive student dossier (financial history, complaints, passes, visitors).
  - Formal student check-out workflow with pending dues verification.
- **Fees & Payment Billing**:
  - Invoicing for Hostel Rent, Mess Fees, Security Deposit, Maintenance, and Utilities.
  - Record payments with UPI / Net Banking / Cash / Card and transaction references.
  - Printable, professional fee receipts (`REC-XXXXX`) formatted for desktop printing and PDF export.
  - Status indicators (`Paid`, `Pending`, `Overdue`).
- **Complaints & Maintenance Helpdesk**:
  - Ticket lodging with categories (Electrical, Plumbing, Wi-Fi, Furniture, Cleaning, Mess, Other) and priority levels (Low, Medium, High, Urgent).
  - Workflow status transitions (`Open` → `In Progress` → `Resolved`) with technician resolution notes.
- **Security Desk (Visitors & Gate Passes)**:
  - Daily visitor registration, relationship, purpose, in-time, and exit tracking.
  - Student out-pass / night-out requests and approval by warden office.
- **Mess & Dining Schedule**:
  - 7-day weekly meal planner covering Breakfast, Lunch, Snacks, and Dinner.
  - Modal editor to update meal menus on the fly.
- **Staff Roster & Notice Board**:
  - Staff management for Wardens, Security, Housekeeping, Cooks, Electricians, and Plumbers.
  - Digital notice board for hostel-wide broadcasts with priority alerts (`Normal`, `Important`, `Urgent`).

---

## 🗄️ Database Configuration

- **Database Name**: `hostal_management`
- **User**: `root`
- **Password**: `kushalgupta@27`
- **Host**: `localhost` (Port: `3306`)

---

## 🚀 Quick Start Instructions

### Method 1: Using the Windows Launcher
Simply double-click the **`run.bat`** file in the project directory. It will:
1. Initialize the MySQL tables and seeds if needed.
2. Synchronize room occupancies.
3. Automatically launch your default web browser to `http://127.0.0.1:5000`.
4. Start the Flask application.

### Method 2: Manual Terminal Startup
1. Open PowerShell / Command Prompt in the project directory:
   ```powershell
   # 1. Install dependencies
   pip install -r requirements.txt

   # 2. Initialize database & seed records
   python db.py

   # 3. Start the application
   python app.py
   ```
2. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 📁 Project Structure

```
Database Project/
├── app.py                  # Main Flask application and controllers
├── config.py               # Database and environment configurations
├── db.py                   # MySQL connection manager and query helpers
├── schema.sql              # MySQL DDL schema and initial seed data
├── requirements.txt        # Python package dependencies
├── run.bat                 # One-click Windows launcher
├── README.md               # Documentation and guide
├── static/
│   └── css/
│       └── style.css       # Custom modern dashboard stylesheet
├── templates/
│   ├── base.html           # Master layout with sidebar & topbar
│   ├── dashboard.html      # KPI analytics dashboard & charts
│   ├── rooms.html          # Rooms list & room management
│   ├── room_detail.html    # Room occupants & complaints view
│   ├── students.html       # Student admissions & directory
│   ├── student_detail.html # Student profile, ledger & check-out
│   ├── fees.html           # Fee billing & payment tracking
│   ├── receipt.html        # Printable payment receipt
│   ├── complaints.html     # Maintenance ticket desk
│   ├── visitors.html       # Visitors log & gate passes
│   ├── mess.html           # Weekly mess meal menu
│   └── staff_notices.html  # Staff roster & notice board
└── tests/
    └── test_hms.py         # Automated test suite
```
