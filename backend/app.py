from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from utils.pdf_processor import PDFProcessor
from utils.gemini_service import GeminiService
from utils.db_connection import db, db_connection
from models.teacher import Teacher
from models.student import Student
from models.evaluation import Evaluation
from models.user import User
from models.subject import Subject
from models.submission import Submission
from utils.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, require_auth
from utils.email_service import send_email, build_reset_email
from bson import ObjectId
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DEV_DEMO_EMAIL = os.getenv('DEV_DEMO_EMAIL', 'admin@example.com')
DEV_DEMO_PASSWORD = os.getenv('DEV_DEMO_PASSWORD', 'admin123')
LOCAL_USERS = {}

# Configure CORS for both development and production
DEFAULT_CORS_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3001',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]


def normalize_origin(origin):
    return origin.rstrip('/') if origin else None


def build_allowed_origins():
    configured_origins = [
        normalize_origin(origin.strip())
        for origin in os.getenv('FRONTEND_URL', '').split(',')
        if origin.strip()
    ]
    return list(dict.fromkeys([
        *(normalize_origin(origin) for origin in DEFAULT_CORS_ORIGINS),
        *configured_origins,
    ]))


cors_origins = build_allowed_origins()

CORS(
    app,
    resources={r'/api/*': {'origins': cors_origins}},
    supports_credentials=True,
    allow_headers=['Content-Type', 'Authorization'],
    methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    vary_header=True,
)


@app.after_request
def apply_allowed_origin(response):
    origin = normalize_origin(request.headers.get('Origin'))
    if origin in cors_origins or request.headers.get('Origin') in cors_origins:
        response.headers['Access-Control-Allow-Origin'] = origin or request.headers.get('Origin')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Vary'] = 'Origin'
    return response

# Configuration
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_FILE_SIZE

# Initialize services
pdf_processor = PDFProcessor()
gemini_keys = Config.GEMINI_API_KEYS if Config.GEMINI_API_KEYS else [Config.GEMINI_API_KEY]
gemini_service = GeminiService(gemini_keys)


def ensure_admin_user():
    """Seed an admin account if none exists"""
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')
    admin_name = os.getenv('ADMIN_NAME', 'Admin')

    if not admin_email or not admin_password:
        return

    try:
        existing_admin = User.find_by_email(admin_email)
        if existing_admin:
            return

        User.create(
            name=admin_name,
            email=admin_email,
            password_hash=hash_password(admin_password),
            role='admin',
            status='active'
        )
        logger.info('Seeded admin account')
    except Exception as e:
        logger.warning(f'Skipping admin seeding because database is unavailable: {e}')


ensure_admin_user()

# Helper function to serialize MongoDB documents
def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        doc = doc.copy()
        for key, value in list(doc.items()):
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, list):
                doc[key] = [str(v) if isinstance(v, ObjectId) else v for v in value]
        if '_id' in doc and isinstance(doc['_id'], ObjectId):
            doc['_id'] = str(doc['_id'])
        return doc
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc


