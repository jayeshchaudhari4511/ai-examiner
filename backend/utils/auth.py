import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

ACCESS_TOKEN_MINUTES = int(os.getenv('ACCESS_TOKEN_MINUTES', '30'))
REFRESH_TOKEN_DAYS = int(os.getenv('REFRESH_TOKEN_DAYS', '7'))
JWT_SECRET = os.getenv('JWT_SECRET', 'dev_change_me')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def _create_token(payload: dict, expires_delta: timedelta) -> str:
    data = payload.copy()
    data['exp'] = datetime.utcnow() + expires_delta
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    return _create_token({'sub': user_id, 'role': role, 'type': 'access'}, timedelta(minutes=ACCESS_TOKEN_MINUTES))


def create_refresh_token(user_id: str, role: str) -> str:
    return _create_token({'sub': user_id, 'role': role, 'type': 'refresh'}, timedelta(days=REFRESH_TOKEN_DAYS))


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def require_auth(roles=None):
    roles = roles or []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid Authorization header'}), 401
            token = auth_header.split(' ', 1)[1]
            try:
                payload = decode_token(token)
                if payload.get('type') != 'access':
                    return jsonify({'error': 'Invalid token type'}), 401
                if roles and payload.get('role') not in roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                request.user = payload
            except Exception:
                return jsonify({'error': 'Invalid or expired token'}), 401
            return func(*args, **kwargs)
        return wrapper
    return decorator
