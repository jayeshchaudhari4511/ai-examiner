import os
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image
import tempfile
import easyocr
import numpy as np
import logging
import platform

logger = logging.getLogger(__name__)

# Set Poppler path only for Windows development
POPPLER_PATH = None
if platform.system() == 'Windows':
    # Local development path
    POPPLER_PATH = r"C:\Users\Jayesh\poppler\poppler-23.08.0\Library\bin"

class PDFProcessor:
    # Initialize EasyOCR reader (will be created once and reused)
    _ocr_reader = None
    
    @classmethod
    def get_ocr_reader(cls):
        """Get or create EasyOCR reader instance"""
        if cls._ocr_reader is None:
            logger.info("Initializing EasyOCR reader...")
            cls._ocr_reader = easyocr.Reader(['en'], gpu=False)
            logger.info("EasyOCR reader initialized")
        return cls._ocr_reader
    @staticmethod
    def extract_text_from_pdf(pdf_path):
        """Extract plain text from PDF (for model answers)"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    @staticmethod
    def convert_pdf_to_images(pdf_path):
        """Convert PDF pages to images for OCR"""
        try:
            logger.info(f"Converting PDF to images: {pdf_path}")
            # Reduced DPI from 150 to 100 to save memory
            # On Linux/Railway, poppler-utils is in PATH, no need to specify poppler_path
            if POPPLER_PATH:
                images = convert_from_path(pdf_path, dpi=100, poppler_path=POPPLER_PATH)
            else:
                images = convert_from_path(pdf_path, dpi=100)
            logger.info(f"Converted {len(images)} pages to images")
            return images
        except Exception as e:
            raise Exception(f"Error converting PDF to images: {str(e)}")
    
    @classmethod
    def extract_text_from_images(cls, images):
        """Extract text from images using EasyOCR"""
        try:
            logger.info(f"Extracting text from {len(images)} images...")
            reader = cls.get_ocr_reader()
            extracted_text = ""
            
            for idx, image in enumerate(images):
                logger.info(f"Processing page {idx + 1}/{len(images)}...")
                
                # Resize image to 50% to save memory (still readable for OCR)
                resized_image = image.resize((image.width // 2, image.height // 2), Image.Resampling.LANCZOS)
                
                # Convert PIL Image to numpy array for EasyOCR
                img_array = np.array(resized_image)
                
                # Perform OCR with optimized parameters for speed
                results = reader.readtext(img_array, detail=0, paragraph=False)
                
                # Combine results
                page_text = "\n".join(results) if results else "[No text detected]"
                extracted_text += f"\n--- Page {idx + 1} ---\n{page_text}\n"
            
            logger.info("Text extraction completed")
            return extracted_text.strip()
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise Exception(f"Error extracting text from images: {str(e)}")
    
    @staticmethod
    def save_uploaded_file(file, upload_folder):
        """Save uploaded file and return path"""
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)
        return file_path