def resolve_submission_storage_path(storage_path):
    """Resolve submission file path for both absolute and legacy relative records"""
    if not storage_path:
        return None

    filename = os.path.basename(storage_path)
    candidates = []

    if os.path.isabs(storage_path):
        candidates.append(storage_path)

    candidates.extend([
        os.path.join(app.config['UPLOAD_FOLDER'], filename),
        os.path.join(os.path.dirname(__file__), 'uploads', filename),
    ])

    for candidate in candidates:
        normalized_candidate = os.path.abspath(candidate)
        if os.path.exists(normalized_candidate):
            return normalized_candidate

    return os.path.abspath(candidates[0]) if candidates else None

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - API info"""
    return jsonify({
        'message': 'AI Examiner API',
        'version': '1.0',
        'health_check': '/api/health'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_connection.get_db().command('ping')
        db_status = 'connected'
    except Exception as e:
        db_status = f'disconnected: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'message': 'AI Examiner API is running',
        'database': db_status
    })

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    """Register a new user (student or teacher)"""
    try:
        data = request.json or {}
        name = data.get('name')
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')
        role = data.get('role')
        roll_number = data.get('roll_number')
        class_name = data.get('class')
        subject_ids = data.get('subject_ids', [])

        if not name or not email or not password or role not in ['student', 'teacher']:
            return jsonify({'error': 'Name, email, password, and role are required'}), 400

        try:
            existing_user = User.find_by_email(email)
            if existing_user:
                return jsonify({'error': 'User with this email already exists'}), 400
        except Exception as db_error:
            existing_user = LOCAL_USERS.get(email)
            if existing_user:
                return jsonify({'error': 'User with this email already exists'}), 400
            logger.warning(f'Registration lookup failed; using local fallback: {db_error}')

        status = 'active'
        password_hash = hash_password(password)
        user = None
        try:
            user = User.create(
                name=name,
                email=email,
                password_hash=password_hash,
                role=role,
                roll_number=roll_number,
                class_name=class_name,
                subject_ids=subject_ids,
                status=status
            )
        except Exception as db_error:
            logger.warning(f'User creation failed; storing user locally: {db_error}')
            user = {
                '_id': f'local-user-{len(LOCAL_USERS) + 1}',
                'name': name,
                'email': email,
                'password_hash': password_hash,
                'role': role,
                'status': status,
                'roll_number': roll_number,
                'class': class_name,
                'subject_ids': subject_ids or [],
            }
            LOCAL_USERS[email] = user

        return jsonify({'success': True, 'user': serialize_doc(user)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login_user():
    """Login user and issue tokens"""
    try:
        data = request.json or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        user = None
        try:
            user = User.find_by_email(email)
        except Exception as db_error:
            logger.warning(f'Login lookup failed because the database is unavailable: {db_error}')

        if not user:
            user = LOCAL_USERS.get(email)

        if not user and email == DEV_DEMO_EMAIL.lower() and password == DEV_DEMO_PASSWORD:
            user = {
                '_id': 'local-demo-user',
                'name': 'Local Demo Admin',
                'email': DEV_DEMO_EMAIL.lower(),
                'password_hash': hash_password(DEV_DEMO_PASSWORD),
                'role': 'admin',
                'status': 'active'
            }

        if not user or not verify_password(password, user.get('password_hash', '')):
            return jsonify({'error': 'Invalid credentials'}), 401

        access_token = create_access_token(str(user['_id']), user['role'])
        refresh_token = create_refresh_token(str(user['_id']), user['role'])

        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': serialize_doc(user)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Issue a new access token from refresh token"""
    try:
        data = request.json or {}
        token = data.get('refresh_token')
        if not token:
            return jsonify({'error': 'Refresh token required'}), 400

        try:
            payload = decode_token(token)
        except Exception:
            return jsonify({'error': 'Invalid refresh token'}), 401

        if payload.get('type') != 'refresh':
            return jsonify({'error': 'Invalid token type'}), 401

        user = User.find_by_id(payload.get('sub'))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        access_token = create_access_token(str(user['_id']), user['role'])
        return jsonify({'success': True, 'access_token': access_token})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/request-reset', methods=['POST'])
