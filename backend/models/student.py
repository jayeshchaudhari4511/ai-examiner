from datetime import datetime
from bson import ObjectId
from utils.db_connection import db_connection

_LOCAL_STUDENTS = {}

class Student:
    @staticmethod
    def get_collection():
        """Get students collection with lazy connection"""
        return db_connection.get_collection('students')
    
    @staticmethod
    def create(name, email, roll_number=None, class_name=None):
        """Create a new student"""
        student = {
            'name': name,
            'email': email,
            'roll_number': roll_number,
            'class': class_name,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        try:
            result = Student.get_collection().insert_one(student)
            student['_id'] = result.inserted_id
        except Exception:
            student['_id'] = f'local-student-{len(_LOCAL_STUDENTS) + 1}'
            _LOCAL_STUDENTS[student['_id']] = student
        return student
    
    @staticmethod
    def find_by_email(email):
        """Find student by email"""
        try:
            return Student.get_collection().find_one({'email': email})
        except Exception:
            return next((s for s in _LOCAL_STUDENTS.values() if (s.get('email') or '').lower() == (email or '').lower()), None)
    
    @staticmethod
    def find_by_id(student_id):
        """Find student by ID"""
        try:
            return Student.get_collection().find_one({'_id': ObjectId(student_id)})
        except Exception:
            return _LOCAL_STUDENTS.get(student_id)
    
    @staticmethod
    def find_by_roll_number(roll_number):
        """Find student by roll number"""
        try:
            return Student.get_collection().find_one({'roll_number': roll_number})
        except Exception:
            return next((s for s in _LOCAL_STUDENTS.values() if s.get('roll_number') == roll_number), None)
    
    @staticmethod
    def update(student_id, data):
        """Update student information"""
        data['updated_at'] = datetime.utcnow()
        return Student.get_collection().update_one(
            {'_id': ObjectId(student_id)},
            {'$set': data}
        )
    
    @staticmethod
    def get_all():
        """Get all students"""
        try:
            return list(Student.get_collection().find())
        except Exception:
            return list(_LOCAL_STUDENTS.values())
    
    @staticmethod
    def delete(student_id):
        """Delete a student"""
        try:
            return Student.get_collection().delete_one({'_id': ObjectId(student_id)})
        except Exception:
            _LOCAL_STUDENTS.pop(student_id, None)
            return type('Result', (), {'deleted_count': 1})()
