from datetime import datetime
from bson import ObjectId
from utils.db_connection import db_connection

class Subject:
    @staticmethod
    def get_collection():
        return db_connection.get_collection('subjects')

    @staticmethod
    def create(name, code, class_name, created_by):
        subject = {
            'name': name,
            'code': code,
            'class': class_name,
            'created_by': created_by,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = Subject.get_collection().insert_one(subject)
        subject['_id'] = result.inserted_id
        return subject

    @staticmethod
    def get_all():
        return list(Subject.get_collection().find().sort('name', 1))

    @staticmethod
    def find_by_id(subject_id):
        return Subject.get_collection().find_one({'_id': ObjectId(subject_id)})

    @staticmethod
    def delete(subject_id):
        return Subject.get_collection().delete_one({'_id': ObjectId(subject_id)})
