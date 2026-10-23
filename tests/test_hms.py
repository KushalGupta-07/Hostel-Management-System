import unittest
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
import db

class TestHostelManagementSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.testing = True
        cls.client = app.test_client()
        # Initialize DB and ensure tables exist
        db.init_db()

    def test_01_db_connection(self):
        """Verify direct MySQL connection and query execution."""
        conn = db.get_db_connection()
        self.assertIsNotNone(conn)
        conn.close()

    def test_02_database_status_api(self):
        """Test API status endpoint."""
        response = self.client.get('/api/db-status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'connected')
        self.assertEqual(data['database'], 'hostal_management')

    def test_03_dashboard_route(self):
        """Test dashboard page loads with 200 OK."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hostel Overview & Dashboard', response.data)
        self.assertIn(b'Bed Occupancy', response.data)

    def test_04_rooms_route_and_crud(self):
        """Test rooms listing and adding a new room."""
        # 1. Rooms listing
        response = self.client.get('/rooms')
        self.assertEqual(response.status_code, 200)

        # 2. Add test room
        room_num = 'TEST-999'
        db.execute_db("DELETE FROM rooms WHERE room_number = %s", [room_num])
        
        post_resp = self.client.post('/rooms/add', data={
            'room_number': room_num,
            'floor': 4,
            'room_type': 'Double',
            'capacity': 2,
            'fee_per_month': 5500.0,
            'amenities': 'Test Amenities'
        }, follow_redirects=True)
        self.assertEqual(post_resp.status_code, 200)
        
        # Verify in DB
        room = db.query_db("SELECT * FROM rooms WHERE room_number = %s", [room_num], one=True)
        self.assertIsNotNone(room)
        self.assertEqual(room['capacity'], 2)
        self.assertEqual(room['status'], 'Available')

        # Clean up
        db.execute_db("DELETE FROM rooms WHERE room_number = %s", [room_num])

    def test_05_student_workflow(self):
        """Test student registration, room allocation, fee generation, and checkout."""
        # Setup clean test room
        test_room_num = 'TEST-RM-101'
        db.execute_db("DELETE FROM rooms WHERE room_number = %s", [test_room_num])
        room_id = db.execute_db("""
            INSERT INTO rooms (room_number, floor, room_type, capacity, fee_per_month, status)
            VALUES (%s, 1, 'Single', 1, 7000.0, 'Available')
        """, [test_room_num], return_id=True)

        stu_code = 'TEST-STU-001'
        db.execute_db("DELETE FROM students WHERE student_id_code = %s", [stu_code])

        # Register Student
        reg_resp = self.client.post('/students/add', data={
            'student_id_code': stu_code,
            'full_name': 'Test Student',
            'email': 'test.stu@test.com',
            'phone': '9998887770',
            'gender': 'Male',
            'room_id': room_id
        }, follow_redirects=True)
        self.assertEqual(reg_resp.status_code, 200)

        student = db.query_db("SELECT * FROM students WHERE student_id_code = %s", [stu_code], one=True)
        self.assertIsNotNone(student)
        self.assertEqual(student['status'], 'Active')

        # Verify room occupancy incremented and room is marked 'Full'
        room = db.query_db("SELECT * FROM rooms WHERE id = %s", [room_id], one=True)
        self.assertEqual(room['current_occupancy'], 1)
        self.assertEqual(room['status'], 'Full')

        # Pay pending fee for checkout
        db.execute_db("UPDATE fees SET status = 'Paid' WHERE student_id = %s", [student['id']])

        # Checkout student
        co_resp = self.client.post(f'/students/checkout/{student["id"]}', follow_redirects=True)
        self.assertEqual(co_resp.status_code, 200)

        # Verify student status changed and room freed
        updated_student = db.query_db("SELECT * FROM students WHERE id = %s", [student['id']], one=True)
        self.assertEqual(updated_student['status'], 'Checked-Out')
        self.assertIsNone(updated_student['room_id'])

        updated_room = db.query_db("SELECT * FROM rooms WHERE id = %s", [room_id], one=True)
        self.assertEqual(updated_room['current_occupancy'], 0)
        self.assertEqual(updated_room['status'], 'Available')

        # Clean up
        db.execute_db("DELETE FROM students WHERE id = %s", [student['id']])
        db.execute_db("DELETE FROM rooms WHERE id = %s", [room_id])

    def test_06_complaint_workflow(self):
        """Test lodging complaint and resolving ticket."""
        post_resp = self.client.post('/complaints/add', data={
            'title': 'Test Water Issue',
            'category': 'Plumbing',
            'priority': 'High',
            'description': 'Water leaking from test tap'
        }, follow_redirects=True)
        self.assertEqual(post_resp.status_code, 200)

        complaint = db.query_db("SELECT * FROM complaints WHERE title = 'Test Water Issue' ORDER BY id DESC", one=True)
        self.assertIsNotNone(complaint)
        self.assertEqual(complaint['status'], 'Open')

        # Resolve ticket
        upd_resp = self.client.post(f'/complaints/update-status/{complaint["id"]}', data={
            'status': 'Resolved',
            'resolution_notes': 'Replaced test washer'
        }, follow_redirects=True)
        self.assertEqual(upd_resp.status_code, 200)

        updated_c = db.query_db("SELECT * FROM complaints WHERE id = %s", [complaint['id']], one=True)
        self.assertEqual(updated_c['status'], 'Resolved')
        self.assertIsNotNone(updated_c['resolved_at'])

        # Clean up
        db.execute_db("DELETE FROM complaints WHERE id = %s", [complaint['id']])

    def test_07_all_nav_pages(self):
        """Verify all navigation endpoints return HTTP 200."""
        routes = ['/fees', '/complaints', '/visitors', '/mess', '/staff-notices']
        for r in routes:
            response = self.client.get(r)
            self.assertEqual(response.status_code, 200, f"Route {r} failed with status {response.status_code}")

if __name__ == '__main__':
    unittest.main()
