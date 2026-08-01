import os
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image
import numpy as np
import logging
import platform
import gc
import base64
from io import BytesIO
from uuid import uuid4
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Set Poppler path only for Windows development
POPPLER_PATH = None
if platform.system() == 'Windows':
    # Local development path
    POPPLER_PATH = r"C:\Users\Jayesh\poppler\poppler-23.08.0\Library\bin"

class PDFProcessor:
    _ocr_reader = None

    @classmethod
    def get_ocr_reader(cls):
        """Lazy-load EasyOCR reader to avoid heavy startup cost."""
        if cls._ocr_reader is None:
            try:
                import easyocr
            except Exception as e:
                raise Exception(f"EasyOCR is not available: {str(e)}")

            cls._ocr_reader = easyocr.Reader(['en'], gpu=False)
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
    def convert_pdf_to_images(pdf_path, max_pages=5):
        """Convert PDF to images for Gemini vision API (limited to first 5 pages)"""
        try:
            logger.info(f"Converting PDF to images: {pdf_path}")
            # Increased DPI to 100 for better text recognition (was 50)
            # Still efficient but much better quality for OCR
            if POPPLER_PATH:
                images = convert_from_path(pdf_path, dpi=100, poppler_path=POPPLER_PATH, last_page=max_pages)
            else:
                images = convert_from_path(pdf_path, dpi=100, last_page=max_pages)
            
            logger.info(f"Converted {len(images)} pages to images")
            return images
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise Exception(f"Error converting PDF to images: {str(e)}")
    
    @staticmethod
    def extract_text_from_images_via_gemini(images, gemini_service):
        """Use Gemini vision API to extract text from images (much faster than EasyOCR)"""
        try:
            logger.info(f"Extracting text from {len(images)} images using Gemini vision...")
            extracted_text = ""
            success_count = 0
            
            for idx, image in enumerate(images):
                try:
                    logger.info(f"Processing page {idx + 1}/{len(images)} with Gemini vision...")
                    
                    # Convert PIL image to bytes for Gemini
                    # Increased quality to 85 for better text recognition
                    img_byte_arr = BytesIO()
                    image.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
                    img_byte_arr.seek(0)
                    img_base64 = base64.standard_b64encode(img_byte_arr.getvalue()).decode()
                    
                    # Use Gemini vision to extract text (with key rotation support)
                    response = gemini_service.generate_content([
                        "Extract all text from this image. Include handwritten and typed text. Return ONLY the extracted text, nothing else.",
                        {
                            "mime_type": "image/jpeg",
                            "data": img_base64
                        }
                    ], expect_json=False)
                    
                    # Check if response is valid
                    if not response or not response.text:
                        logger.warning(f"Empty response from Gemini for page {idx + 1}")
                        page_text = "[No text detected]"
                    else:
                        page_text = response.text.strip()
                        if page_text and page_text != "[No text detected]":
                            success_count += 1
                    
                    extracted_text += f"\n--- Page {idx + 1} ---\n{page_text}\n"
                    
                    # Cleanup
                    del image
                    del img_byte_arr
                    gc.collect()
                    
                except Exception as page_error:
                    logger.warning(f"Error processing page {idx + 1}: {str(page_error)}")
                    extracted_text += f"\n--- Page {idx + 1} ---\n[Error: {str(page_error)}]\n"
                    gc.collect()
                    continue
            
            logger.info("Gemini vision extraction completed")
            if success_count == 0:
                raise Exception("Gemini vision OCR failed for all pages")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text via Gemini: {str(e)}")
            raise Exception(f"Error extracting text from images: {str(e)}")
    
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
        absolute_upload_folder = os.path.abspath(upload_folder)
        if not os.path.exists(absolute_upload_folder):
            os.makedirs(absolute_upload_folder)

        safe_name = secure_filename(file.filename or 'uploaded_file.pdf')
        unique_name = f"{uuid4().hex}_{safe_name}"

        file_path = os.path.join(absolute_upload_folder, unique_name)
        file.save(file_path)
        return file_path
