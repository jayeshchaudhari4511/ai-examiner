import google.generativeai as genai
import json
import re
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_keys):
        if isinstance(api_keys, str):
            api_keys = [api_keys]

        self.api_keys = [key.strip() for key in (api_keys or []) if isinstance(key, str) and key.strip()]
        if not self.api_keys:
            raise ValueError('At least one Gemini API key is required')

        self.model_name = 'gemini-3.1-flash-lite-preview'
        self._last_key_index = 0

    def generate_content(self, content, expect_json=False):
        """Generate content with safe key handling and key rotation."""
        total_keys = len(self.api_keys)
        last_error = None

        for offset in range(total_keys):
            key_index = (self._last_key_index + offset) % total_keys
            current_key = self.api_keys[key_index]

            try:
                genai.configure(api_key=current_key)
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(content)
                self._last_key_index = key_index
                return response
            except Exception as e:
                error_text = str(e).lower()
                last_error = e
                if '429' in error_text or 'quota' in error_text or 'rate' in error_text or 'resource_exhausted' in error_text:
                    logger.warning(f'Gemini key {key_index + 1}/{total_keys} quota/rate limited. Trying next key...')
                    continue
                if 'api_key_invalid' in error_text or 'api key expired' in error_text or 'invalid api key' in error_text:
                    logger.warning(f'Gemini key {key_index + 1}/{total_keys} invalid/expired. Trying next key...')
                    continue
                raise

        if last_error:
            raise Exception(str(last_error))
        raise Exception('Gemini request failed without a specific error.')
    
    def evaluate_answer(self, student_answer, model_answer, max_marks, question=None):
        """Evaluate student answer against model answer"""
        question_context = f"\n\nQuestion: {question}" if question else ""
        
        logger.info("Starting answer evaluation...")
        
        prompt = f"""
You are an expert AI examiner. Evaluate the student's answer against the model answer.

{question_context}

MODEL ANSWER:
{model_answer}

STUDENT'S ANSWER:
{student_answer}

MAXIMUM MARKS: {max_marks}

Provide a comprehensive evaluation in the following JSON format:
{{
    "marks_awarded": <number between 0 and {max_marks}>,
    "percentage": <percentage score>,
    "strengths": [
        "List specific correct points and concepts the student covered well",
        "Include at least 3-5 points if applicable"
    ],
    "missing_points": [
        "List key concepts or details that were missing or incorrect",
        "Include at least 2-3 points if applicable"
    ],
    "feedback": "Provide detailed constructive feedback (2-3 sentences) explaining the evaluation, what was done well, and areas for improvement",
    "grade": "<A+/A/B+/B/C/D/F based on percentage>"
}}

Be fair, constructive, and specific in your evaluation. Consider:
- Conceptual understanding
- Accuracy of information
- Completeness of the answer
- Clarity and structure

Return ONLY valid JSON, no additional text.
"""
        
        try:
            logger.info("Calling Gemini API for evaluation...")
            response = self.generate_content(prompt, expect_json=True)
            logger.info("Received response from Gemini API")
            result_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)

            first_brace = result_text.find('{')
            last_brace = result_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace >= first_brace:
                result_text = result_text[first_brace:last_brace + 1]
            
            # Parse JSON
            evaluation = json.loads(result_text)
            
            # Validate and set defaults
            evaluation.setdefault('marks_awarded', 0)
            evaluation.setdefault('percentage', 0)
            evaluation.setdefault('strengths', [])
            evaluation.setdefault('missing_points', [])
            evaluation.setdefault('feedback', 'No feedback provided')
            evaluation.setdefault('grade', 'N/A')
            
            return evaluation
            
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return {
                "marks_awarded": 0,
                "percentage": 0,
                "strengths": ["Unable to parse evaluation results"],
                "missing_points": ["Error in evaluation process"],
                "feedback": f"Evaluation error: {str(e)}. Raw response: {result_text[:200]}",
                "grade": "N/A"
            }
        except Exception as e:
            return {
                "marks_awarded": 0,
                "percentage": 0,
                "strengths": [],
                "missing_points": [],
                "feedback": f"Error during evaluation: {str(e)}",
                "grade": "N/A"
            }
