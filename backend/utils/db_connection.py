from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from config import Config
import logging
from urllib.parse import urlsplit, urlunsplit

logger = logging.getLogger(__name__)

class DatabaseConnection:
    _instance = None
    _client = None
    _db = None
    _connected = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Don't auto-connect on initialization
        pass

    def _sanitize_uri(self, uri):
        """Mask credentials before logging a MongoDB URI"""
        try:
            parsed = urlsplit(uri)
            if '@' not in parsed.netloc:
                return uri

            host_part = parsed.netloc.split('@', 1)[1]
            safe_netloc = f"***:***@{host_part}"
            return urlunsplit((parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment))
        except Exception:
            return "<invalid-uri>"

    def _get_candidate_uris(self):
        """Get primary and fallback MongoDB URIs, in order."""
        uris = []
        preferred = Config.MONGO_URI or ''
        fallback = Config.MONGO_URI_FALLBACK or ''

        if preferred and 'localhost' not in preferred.lower() and '127.0.0.1' not in preferred.lower():
            uris.append(preferred)
        elif preferred:
            uris.append(preferred)

        if fallback and fallback not in uris and 'localhost' not in fallback.lower() and '127.0.0.1' not in fallback.lower():
            uris.append(fallback)
        elif fallback:
            uris.append(fallback)

        return uris
    
    def connect(self):
        """Establish database connection with proper error handling"""
        if self._connected and self._client is not None:
            return self._db
            
        try:
            logger.info("Attempting to connect to MongoDB...")
            logger.info(f"Using MongoDB URI from config: {self._sanitize_uri(Config.MONGO_URI or '')}")
            
            # Validate MONGO_URI
            candidate_uris = self._get_candidate_uris()
            if not candidate_uris:
                raise ValueError("MONGO_URI (or MONGO_URI_FALLBACK) not found in environment variables")

            last_error = None
            selected_uri = None

            for uri in candidate_uris:
                try:
                    logger.info(f"Trying MongoDB URI: {self._sanitize_uri(uri)}")
                    client = MongoClient(
                        uri,
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=10000
                    )
                    client.admin.command('ping')
                    self._client = client
                    selected_uri = uri
                    break
                except Exception as conn_error:
                    last_error = conn_error
                    logger.warning(f"MongoDB connection attempt failed for URI {self._sanitize_uri(uri)}: {conn_error}")

            if self._client is None:
                raise last_error if last_error else ConnectionFailure("Could not connect using configured MongoDB URIs")
            
            # Get database name from config or URI
            db_name = getattr(Config, 'MONGO_DB_NAME', None)
            if not db_name:
                db_name = selected_uri.split('/')[-1].split('?')[0] if selected_uri else None
            if not db_name:
                db_name = 'ai_examiner'
            
            self._db = self._client[db_name]
            self._connected = True
            logger.info(f"Successfully connected to MongoDB database: {db_name}")
            
            # Create indexes
            self._create_indexes()
            
            return self._db
            
        except OperationFailure as e:
            logger.error(f"MongoDB Authentication Failed: {e}")
            logger.error("Please check:")
            logger.error("1. Username and password are correct")
            logger.error("2. Database user has proper permissions")
            logger.error("3. IP address is whitelisted in MongoDB Atlas (use 0.0.0.0/0 for all IPs)")
            raise Exception(f"Database authentication failed: {e}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            logger.error("Please check your internet connection and MongoDB URI")
            raise Exception(f"Database connection failed: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise Exception(f"Database connection error: {e}")
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Teachers collection indexes
            self._db.teachers.create_index("email", unique=True)
            
            # Students collection indexes
            self._db.students.create_index("email", unique=True)

            # Users collection indexes
            self._db.users.create_index("email", unique=True)
            self._db.users.create_index("role")
            self._db.users.create_index("status")
            self._db.users.create_index("subject_ids")

            # Subjects collection indexes
            self._db.subjects.create_index("code", unique=True)
            self._db.subjects.create_index("class")

            # Submissions collection indexes
            self._db.submissions.create_index("student_id")
            self._db.submissions.create_index("subject_id")
            self._db.submissions.create_index("created_at")
            
            # Evaluations collection indexes
            self._db.evaluations.create_index("student_id")
            self._db.evaluations.create_index("teacher_id")
            self._db.evaluations.create_index("subject_id")
            self._db.evaluations.create_index("submission_id")
            self._db.evaluations.create_index("created_at")
            self._db.evaluations.create_index([("created_at", -1)])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def get_db(self):
        """Get database instance, connecting if necessary"""
        if not self._connected or self._db is None:
            return self.connect()
        return self._db
    
    def get_collection(self, collection_name):
        """Get specific collection"""
        db = self.get_db()
        return db[collection_name]
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            logger.info("Database connection closed")

# Global database instance (lazy initialization)
db_connection = DatabaseConnection()

# Lazy database accessor
def get_database():
    """Get database instance with lazy connection"""
    return db_connection.get_db()

# For backward compatibility
db = None

try:
    db = db_connection.connect()
except Exception as e:
    logger.warning(f"Database not connected at startup: {e}")
    logger.warning("Database will be connected on first use")
