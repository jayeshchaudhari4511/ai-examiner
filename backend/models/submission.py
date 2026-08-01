from datetime import datetime
import os
from bson import ObjectId
from utils.db_connection import db_connection

class Submission:
    @staticmethod
    def get_collection():
        return db_connection.get_collection('submissions')

    @staticmethod
    def create(student_id, subject_id, filename, storage_path):
        normalized_path = os.path.abspath(storage_path)
        submission = {
            'student_id': student_id,
            'subject_id': subject_id,
            'filename': filename,
            'storage_path': normalized_path,
            'status': 'submitted',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = Submission.get_collection().insert_one(submission)
        submission['_id'] = result.inserted_id
        return submission

    @staticmethod
    def find_by_id(submission_id):
        return Submission.get_collection().find_one({'_id': ObjectId(submission_id)})

    @staticmethod
    def find_by_student(student_id, limit=20):
        return list(Submission.get_collection().find({'student_id': student_id})
                   .sort('created_at', -1)
                   .limit(limit))

    @staticmethod
    def find_by_subject(subject_id, limit=50):
        return list(Submission.get_collection().find({'subject_id': subject_id})
                   .sort('created_at', -1)
                   .limit(limit))

    @staticmethod
    def update(submission_id, data):
        data['updated_at'] = datetime.utcnow()
        return Submission.get_collection().update_one(
            {'_id': ObjectId(submission_id)},
            {'$set': data}
        )
