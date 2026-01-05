# 🎓 AI Examiner - Automated Answer Evaluation System

An intelligent examination system that uses AI to automatically evaluate student answers against model answers, providing detailed feedback, marks, and suggestions for improvement.

[![React](https://img.shields.io/badge/React-19.2.3-blue.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://www.mongodb.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI-orange.svg)](https://ai.google.dev/)

## 📋 Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Functionality
- 🤖 **AI-Powered Evaluation**: Uses Google Gemini AI for intelligent answer assessment
- 📄 **PDF Support**: Upload and process PDF documents for model and student answers
- 🔍 **OCR Integration**: Extract handwritten text from images using EasyOCR
- 📊 **Detailed Analysis**: Get comprehensive feedback with strengths and improvement areas
- 📈 **Grading System**: Automatic grade assignment based on percentage scores

### Management Features
- 👨‍🏫 **Teacher Management**: Add, view, and manage teacher profiles
- 👨‍🎓 **Student Management**: Maintain student records with roll numbers and classes
- 📝 **Evaluation History**: Track all evaluations with filtering and search capabilities
- 📥 **Export to PDF**: Download evaluation reports in professional PDF format
- 🗑️ **Delete Evaluations**: Remove unwanted evaluation records

### User Interface
- 🎨 **Modern UI**: Beautiful, responsive design with gradient themes
- 🌙 **Dark Mode**: Eye-friendly dark theme interface
- 📱 **Responsive**: Works seamlessly on desktop, tablet, and mobile devices
- ⚡ **Real-time Updates**: Live feedback during evaluation process
- 🔍 **Advanced Filters**: Filter evaluations by student, teacher, date, and more

## 🛠️ Tech Stack

### Frontend
- **React 19.2.3** - UI framework
- **React Router DOM** - Navigation and routing
- **Axios** - HTTP client for API requests
- **React Icons** - Icon library
- **CSS3** - Modern styling with animations

### Backend
- **Flask** - Python web framework
- **MongoDB** - NoSQL database
- **Google Gemini AI** - AI model for evaluation
- **EasyOCR** - Optical character recognition
- **PyMongo** - MongoDB driver for Python
- **pdf2image** - PDF to image conversion
- **Flask-CORS** - Cross-origin resource sharing

### AI & Processing
- **Google Generative AI (Gemini)** - Natural language processing and evaluation
- **EasyOCR** - Handwritten text extraction
- **Poppler** - PDF processing utilities

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   React     │────────▶│   Flask API  │────────▶│   MongoDB   │
│   Frontend  │◀────────│   Backend    │◀────────│   Database  │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  Gemini AI   │
                        │  + EasyOCR   │
                        └──────────────┘
```

## 📦 Installation

### Prerequisites
- Node.js (v16 or higher)
- Python 3.8+
- MongoDB (local or cloud instance)
- Google Gemini API Key
- Poppler (for PDF processing)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ai-examiner.git
cd ai-examiner
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirement.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### 4. Install Poppler (for PDF processing)

**Windows:**
- Download from: https://github.com/oschwartz10612/poppler-windows/releases
- Add to PATH environment variable

**macOS:**
```bash
brew install poppler
```

**Linux:**
```bash
sudo apt-get install poppler-utils
```

## ⚙️ Configuration

### Backend Configuration

Update `config.py` file in the `backend` directory:

```python
import os

class Config:
    # MongoDB Configuration
    MONGO_URI = "mongodb://localhost:27017/"
    DATABASE_NAME = "ai_examiner"
    
    # Google Gemini API
    GEMINI_API_KEY = "your-gemini-api-key-here"
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
```

### Frontend Configuration

Update API URL in `frontend/src/services/api.js` if needed:

```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

## 🚀 Usage

### Starting the Backend Server

```bash
cd backend
python app.py
```

The backend server will start at `http://localhost:5000`

### Starting the Frontend Development Server

```bash
cd frontend
npm start
```

The frontend will start at `http://localhost:3000`

### Using the Application

1. **Add Teachers and Students**
   - Navigate to Management page
   - Add teacher profiles with name, email, and subject
   - Add student profiles with name, email, roll number, and class

2. **Evaluate Answers**
   - Go to Evaluate page
   - Upload model answer PDF or paste text
   - Select teacher and student
   - Upload student answer PDF
   - Enter maximum marks
   - Click "Evaluate" to get AI-powered results

3. **View History**
   - Access Evaluation History page
   - Filter by student name, roll number, teacher, or date
   - View detailed evaluations
   - Download reports as PDF
   - Delete old evaluations

4. **Dashboard**
   - View statistics of teachers and students
   - Quick access to all features

## 📁 Project Structure

```
ai-examiner/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration settings
│   ├── requirement.txt        # Python dependencies
│   ├── models/
│   │   ├── evaluation.py      # Evaluation data model
│   │   ├── student.py         # Student data model
│   │   └── teacher.py         # Teacher data model
│   └── utils/
│       ├── db_connection.py   # MongoDB connection
│       ├── gemini_service.py  # AI evaluation service
│       ├── pdf_processor.py   # PDF processing utilities
│       └── init.py
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js             # Main React component
│   │   ├── App.css            # Global styles
│   │   ├── components/
│   │   │   └── Navigation.jsx # Navigation bar
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx  # Dashboard page
│   │   │   ├── Evaluate.jsx   # Evaluation page
│   │   │   ├── EvaluationHistory.jsx
│   │   │   ├── Management.jsx # Management page
│   │   │   └── Results.jsx    # Results page
│   │   ├── services/
│   │   │   └── api.js         # API service layer
│   │   └── index.js
│   └── package.json           # Node dependencies
│
└── README.md                  # This file
```

## 🔌 API Endpoints

### Teachers
- `POST /api/teachers` - Create new teacher
- `GET /api/teachers` - Get all teachers
- `GET /api/teachers/:id` - Get teacher by ID
- `DELETE /api/teachers/:id` - Delete teacher

### Students
- `POST /api/students` - Create new student
- `GET /api/students` - Get all students
- `GET /api/students/:id` - Get student by ID
- `DELETE /api/students/:id` - Delete student

### Evaluations
- `POST /api/upload-model-answer` - Upload model answer PDF
- `POST /api/evaluate-answer` - Evaluate student answer
- `GET /api/evaluations` - Get all evaluations
- `GET /api/evaluations/:id` - Get evaluation by ID
- `DELETE /api/evaluations/:id` - Delete evaluation

### Health Check
- `GET /api/health` - Check API and database status

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Google Gemini AI for powerful natural language processing
- MongoDB for reliable data storage
- React community for excellent documentation
- All contributors and testers

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Batch evaluation of multiple students
- [ ] Analytics dashboard with charts
- [ ] Email notifications
- [ ] Mobile app
- [ ] LMS integration
- [ ] Support for more file formats

## ⚠️ Known Issues

- Large PDF files (>10MB) may take longer to process
- Handwritten text recognition accuracy depends on handwriting clarity
- Requires stable internet connection for AI evaluation

---

Made with ❤️ by the AI Examiner Team

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
