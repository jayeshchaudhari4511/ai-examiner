from datetime import datetime, timedelta
from bson import ObjectId
from utils.db_connection import db_connection
import secrets
import hashlib

_LOCAL_USERS = {}

class User:
    @staticmethod
    def get_collection():
        return db_connection.get_collection('users')

    @staticmethod
    def create(name, email, password_hash, role, roll_number=None, class_name=None, subject_ids=None, status='active'):
        user = {
            'name': name,
            'email': email.lower(),
            'password_hash': password_hash,
            'role': role,
            'status': status,
            'roll_number': roll_number,
            'class': class_name,
            'subject_ids': subject_ids or [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        try:
            result = User.get_collection().insert_one(user)
            user['_id'] = result.inserted_id
        except Exception:
            user['_id'] = f'local-user-{len(_LOCAL_USERS) + 1}'
            _LOCAL_USERS[user['_id']] = user
        return user

    @staticmethod
    def find_by_email(email):
        try:
            return User.get_collection().find_one({'email': email.lower()})
        except Exception:
            return next((u for u in _LOCAL_USERS.values() if (u.get('email') or '').lower() == (email or '').lower()), None)

    @staticmethod
    def find_by_id(user_id):
        try:
            return User.get_collection().find_one({'_id': ObjectId(user_id)})
        except Exception:
            return _LOCAL_USERS.get(user_id)

    @staticmethod
    def update(user_id, data):
        data['updated_at'] = datetime.utcnow()
        try:
            return User.get_collection().update_one({'_id': ObjectId(user_id)}, {'$set': data})
        except Exception:
            if user_id in _LOCAL_USERS:
                _LOCAL_USERS[user_id].update(data)
            return type('Result', (), {'modified_count': 1})()

    @staticmethod
    def get_by_role(role):
        try:
            return list(User.get_collection().find({'role': role}))
        except Exception:
            return [u for u in _LOCAL_USERS.values() if u.get('role') == role]

    @staticmethod
    def delete(user_id):
        try:
            return User.get_collection().delete_one({'_id': ObjectId(user_id)})
        except Exception:
            _LOCAL_USERS.pop(user_id, None)
            return type('Result', (), {'deleted_count': 1})()

    @staticmethod
    def create_reset_token(user_id, expires_minutes=30):
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        expiry = datetime.utcnow() + timedelta(minutes=expires_minutes)
        User.update(user_id, {'reset_token': token_hash, 'reset_expires': expiry})
        return token

    @staticmethod
    def find_by_reset_token(token):
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        user = User.get_collection().find_one({'reset_token': token_hash})
        if not user:
            return None
        if user.get('reset_expires') and user['reset_expires'] < datetime.utcnow():
            return None
        return user
