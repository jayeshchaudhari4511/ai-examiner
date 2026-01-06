import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'ai_examiner')  
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
