from datetime import datetime
from bson import ObjectId
from utils.db_connection import db_connection

_LOCAL_TEACHERS = {}

class Teacher:
    @staticmethod
    def get_collection():
        """Get teachers collection with lazy connection"""
        return db_connection.get_collection('teachers')
    
    @staticmethod
    def create(name, email, subject=None):
        """Create a new teacher"""
        teacher = {
            'name': name,
            'email': email,
            'subject': subject,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        try:
            result = Teacher.get_collection().insert_one(teacher)
            teacher['_id'] = result.inserted_id
        except Exception:
            teacher['_id'] = f'local-teacher-{len(_LOCAL_TEACHERS) + 1}'
            _LOCAL_TEACHERS[teacher['_id']] = teacher
        return teacher
    
    @staticmethod
    def find_by_email(email):
        """Find teacher by email"""
        try:
            return Teacher.get_collection().find_one({'email': email})
        except Exception:
            return next((t for t in _LOCAL_TEACHERS.values() if (t.get('email') or '').lower() == (email or '').lower()), None)
    
    @staticmethod
    def find_by_id(teacher_id):
        """Find teacher by ID"""
        try:
            return Teacher.get_collection().find_one({'_id': ObjectId(teacher_id)})
        except Exception:
            return _LOCAL_TEACHERS.get(teacher_id)
    
    @staticmethod
    def update(teacher_id, data):
        """Update teacher information"""
        data['updated_at'] = datetime.utcnow()
        return Teacher.get_collection().update_one(
            {'_id': ObjectId(teacher_id)},
            {'$set': data}
        )
    
    @staticmethod
    def get_all():
        """Get all teachers"""
        try:
            return list(Teacher.get_collection().find())
        except Exception:
            return list(_LOCAL_TEACHERS.values())
    
    @staticmethod
    def delete(teacher_id):
        """Delete a teacher"""
        try:
            return Teacher.get_collection().delete_one({'_id': ObjectId(teacher_id)})
        except Exception:
            _LOCAL_TEACHERS.pop(teacher_id, None)
            return type('Result', (), {'deleted_count': 1})()
