import os
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image
import tempfile
import easyocr
import numpy as np
import logging
import platform
import gc

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
        """Convert PDF pages to images for OCR - limit to first 10 pages"""
        try:
            logger.info(f"Converting PDF to images: {pdf_path}")
            # Reduced DPI to 75 for memory efficiency
            # Limit to first 10 pages to avoid memory issues
            if POPPLER_PATH:
                all_images = convert_from_path(pdf_path, dpi=75, poppler_path=POPPLER_PATH, last_page=10)
            else:
                all_images = convert_from_path(pdf_path, dpi=75, last_page=10)
            
            logger.info(f"Converted {len(all_images)} pages to images (limited to 10)")
            return all_images
        except Exception as e:
            raise Exception(f"Error converting PDF to images: {str(e)}")
    
    @classmethod
    def extract_text_from_images(cls, images):
        """Extract text from images using EasyOCR with memory optimization"""
        try:
            logger.info(f"Extracting text from {len(images)} images...")
            reader = cls.get_ocr_reader()
            extracted_text = ""
            
            for idx, image in enumerate(images):
                try:
                    logger.info(f"Processing page {idx + 1}/{len(images)}...")
                    
                    # Resize image to 40% to save memory
                    new_width = max(int(image.width * 0.4), 400)
                    new_height = int(image.height * 0.4)
                    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Convert PIL Image to numpy array for EasyOCR
                    img_array = np.array(resized_image)
                    
                    # Perform OCR
                    results = reader.readtext(img_array, detail=0, paragraph=False)
                    
                    # Combine results
                    page_text = "\n".join(results) if results else "[No text detected]"
                    extracted_text += f"\n--- Page {idx + 1} ---\n{page_text}\n"
                    
                    # Explicit memory cleanup
                    del resized_image
                    del img_array
                    del image
                    gc.collect()
                    
                except Exception as page_error:
                    logger.warning(f"Error processing page {idx + 1}: {str(page_error)}")
                    extracted_text += f"\n--- Page {idx + 1} ---\n[Error processing page]\n"
                    gc.collect()
                    continue
            
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
