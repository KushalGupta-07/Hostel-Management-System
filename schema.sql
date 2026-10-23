-- =====================================================================
-- Hostel Management System (hostal_management) Database Schema
-- =====================================================================

CREATE DATABASE IF NOT EXISTS hostal_management;
USE hostal_management;

-- 1. Rooms Table
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(20) NOT NULL UNIQUE,
    floor INT NOT NULL DEFAULT 1,
    room_type ENUM('Single', 'Double', 'Triple', 'Dormitory') NOT NULL DEFAULT 'Double',
    capacity INT NOT NULL DEFAULT 2,
    current_occupancy INT NOT NULL DEFAULT 0,
    fee_per_month DECIMAL(10, 2) NOT NULL DEFAULT 6000.00,
    status ENUM('Available', 'Full', 'Maintenance') NOT NULL DEFAULT 'Available',
    amenities VARCHAR(255) DEFAULT 'High-speed Wi-Fi, Attached Bathroom, Study Desk, Cupboard',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Students Table
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id_code VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NULL,
    phone VARCHAR(20) NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL DEFAULT 'Male',
    dob DATE NULL,
    address TEXT NULL,
    guardian_name VARCHAR(100) NULL,
    guardian_phone VARCHAR(20) NULL,
    blood_group VARCHAR(10) NULL,
    room_id INT NULL,
    check_in_date DATE DEFAULT (CURRENT_DATE),
    check_out_date DATE NULL,
    status ENUM('Active', 'Checked-Out', 'Suspended') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Fees Table
CREATE TABLE IF NOT EXISTS fees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    fee_type ENUM('Hostel Rent', 'Mess Fee', 'Security Deposit', 'Maintenance', 'Utility') NOT NULL DEFAULT 'Hostel Rent',
    amount DECIMAL(10, 2) NOT NULL,
    due_date DATE NOT NULL,
    paid_date DATE NULL,
    payment_mode ENUM('Cash', 'UPI', 'Credit Card', 'Debit Card', 'Net Banking') DEFAULT 'UPI',
    transaction_ref VARCHAR(100) NULL,
    status ENUM('Paid', 'Pending', 'Overdue') NOT NULL DEFAULT 'Pending',
    notes VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Complaints Table
CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NULL,
    room_id INT NULL,
    title VARCHAR(150) NOT NULL,
    category ENUM('Electrical', 'Plumbing', 'Wi-Fi / Internet', 'Furniture', 'Cleaning / Housekeeping', 'Mess / Food', 'Other') NOT NULL DEFAULT 'Electrical',
    priority ENUM('Low', 'Medium', 'High', 'Urgent') NOT NULL DEFAULT 'Medium',
    description TEXT NOT NULL,
    status ENUM('Open', 'In Progress', 'Resolved') NOT NULL DEFAULT 'Open',
    resolution_notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Visitors Table
CREATE TABLE IF NOT EXISTS visitors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    visitor_name VARCHAR(100) NOT NULL,
    visitor_phone VARCHAR(20) NOT NULL,
    relation VARCHAR(50) NOT NULL,
    id_proof VARCHAR(100) NULL,
    in_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    out_time DATETIME NULL,
    purpose VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Gate Passes (Out-Pass) Table
CREATE TABLE IF NOT EXISTS gate_passes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    leave_date DATETIME NOT NULL,
    return_date DATETIME NOT NULL,
    destination VARCHAR(150) NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected', 'Returned') NOT NULL DEFAULT 'Pending',
    approved_by VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Meal Menu Table