def request_password_reset():
    """Send password reset email"""
    try:
        data = request.json or {}
        email = data.get('email')
        if not email:
            return jsonify({'error': 'Email required'}), 400

        user = User.find_by_email(email)
        if not user:
            return jsonify({'success': True, 'message': 'If account exists, email sent'})

        reset_token = User.create_reset_token(str(user['_id']))
        email_payload = build_reset_email(user['email'], reset_token)
        send_email(email_payload['to'], email_payload['subject'], email_payload['html'])

        return jsonify({'success': True, 'message': 'Reset email sent'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.json or {}
        token = data.get('token')
        new_password = data.get('new_password')
        if not token or not new_password:
            return jsonify({'error': 'Token and new password required'}), 400

        user = User.find_by_reset_token(token)
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 400

        User.update(str(user['_id']), {
            'password_hash': hash_password(new_password),
            'reset_token': None,
            'reset_expires': None
        })

        return jsonify({'success': True, 'message': 'Password updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/me', methods=['GET'])
@require_auth()
def get_current_user():
    """Get current user profile"""
    try:
        user_id = request.user.get('sub')
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'success': True, 'user': serialize_doc(user)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/teachers/pending', methods=['GET'])
@require_auth(['admin'])
def get_pending_teachers():
    """List pending teachers for approval"""
    try:
        pending = list(User.get_collection().find({'role': 'teacher', 'status': 'pending'}))
        return jsonify({'success': True, 'teachers': serialize_doc(pending)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/teachers/<teacher_id>/approve', methods=['POST'])
@require_auth(['admin'])
def approve_teacher(teacher_id):
    """Approve teacher account and assign subjects"""
    try:
        data = request.json or {}
        subject_ids = data.get('subject_ids', [])
        User.update(teacher_id, {'status': 'active', 'subject_ids': subject_ids})
        return jsonify({'success': True, 'message': 'Teacher approved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== TEACHER ROUTES ====================

@app.route('/api/teachers', methods=['POST'])
def create_teacher():
    """Create a new teacher"""
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject')
        
        if not name or not email:
            return jsonify({'error': 'Name and email are required'}), 400
        
        # Check if teacher already exists
        existing = Teacher.find_by_email(email) or User.find_by_email(email)
        if existing:
            return jsonify({'error': 'Teacher with this email already exists'}), 400
        
        teacher = Teacher.create(name, email, subject)
        return jsonify({
            'success': True,
            'teacher': serialize_doc(teacher)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers/<teacher_id>', methods=['GET'])
def get_teacher(teacher_id):
    """Get teacher by ID"""
    try:
        teacher = Teacher.find_by_id(teacher_id)
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404
        
        return jsonify({
            'success': True,
            'teacher': serialize_doc(teacher)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers', methods=['GET'])
def get_all_teachers():
    """Get all teachers"""
    try:
        legacy_teachers = Teacher.get_all()
        role_teachers = User.get_by_role('teacher')

        teachers_by_email = {}

        for teacher in legacy_teachers:
            email = (teacher.get('email') or '').lower()
            teachers_by_email[email] = {
                '_id': teacher.get('_id'),
                'name': teacher.get('name'),
                'email': teacher.get('email'),
                'subject': teacher.get('subject'),
                'created_at': teacher.get('created_at'),
                'updated_at': teacher.get('updated_at')
            }

        for teacher in role_teachers:
            email = (teacher.get('email') or '').lower()
            if email not in teachers_by_email:
                teachers_by_email[email] = {
                    '_id': teacher.get('_id'),
                    'name': teacher.get('name'),
                    'email': teacher.get('email'),
                    'subject': None,
                    'created_at': teacher.get('created_at'),
                    'updated_at': teacher.get('updated_at')
                }

        teachers = list(teachers_by_email.values())
        return jsonify({
            'success': True,
            'teachers': serialize_doc(teachers),
            'count': len(teachers)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== STUDENT ROUTES ====================

@app.route('/api/students', methods=['POST'])
def create_student():
    """Create a new student"""
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        roll_number = data.get('roll_number')
        class_name = data.get('class')
        
        if not name or not email:
            return jsonify({'error': 'Name and email are required'}), 400
        
        # Check if student already exists
        existing = Student.find_by_email(email) or User.find_by_email(email)
        if existing:
            return jsonify({'error': 'Student with this email already exists'}), 400
        
        student = Student.create(name, email, roll_number, class_name)
        return jsonify({
            'success': True,
            'student': serialize_doc(student)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<student_id>', methods=['GET'])
def get_student(student_id):
    """Get student by ID"""
    try:
        student = Student.find_by_id(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        return jsonify({
            'success': True,
            'student': serialize_doc(student)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_all_students():
    """Get all students"""
    try:
        legacy_students = Student.get_all()
        role_students = User.get_by_role('student')

        students_by_email = {}

        for student in legacy_students:
            email = (student.get('email') or '').lower()
            students_by_email[email] = {
                '_id': student.get('_id'),
                'name': student.get('name'),
                'email': student.get('email'),
                'roll_number': student.get('roll_number'),
                'rollNumber': student.get('roll_number'),
                'class': student.get('class'),
                'created_at': student.get('created_at'),
                'updated_at': student.get('updated_at')
            }

        for student in role_students:
            email = (student.get('email') or '').lower()
            if email not in students_by_email:
                roll_number = student.get('roll_number')
                students_by_email[email] = {
                    '_id': student.get('_id'),
                    'name': student.get('name'),
                    'email': student.get('email'),
                    'roll_number': roll_number,
                    'rollNumber': roll_number,
                    'class': student.get('class'),
                    'created_at': student.get('created_at'),
                    'updated_at': student.get('updated_at')
                }

        students = list(students_by_email.values())
        return jsonify({
            'success': True,
            'students': serialize_doc(students),
            'count': len(students)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<student_id>/statistics', methods=['GET'])
def get_student_statistics(student_id):
    """Get statistics for a student"""
    try:
        stats = Evaluation.get_student_statistics(student_id)
        if not stats:
            return jsonify({
                'success': True,
                'statistics': {
                    'total_evaluations': 0,
                    'average_marks': 0,
                    'average_percentage': 0
                }
            })
        
        return jsonify({
            'success': True,
            'statistics': serialize_doc(stats)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers/<teacher_id>', methods=['DELETE'])
def delete_teacher(teacher_id):
    """Delete a teacher"""
    try:
        deleted = False
        try:
            if Teacher.delete(teacher_id).deleted_count > 0:
                deleted = True
        except Exception:
            pass

        try:
            user = User.find_by_id(teacher_id)
            if user and user.get('role') == 'teacher':
                User.delete(teacher_id)
                deleted = True
        except Exception:
            pass

        if not deleted:
            return jsonify({'error': 'Teacher not found'}), 404

        return jsonify({'success': True, 'message': 'Teacher deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting teacher: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student"""
    try:
        deleted = False
        try:
            if Student.delete(student_id).deleted_count > 0:
                deleted = True
        except Exception:
            pass

        try:
            user = User.find_by_id(student_id)
            if user and user.get('role') == 'student':
                User.delete(student_id)
                deleted = True
        except Exception:
            pass

        if not deleted:
            return jsonify({'error': 'Student not found'}), 404

        return jsonify({'success': True, 'message': 'Student deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== SUBJECT ROUTES ====================

@app.route('/api/subjects', methods=['POST'])
@require_auth(['admin'])
def create_subject():
    """Create a subject"""
    try:
        data = request.json or {}
        name = data.get('name')
        code = data.get('code')
        class_name = data.get('class')
        if not name or not code or not class_name:
            return jsonify({'error': 'Name, code, and class are required'}), 400

        subject = Subject.create(name, code, class_name, request.user.get('sub'))
        return jsonify({'success': True, 'subject': serialize_doc(subject)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/subjects', methods=['GET'])
def list_subjects():
    """List subjects"""
    try:
        subjects = Subject.get_all()
        return jsonify({'success': True, 'subjects': serialize_doc(subjects)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== SUBMISSION ROUTES ====================

@app.route('/api/submissions', methods=['POST'])
@require_auth(['student'])
def create_submission():
    """Student uploads an answer sheet for a subject"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        subject_id = request.form.get('subject_id')
        if not subject_id:
            return jsonify({'error': 'Subject is required'}), 400

        file = request.files['file']
        if not Config.allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        file_path = pdf_processor.save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
        submission = Submission.create(
            student_id=request.user.get('sub'),
            subject_id=subject_id,
            filename=file.filename,
            storage_path=file_path
        )

        return jsonify({'success': True, 'submission': serialize_doc(submission)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/submissions/student', methods=['GET'])
@require_auth(['student'])
def list_student_submissions():
    """List submissions for current student"""
    try:
        submissions = Submission.find_by_student(request.user.get('sub'))
        return jsonify({'success': True, 'submissions': serialize_doc(submissions)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/submissions/teacher', methods=['GET'])
@require_auth(['teacher'])
def list_teacher_submissions():
    """List submissions for a subject (teacher scope)"""
    try:
        subject_id = request.args.get('subject_id')
        if not subject_id:
            return jsonify({'error': 'Subject is required'}), 400

        teacher = User.find_by_id(request.user.get('sub'))
        teacher_subjects = teacher.get('subject_ids', []) if teacher else []
        if subject_id not in teacher_subjects:
            return jsonify({'error': 'Subject not assigned to teacher'}), 403

        submissions = Submission.find_by_subject(subject_id)
        for submission in submissions:
            resolved_path = resolve_submission_storage_path(submission.get('storage_path'))
            file_exists = bool(resolved_path and os.path.exists(resolved_path))
            submission['file_exists'] = file_exists
            submission['can_evaluate'] = submission.get('status') != 'evaluated' and file_exists
            if not file_exists:
                submission['file_missing_reason'] = 'Answer sheet file is missing. Ask the student to re-upload.'
        return jsonify({'success': True, 'submissions': serialize_doc(submissions)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/submissions/<submission_id>/evaluate', methods=['POST'])
@require_auth(['teacher'])
def evaluate_submission(submission_id):
    """Teacher evaluates a submission"""
    try:
        submission = Submission.find_by_id(submission_id)
        if not submission:
            return jsonify({'error': 'Submission not found'}), 404

        teacher = User.find_by_id(request.user.get('sub'))
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404

        subject_id = submission.get('subject_id')
        if subject_id not in teacher.get('subject_ids', []):
            return jsonify({'error': 'Subject not assigned to teacher'}), 403

        model_answer = request.form.get('model_answer')
        max_marks = request.form.get('max_marks')
        question = request.form.get('question', '')

        if not model_answer or not max_marks:
            return jsonify({'error': 'Model answer and max marks are required'}), 400

        try:
            max_marks = int(max_marks)
        except ValueError:
            return jsonify({'error': 'Invalid max marks value'}), 400

        student = User.find_by_id(submission.get('student_id'))
        student_name = student.get('name', 'Unknown') if student else 'Unknown'
        student_rollno = student.get('roll_number', 'N/A') if student else 'N/A'

        teacher_name = teacher.get('name', 'Unknown')

        resolved_storage_path = resolve_submission_storage_path(submission.get('storage_path'))

        if not resolved_storage_path or not os.path.exists(resolved_storage_path):
            Submission.update(submission_id, {'status': 'file_missing'})
            return jsonify({'error': 'Submission file not found. Please ask the student to re-upload the answer sheet.'}), 404

        student_text = pdf_processor.extract_text_from_pdf(resolved_storage_path)
        if len(student_text.strip()) < 100:
            images = pdf_processor.convert_pdf_to_images(resolved_storage_path, max_pages=5)
            try:
                student_text = pdf_processor.extract_text_from_images_via_gemini(images, gemini_service)
            except Exception as ocr_error:
                logger.warning(f"Gemini OCR unavailable, falling back to EasyOCR: {str(ocr_error)}")
                student_text = pdf_processor.extract_text_from_images(images)

        evaluation_result = gemini_service.evaluate_answer(
            student_text,
            model_answer,
            max_marks,
            question
        )

        evaluation_doc = Evaluation.create(
            teacher_id=request.user.get('sub'),
            student_id=submission.get('student_id'),
            question=question,
            model_answer=model_answer,
            student_answer=submission.get('filename'),
            extracted_text=student_text,
            max_marks=max_marks,
            evaluation_result=evaluation_result,
            teacher_name=teacher_name,
            student_name=student_name,
            student_rollno=student_rollno,
            subject_id=subject_id,
            submission_id=submission_id
        )

        Submission.update(submission_id, {'status': 'evaluated'})

        evaluation_result['extracted_text'] = student_text
        evaluation_result['evaluation_id'] = str(evaluation_doc['_id'])

        return jsonify({'success': True, 'evaluation': evaluation_result})
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== EVALUATION ROUTES ====================

@app.route('/api/upload-model-answer', methods=['POST'])
def upload_model_answer():
    """Handle model answer upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not Config.allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF allowed.'}), 400
        
        # Save file
        file_path = pdf_processor.save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
        
        # Extract text
        text = pdf_processor.extract_text_from_pdf(file_path)
        
        # Clean up
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'model_answer': text,
            'message': 'Model answer uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluate-answer', methods=['POST'])
def evaluate_answer():
    """Evaluate student answer against model answer and store in database"""
    try:
        # Validate inputs
        if 'student_file' not in request.files:
            return jsonify({'error': 'No student file provided'}), 400
        
        student_file = request.files['student_file']
        model_answer = request.form.get('model_answer')
        max_marks = request.form.get('max_marks')
        question = request.form.get('question', '')
        teacher_id = request.form.get('teacher_id')
        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')
        submission_id = request.form.get('submission_id')
        
        if not model_answer or not max_marks:
            return jsonify({'error': 'Model answer and max marks are required'}), 400
        
        if not Config.allowed_file(student_file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Convert max_marks to integer
        try:
            max_marks = int(max_marks)
        except ValueError:
            return jsonify({'error': 'Invalid max marks value'}), 400
        
        # Fetch teacher and student info for storing in evaluation
        teacher_name = 'Unknown'
        student_name = 'Unknown'
        student_rollno = 'N/A'
        
        if teacher_id:
            teacher = Teacher.find_by_id(teacher_id)
            if teacher:
                teacher_name = teacher.get('name', 'Unknown')
            else:
                teacher_user = User.find_by_id(teacher_id)
                if teacher_user:
                    teacher_name = teacher_user.get('name', 'Unknown')
        
        if student_id:
            student = Student.find_by_id(student_id)
            if student:
                student_name = student.get('name', 'Unknown')
                student_rollno = student.get('roll_number', 'N/A')
        
        # Save student file
        student_file_path = pdf_processor.save_uploaded_file(
            student_file, 
            app.config['UPLOAD_FOLDER']
        )
        
        # Try text extraction first (instant)
        logger.info("=== Starting text extraction from student PDF ===")
        try:
            logger.info("Attempting direct PDF text extraction...")
            student_text = pdf_processor.extract_text_from_pdf(student_file_path)
            logger.info(f"Extracted {len(student_text)} characters from PDF")
            
            if len(student_text.strip()) < 100:
                # Not enough text extracted, use Gemini vision
                logger.info("Insufficient text from extraction, using Gemini vision API...")
                logger.info("Converting PDF to images...")
                images = pdf_processor.convert_pdf_to_images(student_file_path, max_pages=5)
                logger.info(f"Converted to {len(images)} images, starting OCR...")
                try:
                    student_text = pdf_processor.extract_text_from_images_via_gemini(images, gemini_service)
                except Exception as ocr_error:
                    logger.warning(f"Gemini OCR unavailable, falling back to EasyOCR: {str(ocr_error)}")
                    student_text = pdf_processor.extract_text_from_images(images)
                logger.info(f"OCR completed, extracted {len(student_text)} characters")
        except Exception as extract_error:
            logger.error(f"Text extraction failed: {str(extract_error)}")
            logger.info("Falling back to OCR from rendered images...")
            try:
                images = pdf_processor.convert_pdf_to_images(student_file_path, max_pages=5)
                logger.info(f"Converted to {len(images)} images for OCR")
                try:
                    student_text = pdf_processor.extract_text_from_images_via_gemini(images, gemini_service)
                except Exception as ocr_error:
                    logger.warning(f"Gemini OCR unavailable, falling back to EasyOCR: {str(ocr_error)}")
                    student_text = pdf_processor.extract_text_from_images(images)
                logger.info(f"Fallback OCR completed, extracted {len(student_text)} characters")
            except Exception as ocr_error:
                logger.error(f"OCR also failed: {str(ocr_error)}")
                raise Exception(f"Failed to extract text from PDF: {str(ocr_error)}")
        
        # Validate extracted text
        if not student_text or len(student_text.strip()) < 10:
            raise Exception("Could not extract sufficient text from student PDF")
        
        logger.info("=== Starting Gemini evaluation ===")
        # Evaluate using Gemini
        evaluation_result = gemini_service.evaluate_answer(
            student_text, 
            model_answer, 
            max_marks,
            question
        )
        logger.info("=== Evaluation completed successfully ===")
        
        # Store evaluation in database
        evaluation_doc = Evaluation.create(
            teacher_id=teacher_id,
            student_id=student_id,
            question=question,
            model_answer=model_answer,
            student_answer=student_file.filename,
            extracted_text=student_text,
            max_marks=max_marks,
            evaluation_result=evaluation_result,
            teacher_name=teacher_name,
            student_name=student_name,
            student_rollno=student_rollno,
            subject_id=subject_id,
            submission_id=submission_id
        )
        
        # Add extracted text to response
        evaluation_result['extracted_text'] = student_text
        evaluation_result['evaluation_id'] = str(evaluation_doc['_id'])
        
        # Clean up
        os.remove(student_file_path)
        
        return jsonify({
            'success': True,
            'evaluation': evaluation_result
        })
        
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluations', methods=['GET'])
def get_all_evaluations():
    """Get all evaluations"""
    try:
        evaluations = Evaluation.get_all()
        if not evaluations:
            return jsonify([])
        
        return jsonify([serialize_doc(e) for e in evaluations])
    except Exception as e:
        logger.error(f"Error fetching evaluations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluations/<evaluation_id>', methods=['GET'])
def get_evaluation(evaluation_id):
    """Get evaluation by ID"""
    try:
        evaluation = Evaluation.find_by_id(evaluation_id)
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        return jsonify({
            'success': True,
            'evaluation': serialize_doc(evaluation)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluations/student/<student_id>', methods=['GET'])
def get_student_evaluations(student_id):
    """Get all evaluations for a student"""
    try:
        limit = request.args.get('limit', 10, type=int)
        evaluations = Evaluation.find_by_student(student_id, limit)
        
        return jsonify({
            'success': True,
            'evaluations': serialize_doc(evaluations),
            'count': len(evaluations)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/me/evaluations', methods=['GET'])
@require_auth(['student', 'teacher'])
def get_my_evaluations():
    """Get evaluations for the logged-in student or teacher"""
    try:
        limit = request.args.get('limit', 10, type=int)
        if request.user.get('role') == 'student':
            evaluations = Evaluation.find_by_student(request.user.get('sub'), limit)
        else:
            evaluations = Evaluation.find_by_teacher(request.user.get('sub'), limit)

        return jsonify({'success': True, 'evaluations': serialize_doc(evaluations)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluations/teacher/<teacher_id>', methods=['GET'])
def get_teacher_evaluations(teacher_id):
    """Get all evaluations by a teacher"""
    try:
        limit = request.args.get('limit', 10, type=int)
        evaluations = Evaluation.find_by_teacher(teacher_id, limit)
        
        return jsonify({
            'success': True,
            'evaluations': serialize_doc(evaluations),
            'count': len(evaluations)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluations/recent', methods=['GET'])
def get_recent_evaluations():
    """Get recent evaluations"""
    try:
        limit = request.args.get('limit', 20, type=int)
        evaluations = Evaluation.get_recent_evaluations(limit)
        
        return jsonify({
            'success': True,
            'evaluations': serialize_doc(evaluations),
            'count': len(evaluations)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluations/<evaluation_id>', methods=['DELETE'])
def delete_evaluation(evaluation_id):
    """Delete an evaluation"""
    try:
        result = Evaluation.delete(evaluation_id)
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Evaluation deleted successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ocr-only', methods=['POST'])
def ocr_only():
    """Extract text from handwritten PDF without evaluation"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not Config.allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save and process file
        file_path = pdf_processor.save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
        extracted_text = pdf_processor.extract_text_from_pdf(file_path)
        
        # Clean up
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'extracted_text': extracted_text
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create uploads folder if it doesn't exist
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)

    try:
        logger.info('Starting Flask application...')
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    finally:
        db_connection.close()
