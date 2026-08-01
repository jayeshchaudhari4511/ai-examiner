import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load environment variables from .env file (only if it exists)
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    # In production, environment variables should be set directly
    load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_API_KEYS = [key.strip() for key in os.getenv('GEMINI_API_KEYS', '').split(',') if key.strip()]
    _upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
    UPLOAD_FOLDER = _upload_folder if os.path.isabs(_upload_folder) else os.path.join(BASE_DIR, _upload_folder)
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_URI_FALLBACK = os.getenv('MONGO_URI_FALLBACK')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'ai_examiner')  

    # Auth configuration
    JWT_SECRET = os.getenv('JWT_SECRET', 'dev_change_me')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    ACCESS_TOKEN_MINUTES = int(os.getenv('ACCESS_TOKEN_MINUTES', '30'))
    REFRESH_TOKEN_DAYS = int(os.getenv('REFRESH_TOKEN_DAYS', '7'))

    # SMTP configuration
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM = os.getenv('SMTP_FROM', SMTP_USER)
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