CREATE TABLE IF NOT EXISTS meal_menu (
    id INT AUTO_INCREMENT PRIMARY KEY,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    meal_type ENUM('Breakfast', 'Lunch', 'Snacks', 'Dinner') NOT NULL,
    menu_items TEXT NOT NULL,
    UNIQUE KEY unique_day_meal (day_of_week, meal_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Staff Table
CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role ENUM('Warden', 'Assistant Warden', 'Security Supervisor', 'Security Guard', 'Chef / Cook', 'Cleaning Staff', 'Maintenance Electrician', 'Plumber') NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NULL,
    shift ENUM('Morning', 'Evening', 'Night', 'General') NOT NULL DEFAULT 'General',
    salary DECIMAL(10, 2) NOT NULL DEFAULT 18000.00,
    status ENUM('Active', 'On Leave', 'Inactive') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Notices Table
CREATE TABLE IF NOT EXISTS notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    priority ENUM('Normal', 'Important', 'Urgent') NOT NULL DEFAULT 'Normal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- Initial Seed Data
-- =====================================================================

-- Insert Rooms
INSERT IGNORE INTO rooms (room_number, floor, room_type, capacity, current_occupancy, fee_per_month, status, amenities) VALUES
('101', 1, 'Single', 1, 1, 8000.00, 'Full', 'AC, High-speed Wi-Fi, Attached Bathroom, Balcony'),
('102', 1, 'Double', 2, 2, 6000.00, 'Full', 'High-speed Wi-Fi, Attached Bathroom, Study Desks'),
('103', 1, 'Double', 2, 1, 6000.00, 'Available', 'High-speed Wi-Fi, Attached Bathroom, Study Desks'),
('104', 1, 'Triple', 3, 0, 4500.00, 'Available', 'Wi-Fi, Common Bathroom, Lockers'),
('201', 2, 'Single', 1, 0, 8500.00, 'Available', 'AC, High-speed Wi-Fi, Attached Bathroom, Smart TV'),
('202', 2, 'Double', 2, 2, 6000.00, 'Full', 'High-speed Wi-Fi, Attached Bathroom, Study Desks'),
('203', 2, 'Double', 2, 0, 6000.00, 'Maintenance', 'High-speed Wi-Fi, Attached Bathroom, Study Desks (Repainting)'),
('204', 2, 'Triple', 3, 1, 4500.00, 'Available', 'Wi-Fi, Common Bathroom, Lockers'),
('301', 3, 'Dormitory', 4, 2, 3500.00, 'Available', 'Wi-Fi, Common Washrooms, 4 Bunk Beds, Lockers'),
('302', 3, 'Double', 2, 0, 6000.00, 'Available', 'High-speed Wi-Fi, Attached Bathroom, Balcony');

-- Insert Students
INSERT IGNORE INTO students (student_id_code, full_name, email, phone, gender, dob, address, guardian_name, guardian_phone, blood_group, room_id, check_in_date, status) VALUES
('STU-2026-001', 'Aarav Sharma', 'aarav.sharma@example.com', '9876543210', 'Male', '2004-05-14', 'B-12, Green Park, New Delhi', 'Rajesh Sharma', '9876500001', 'O+', 1, '2026-01-10', 'Active'),
('STU-2026-002', 'Rohan Verma', 'rohan.verma@example.com', '9876543211', 'Male', '2003-11-20', 'Sector 15, Noida, UP', 'Sunil Verma', '9876500002', 'B+', 2, '2026-01-12', 'Active'),
('STU-2026-003', 'Aditya Singh', 'aditya.singh@example.com', '9876543212', 'Male', '2004-03-08', 'Civil Lines, Jaipur, Rajasthan', 'Mahesh Singh', '9876500003', 'A+', 2, '2026-01-15', 'Active'),
('STU-2026-004', 'Kunal Patel', 'kunal.patel@example.com', '9876543213', 'Male', '2004-08-25', 'Navrangpura, Ahmedabad, Gujarat', 'Dinesh Patel', '9876500004', 'AB+', 3, '2026-02-01', 'Active'),
('STU-2026-005', 'Vikram Malhotra', 'vikram.m@example.com', '9876543214', 'Male', '2003-09-12', 'Model Town, Ludhiana, Punjab', 'Harish Malhotra', '9876500005', 'O-', 6, '2026-02-05', 'Active'),
('STU-2026-006', 'Siddharth Roy', 'sid.roy@example.com', '9876543215', 'Male', '2004-01-30', 'Salt Lake, Kolkata, WB', 'Anil Roy', '9876500006', 'B-', 6, '2026-02-10', 'Active'),
('STU-2026-007', 'Aryan Mishra', 'aryan.mishra@example.com', '9876543216', 'Male', '2003-07-19', 'Aliganj, Lucknow, UP', 'Pramod Mishra', '9876500007', 'A-', 8, '2026-02-15', 'Active'),
('STU-2026-008', 'Devansh Gupta', 'devansh.g@example.com', '9876543217', 'Male', '2004-12-05', 'Kankarbagh, Patna, Bihar', 'Vinod Gupta', '9876500008', 'O+', 9, '2026-03-01', 'Active'),
('STU-2026-009', 'Nikhil Joshi', 'nikhil.j@example.com', '9876543218', 'Male', '2003-04-22', 'Kothrud, Pune, Maharashtra', 'Sanjay Joshi', '9876500009', 'B+', 9, '2026-03-05', 'Active');

-- Insert Fees
INSERT IGNORE INTO fees (student_id, fee_type, amount, due_date, paid_date, payment_mode, transaction_ref, status, notes) VALUES
(1, 'Hostel Rent', 8000.00, '2026-04-05', '2026-04-02', 'UPI', 'UPI/20260402/847291', 'Paid', 'April 2026 Rent Single AC Room'),
(1, 'Mess Fee', 4000.00, '2026-04-05', '2026-04-02', 'UPI', 'UPI/20260402/847292', 'Paid', 'April 2026 Mess Subscription'),
(2, 'Hostel Rent', 6000.00, '2026-04-05', '2026-04-04', 'Net Banking', 'TXN-9988231', 'Paid', 'April 2026 Rent Room 102'),
(3, 'Hostel Rent', 6000.00, '2026-04-05', NULL, NULL, NULL, 'Pending', 'April 2026 Rent Room 102'),
(4, 'Hostel Rent', 6000.00, '2026-03-05', NULL, NULL, NULL, 'Overdue', 'March 2026 Rent Room 103 overdue reminder sent'),
(5, 'Hostel Rent', 6000.00, '2026-04-05', '2026-04-03', 'Cash', 'RCP-1049', 'Paid', 'Paid in cash at warden office'),
(6, 'Hostel Rent', 6000.00, '2026-04-05', NULL, NULL, NULL, 'Pending', 'April 2026 Rent Room 202'),
(7, 'Security Deposit', 5000.00, '2026-02-15', '2026-02-15', 'UPI', 'UPI/20260215/982143', 'Paid', 'Refundable Security Deposit'),
(8, 'Hostel Rent', 3500.00, '2026-04-05', '2026-04-01', 'Debit Card', 'CARD-88310', 'Paid', 'Dormitory Rent April 2026');

-- Insert Complaints
INSERT IGNORE INTO complaints (student_id, room_id, title, category, priority, description, status, resolution_notes, resolved_at) VALUES
(1, 1, 'AC cooling slow', 'Electrical', 'Medium', 'The air conditioner in room 101 is not cooling adequately during afternoon hours.', 'Resolved', 'AC technician serviced the air filters and topped up refrigerant.', '2026-04-12 14:30:00'),
(2, 2, 'Bathroom tap leaking continuously', 'Plumbing', 'High', 'Water leakage from the main shower head in Room 102.', 'In Progress', 'Plumber assigned, replacement washer being installed today.', NULL),
(4, 3, 'Wi-Fi connection keeps dropping', 'Wi-Fi / Internet', 'Medium', 'Wi-Fi signal on floor 1 wing B drops frequently in evening.', 'Open', NULL, NULL),
(5, 6, 'Study chair wheel damaged', 'Furniture', 'Low', 'One of the study chair caster wheels broke off.', 'Open', NULL, NULL);

-- Insert Visitors
INSERT IGNORE INTO visitors (student_id, visitor_name, visitor_phone, relation, id_proof, in_time, out_time, purpose) VALUES
(1, 'Rajesh Sharma', '9876500001', 'Father', 'Aadhar Card - 4821', '2026-04-18 10:30:00', '2026-04-18 13:00:00', 'Delivered home parcel and books'),
(2, 'Amit Verma', '9876500099', 'Brother', 'Driving License - DL-14-2018', '2026-04-19 11:15:00', NULL, 'Meeting for weekend study materials');

-- Insert Gate Passes
INSERT IGNORE INTO gate_passes (student_id, leave_date, return_date, destination, reason, status, approved_by) VALUES
(1, '2026-04-20 18:00:00', '2026-04-22 20:00:00', 'New Delhi Home', 'Sister wedding ceremony', 'Approved', 'Warden Dr. R. K. Saxena'),
(3, '2026-04-21 09:00:00', '2026-04-21 21:00:00', 'City Center Mall', 'Weekend grocery and project printouts', 'Approved', 'Warden Dr. R. K. Saxena'),
(4, '2026-04-22 17:00:00', '2026-04-23 10:00:00', 'Ahmedabad Home', 'Personal family reason', 'Pending', NULL);

-- Insert Staff
INSERT IGNORE INTO staff (name, role, phone, email, shift, salary, status) VALUES
('Dr. R. K. Saxena', 'Warden', '9811223344', 'warden.saxena@hostel.edu', 'General', 55000.00, 'Active'),
('Mr. Vikram Rathore', 'Assistant Warden', '9811223355', 'vikram.rathore@hostel.edu', 'Night', 35000.00, 'Active'),
('Baljit Singh', 'Security Supervisor', '9811223366', 'security@hostel.edu', 'Morning', 22000.00, 'Active'),
('Rameshwar Prasad', 'Chef / Cook', '9811223377', 'mess.chef@hostel.edu', 'Morning', 25000.00, 'Active'),
('Mohan Lal', 'Maintenance Electrician', '9811223388', 'electrician@hostel.edu', 'General', 20000.00, 'Active'),
('Santosh Kumar', 'Plumber', '9811223399', 'plumber@hostel.edu', 'General', 19000.00, 'Active');

-- Insert Notices
INSERT IGNORE INTO notices (title, content, priority) VALUES
('Hostel Gate Curfew Notice', 'All residents are strictly reminded that the hostel main gate closes at 10:00 PM. Late entries require prior written approval or out-pass.', 'Important'),
('Routine Water Tank Cleaning on Sunday', 'Please note that overhead water tanks will undergo periodic cleaning this Sunday between 9:00 AM and 1:00 PM. Please store required water in advance.', 'Normal'),
('Hostel Wi-Fi Bandwidth Upgrade', 'High-speed fiber connectivity has been upgraded across all floors. Please contact IT desk if facing latency issues in your room.', 'Normal');

-- Insert Meal Menu (7 Days x 4 Meals)
INSERT IGNORE INTO meal_menu (day_of_week, meal_type, menu_items) VALUES
('Monday', 'Breakfast', 'Poha, Boiled Eggs / Banana, Tea / Coffee, Bread & Butter'),
('Monday', 'Lunch', 'Dal Tadka, Seasonal Sabzi, Jeera Rice, Phulkas, Fresh Curd, Salad'),
('Monday', 'Snacks', 'Samosa, Green Chutney, Masala Chai'),
('Monday', 'Dinner', 'Paneer Butter Masala, Mixed Dal, Steamed Rice, Roti, Gulab Jamun'),

('Tuesday', 'Breakfast', 'Aloo Paratha, Curd, Pickle, Tea / Coffee'),
('Tuesday', 'Lunch', 'Rajma Masala, Steamed Basmati Rice, Aloo Gobi, Roti, Papad'),
('Tuesday', 'Snacks', 'Veg Sandwich, Tea / Coffee'),
('Tuesday', 'Dinner', 'Egg Curry / Malai Kofta, Dal Makhani, Pulao, Butter Roti, Ice Cream'),

('Wednesday', 'Breakfast', 'Idli, Medu Vada, Sambar, Coconut Chutney, Filter Coffee'),
('Wednesday', 'Lunch', 'Chole Masala, Bhature / Poori, Jeera Rice, Boondi Raita, Salad'),
('Wednesday', 'Snacks', 'Pakoras (Paneer & Onion), Mint Chutney, Tea'),
('Wednesday', 'Dinner', 'Chicken Curry / Shahi Paneer, Dal Fry, Steamed Rice, Tandoori Roti, Kheer'),

('Thursday', 'Breakfast', 'Masala Dosa, Sambar, Tomato Chutney, Tea / Milk'),
('Thursday', 'Lunch', 'Kadhi Pakoda, Steamed Rice, Bhindi Do Pyaza, Chapati, Salad'),
('Thursday', 'Snacks', 'Biscuits & Cookies, Bhel Puri, Tea'),
('Thursday', 'Dinner', 'Veg Biryani / Dum Chicken Biryani, Mirchi Ka Salan, Raita, Rasgulla'),

('Friday', 'Breakfast', 'Upma with Coconut Chutney, Boiled Sprouts, Tea / Coffee'),
('Friday', 'Lunch', 'Dal Palak, Aloo Jeera, Steamed Rice, Roti, Buttermilk, Pickle'),
('Friday', 'Snacks', 'Pav Bhaji, Lemon Water / Tea'),
('Friday', 'Dinner', 'Matar Mushroom, Yellow Dal, Veg Pulao, Garlic Naan, Moong Dal Halwa'),

('Saturday', 'Breakfast', 'Poori Sabzi (Aloo Tamatar), Halwa, Tea / Milk'),
('Saturday', 'Lunch', 'Mixed Vegetable Khichdi, Gujarati Kadhi, Begun Bhaja, Papad, Pickle'),
('Saturday', 'Snacks', 'Veg Cutlet, Tomato Ketchup, Tea'),
('Saturday', 'Dinner', 'Kadhai Paneer, Dal Tadka, Jeera Rice, Tawa Roti, Fruit Custard'),

('Sunday', 'Breakfast', 'Chole Kulche, Sweet Lassi / Tea, Fresh Fruits'),
('Sunday', 'Lunch', 'Hostel Special Feast: Butter Chicken / Paneer Lababdar, Dal Makhani, Peas Pulao, Naan, Gulab Jamun'),
('Sunday', 'Snacks', 'Corn Chaat / French Fries, Cold Coffee / Tea'),
('Sunday', 'Dinner', 'Light Dinner: Khichdi / Dal Rice, Aloo Methi, Roti, Warm Milk');
