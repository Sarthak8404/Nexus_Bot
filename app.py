#!/usr/bin/env python3
"""
Flask Web Application for BusinessAI Platform
Handles file upload, text extraction, web scraping, and AI-powered data extraction
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Tuple, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
import docx
from werkzeug.utils import secure_filename
import tempfile
import ssl
import urllib3
import logging
from datetime import datetime
from supabase.client import create_client, Client
from chroma_utils import store_data_in_chroma, query_chroma
import threading
import time

# Setup logging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG level
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)  # Force override environment variables with .env file

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Get API key and configure
api_key = os.getenv("GEMINI_API_KEY")
logger.debug(f"API Key loaded: {'Present' if api_key else 'Not found'}")
if api_key:
    logger.debug(f"API Key length: {len(api_key)}")
    logger.debug(f"API Key starts with: {api_key[:5]}")

if not api_key:
    logger.error("GEMINI_API_KEY not found in environment variables")
    logger.error("Please make sure your .env file exists and contains GEMINI_API_KEY")
    logger.error("Current working directory: " + os.getcwd())
    logger.error("Looking for .env file in: " + os.path.abspath(".env"))
else:
    try:
        # Configure the API key
        genai.configure(api_key=api_key)
        # Test the configuration
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Successfully configured Gemini API")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {str(e)}")

# Disable SSL warnings for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

# Telegram bot settings storage (in production, use database)
telegram_settings = {}

# Track processed message IDs to avoid duplicates
processed_message_ids = set()

class TelegramBot:
    """Telegram bot handler for customer service."""
    
    def __init__(self, token: str, user_id: str):
        self.token = token
        self.user_id = user_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.webhook_url = None
        
    def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook URL for the bot."""
        try:
            response = requests.post(
                f"{self.base_url}/setWebhook",
                json={"url": webhook_url}
            )
            if response.status_code == 200:
                self.webhook_url = webhook_url
                logger.info(f"Webhook set successfully for user {self.user_id}")
                return True
            else:
                logger.error(f"Failed to set webhook: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error setting webhook: {str(e)}")
            return False
    
    def delete_webhook(self) -> bool:
        """Delete webhook for the bot."""
        try:
            response = requests.post(f"{self.base_url}/deleteWebhook")
            if response.status_code == 200:
                logger.info(f"Webhook deleted successfully for user {self.user_id}")
                return True
            else:
                logger.error(f"Failed to delete webhook: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting webhook: {str(e)}")
            return False
    
    def send_message(self, chat_id: str, text: str) -> bool:
        """Send message to Telegram chat."""
        try:
            logger.info(f"=== SENDING TELEGRAM MESSAGE ===")
            logger.info(f"Chat ID: {chat_id}")
            logger.info(f"Text: {text[:100]}...")
            logger.info(f"Bot URL: {self.base_url}")
            
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response text: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Message sent successfully to chat {chat_id}")
                    return True
                else:
                    logger.error(f"Telegram API error: {result.get('description')}")
                    return False
            else:
                logger.error(f"HTTP error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    def get_me(self) -> Optional[Dict]:
        """Get bot information."""
        try:
            response = requests.get(f"{self.base_url}/getMe")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get bot info: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting bot info: {str(e)}")
            return None

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class SimpleWebScraper:
    """Simple web scraper using requests + BeautifulSoup."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Disable SSL verification for corporate networks
        self.session.verify = False
    
    def scrape_url(self, url: str) -> str:
        """Scrape content from URL using requests + BeautifulSoup."""
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            logger.info(f"Successfully scraped {len(text)} characters from {url}")
            return text
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return ""

class TextExtractor:
    """Text extraction from various file formats."""
    
    @staticmethod
    def extract_from_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            return f"Error reading PDF: {str(e)}"
    
    @staticmethod
    def extract_from_docx(file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            logger.info(f"Extracted {len(text)} characters from DOCX")
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading DOCX: {str(e)}")
            return f"Error reading DOCX: {str(e)}"
    
    @staticmethod
    def extract_from_txt(file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read().strip()
                logger.info(f"Extracted {len(text)} characters from TXT")
                return text
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read().strip()
                    logger.info(f"Extracted {len(text)} characters from TXT (latin-1)")
                    return text
            except Exception as e:
                logger.error(f"Error reading TXT with latin-1: {str(e)}")
                return f"Error reading TXT: {str(e)}"
        except Exception as e:
            logger.error(f"Error reading TXT: {str(e)}")
            return f"Error reading TXT: {str(e)}"
    
    @classmethod
    def extract_text(cls, file_path: str, file_extension: str) -> str:
        """Extract text based on file extension."""
        if file_extension.lower() == 'pdf':
            return cls.extract_from_pdf(file_path)
        elif file_extension.lower() in ['docx', 'doc']:
            return cls.extract_from_docx(file_path)
        elif file_extension.lower() == 'txt':
            return cls.extract_from_txt(file_path)
        else:
            return "Unsupported file format"

class DataProcessor:
    """Main data processing class with AI extraction capabilities."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        logger.debug(f"DataProcessor API Key loaded: {'Present' if self.api_key else 'Not found'}")
        if self.api_key:
            logger.debug(f"DataProcessor API Key length: {len(self.api_key)}")
            logger.debug(f"DataProcessor API Key starts with: {self.api_key[:5]}")
        
        self.web_scraper = SimpleWebScraper()
        self.text_extractor = TextExtractor()
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
        else:
            try:
                # Configure the API key
                genai.configure(api_key=self.api_key)
                # Test the configuration
                model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Successfully configured Gemini API in DataProcessor")
            except Exception as e:
                logger.error(f"Failed to configure Gemini API in DataProcessor: {str(e)}")
    
    def get_content_type_options(self) -> Dict[str, str]:
        """Get available content type options."""
        return {
            "products": "🛍️ Products (e-commerce items)",
            "services": "🔧 Services (service offerings)",
            "contact": "📞 Contact Information",
            "about": "🏢 About/Company Info",
            "faq": "❓ FAQs",
            "policies": "📋 Policies (Terms, Privacy)",
            "general": "📄 General Content"
        }
    
    def get_extraction_prompts(self, content_type: str) -> Tuple[str, str]:
        """Get system and user prompts based on content type."""
        
        system_message = """You are an expert data extraction specialist. Extract structured information 
                          from the provided content and format it as clean JSON. Be thorough, precise, and maintain 
                          original language if content is in a foreign language. Always return valid JSON."""
        
        prompts = {
            "products": """Extract product information. For each product include:
- name: Product name (required)
- description: Product description (required) 
- price: Price with currency (required)
- imageUrl: Image URL if available
- availability: Stock status
- category: Product category
- sku: Product SKU/ID if available

Format as JSON array of product objects. Extract ALL products found.
If information is missing, use empty string.

Content to analyze:
""",
            
            "services": """Extract service information. For each service include:
- name: Service name (required)
- description: Service description (required)
- price: Service price/cost if available
- duration: Service duration if mentioned
- category: Service category
- features: List of service features/benefits

Format as JSON array of service objects. Extract ALL services found.
If information is missing, use empty string or empty array.

Content to analyze:
""",
            
            "contact": """Extract contact information including:
- email: All email addresses found
- phone: All phone numbers found  
- address: Complete physical addresses
- hours: Business hours
- socialMedia: Social media links/handles
- website: Website URLs
- contactPerson: Contact person names if available

Format as JSON object with these fields.
Use arrays for multiple entries, empty string/array if not found.

Content to analyze:
""",
            
            "about": """Extract company/organization information:
- companyName: Organization name
- history: Company history/founding info
- mission: Mission statement
- vision: Vision statement  
- values: Company values/principles
- team: Team/leadership information
- achievements: Awards/achievements
- location: Company locations

Format as JSON object. Include detailed information for each field.
Use empty string if information not found.

Content to analyze:
""",
            
            "faq": """Extract FAQ information. For each FAQ include:
- question: The question text (required)
- answer: Complete answer text (required)
- category: Question category if available
- tags: Relevant tags if available

Format as JSON array of FAQ objects. Extract ALL FAQs found.
If information is missing, use empty string or empty array.

Content to analyze:
""",
            
            "policies": """Extract policy documents. For each policy include:
- title: Policy title (e.g., "Privacy Policy", "Terms of Service")
- content: Full policy content
- lastUpdated: Last update date if available
- version: Policy version if available
- category: Policy category

Format as JSON array of policy objects. Extract ALL policies found.
If information is missing, use empty string.

Content to analyze:
""",
            
            "general": """Extract general structured information from the content.
Identify and extract key information in a logical JSON structure.
Use appropriate field names based on the content type discovered.

Format as JSON object or array depending on content structure.

Content to analyze:
"""
        }
        
        user_message = prompts.get(content_type, prompts["general"])
        return system_message, user_message
    
    def extract_structured_data(self, content: str, content_type: str) -> Tuple[Any, Optional[Dict], Optional[float]]:
        """Extract structured data using LLM."""
        if not self.api_key:
            return {"error": "GEMINI_API_KEY not configured"}, None, None
            
        try:
            logger.info(f"Starting AI extraction for content type: {content_type}")
            logger.debug(f"Using API key: {self.api_key[:5]}...")
            
            # Get appropriate prompts
            system_message, user_message = self.get_extraction_prompts(content_type)
            
            # Limit content length to avoid token limits
            content_preview = content[:15000] if len(content) > 15000 else content
            
            try:
                # Create the model
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Create the chat
                chat = model.start_chat(history=[])
                
                # Send the message
                response = chat.send_message(f"{system_message}\n\n{user_message}\n\n{content_preview}")
                
                # Get the response text
                llm_response = response.text
                
                # For now, we'll use placeholder values for tokens and cost
                token_info = {
                    "input_tokens": len(content_preview) // 4,  # Rough estimate
                    "output_tokens": len(llm_response) // 4,    # Rough estimate
                    "total_tokens": (len(content_preview) + len(llm_response)) // 4
                }
                
                # Parse JSON from response
                structured_data = self.parse_json_response(llm_response, content_type)
                
                logger.info(f"AI extraction completed. Tokens: {token_info['total_tokens']}")
                
                return structured_data, token_info, 0.0  # Cost is not available with direct API
                
            except Exception as e:
                logger.error(f"Gemini API call failed: {str(e)}")
                return {"error": f"Gemini API call failed: {str(e)}"}, None, None
            
        except Exception as e:
            logger.error(f"AI processing failed: {str(e)}")
            return {"error": f"AI processing failed: {str(e)}"}, None, None
    
    def parse_json_response(self, response: str, content_type: str) -> Any:
        """Parse JSON from LLM response with fallback handling."""
        import re
        
        try:
            # Method 1: Extract from markdown code blocks
            json_pattern = r"```(?:json)?\s*(.*?)\s*```"
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            if matches:
                for match in matches:
                    try:
                        return json.loads(match.strip())
                    except json.JSONDecodeError:
                        continue
            
            # Method 2: Find JSON objects/arrays
            # Try array first
            array_match = re.search(r'\[.*\]', response, re.DOTALL)
            if array_match:
                try:
                    return json.loads(array_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # Try object
            object_match = re.search(r'\{.*\}', response, re.DOTALL)
            if object_match:
                try:
                    return json.loads(object_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # Method 3: Fallback structure
            return self.create_fallback_structure(response, content_type)
            
        except Exception:
            return self.create_fallback_structure(response, content_type)
    
    def create_fallback_structure(self, response: str, content_type: str) -> Any:
        """Create fallback data structure when JSON parsing fails."""
        content_preview = response[:500] + "..." if len(response) > 500 else response
        
        fallback_structures = {
            "products": [{"name": "Extracted Product", "description": content_preview, "price": ""}],
            "services": [{"name": "Extracted Service", "description": content_preview, "price": ""}],
            "contact": {"email": "", "phone": "", "address": "", "info": content_preview},
            "about": {"companyName": "", "description": content_preview},
            "faq": [{"question": "Extracted FAQ", "answer": content_preview}],
            "policies": [{"title": "Extracted Policy", "content": content_preview}],
            "general": {"content": content_preview}
        }
        
        return fallback_structures.get(content_type, {"content": content_preview})
    
    def clean_data(self, data: Any) -> Any:
        """Clean extracted data by removing excess whitespace."""
        if isinstance(data, list):
            return [self.clean_data(item) for item in data]
        elif isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if isinstance(value, str):
                    cleaned[key] = ' '.join(value.split())
                else:
                    cleaned[key] = self.clean_data(value)
            return cleaned
        elif isinstance(data, str):
            return ' '.join(data.split())
        else:
            return data
    
    def scrape_website(self, url: str, content_type: str) -> Dict[str, Any]:
        """Main scraping function."""
        logger.info(f"Processing website: {url} with content type: {content_type}")
        
        # Fetch content
        content = self.web_scraper.scrape_url(url)
        if not content:
            return {
                "url": url,
                "content_type": content_type,
                "source": "website",
                "error": "Failed to fetch website content",
                "data": [],
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract structured data
        structured_data, token_info, cost = self.extract_structured_data(content, content_type)
        
        if isinstance(structured_data, dict) and "error" in structured_data:
            return {
                "url": url,
                "content_type": content_type,
                "source": "website",
                "error": structured_data["error"],
                "data": [],
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Clean data
        cleaned_data = self.clean_data(structured_data)
        
        # Prepare result
        result = {
            "url": url,
            "content_type": content_type,
            "source": "website",
            "data": cleaned_data,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "input_tokens": token_info["input_tokens"] if token_info else 0,
                "output_tokens": token_info["output_tokens"] if token_info else 0,
                "total_tokens": token_info["total_tokens"] if token_info else 0,
                "cost_usd": cost if cost else 0,
                "items_extracted": len(cleaned_data) if isinstance(cleaned_data, list) else 1,
                "content_length": len(content)
            }
        }
        
        logger.info(f"Website processing completed successfully for {url}")
        return result
    
    def process_file(self, file_path: str, filename: str, content_type: str) -> Dict[str, Any]:
        """Process uploaded file and extract structured data."""
        try:
            logger.info(f"Processing file: {filename} with content type: {content_type}")
            
            # Get file extension
            file_extension = filename.rsplit('.', 1)[1].lower()
            
            # Extract text from file
            extracted_text = self.text_extractor.extract_text(file_path, file_extension)
            
            if not extracted_text or extracted_text.startswith("Error"):
                return {
                    "filename": filename,
                    "content_type": content_type,
                    "source": "file",
                    "error": extracted_text or "Failed to extract text from file",
                    "data": [],
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Extract structured data
            structured_data, token_info, cost = self.extract_structured_data(extracted_text, content_type)
            
            if isinstance(structured_data, dict) and "error" in structured_data:
                return {
                    "filename": filename,
                    "content_type": content_type,
                    "source": "file",
                    "error": structured_data["error"],
                    "data": [],
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Clean data
            cleaned_data = self.clean_data(structured_data)
            
            # Prepare result
            result = {
                "filename": filename,
                "content_type": content_type,
                "source": "file",
                "data": cleaned_data,
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "stats": {
                    "input_tokens": token_info["input_tokens"] if token_info else 0,
                    "output_tokens": token_info["output_tokens"] if token_info else 0,
                    "total_tokens": token_info["total_tokens"] if token_info else 0,
                    "cost_usd": cost if cost else 0,
                    "items_extracted": len(cleaned_data) if isinstance(cleaned_data, list) else 1,
                    "file_type": file_extension.upper(),
                    "text_length": len(extracted_text)
                }
            }
            
            logger.info(f"File processing completed successfully for {filename}")
            return result
            
        except Exception as e:
            logger.error(f"File processing failed for {filename}: {str(e)}")
            return {
                "filename": filename,
                "content_type": content_type,
                "source": "file",
                "error": f"File processing failed: {str(e)}",
                "data": [],
                "success": False,
                "timestamp": datetime.now().isoformat()
            }

# Initialize the processor
processor = DataProcessor()

# API Routes

@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        "status": "running",
        "message": "BusinessAI Platform Backend",
        "version": "1.0.0",
        "endpoints": ["/api/scrape", "/api/upload", "/api/content-types"]
    })

@app.route('/api/scrape', methods=['POST'])
def scrape_api():
    """API endpoint for website scraping and AI extraction."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        content_type = data.get('content_type', '').strip()
        
        # Validate input
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        if not content_type:
            return jsonify({"error": "Content type is required"}), 400
        
        if content_type not in processor.get_content_type_options():
            return jsonify({"error": "Invalid content type"}), 400
        
        result = processor.scrape_website(url, content_type)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Scrape API error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """API endpoint for file upload and processing."""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        content_type = request.form.get('content_type', '').strip()
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not content_type:
            return jsonify({"error": "Content type is required"}), 400
        
        if content_type not in processor.get_content_type_options():
            return jsonify({"error": "Invalid content type"}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                "error": f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.rsplit('.', 1)[1].lower()}") as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Process the file
            result = processor.process_file(temp_file_path, filename, content_type)
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Upload API error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/content-types', methods=['GET'])
def get_content_types():
    """Get available content types."""
    return jsonify(processor.get_content_type_options())

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with system status."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_key_configured": bool(processor.api_key),
        "supported_file_types": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
    })

@app.route('/api/save', methods=['POST'])
def save_data():
    """API endpoint for saving extracted data to database."""
    try:
        data = request.get_json()
        logger.debug(f"Received save request with data: {json.dumps(data, indent=2)}")
        
        # Validate input
        if not data:
            logger.error("No data provided in request")
            return jsonify({"error": "No data provided"}), 400
            
        # Extract required fields
        content_type = data.get('content_type')
        source = data.get('source')  # 'website' or 'file'
        extracted_data = data.get('data')
        
        if not all([content_type, source, extracted_data]):
            missing_fields = []
            if not content_type: missing_fields.append('content_type')
            if not source: missing_fields.append('source')
            if not extracted_data: missing_fields.append('data')
            logger.error(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
            
        # Prepare data for Supabase
        record = {
            'content_type': content_type,
            'source': source,
            'data': extracted_data,
            'created_at': datetime.now().isoformat(),
            'url': data.get('url') if source == 'website' else None,
            'filename': data.get('filename') if source == 'file' else None,
            'stats': data.get('stats', {})
        }
        
        logger.debug(f"Prepared record for Supabase: {json.dumps(record, indent=2)}")
        
        # Save to Supabase
        try:
            result = supabase.table('extracted_data').insert(record).execute()
            logger.info(f"Successfully saved data to Supabase: {json.dumps(result.data, indent=2)}")
            
            return jsonify({
                "success": True,
                "message": "Data saved successfully",
                "record_id": result.data[0]['id'] if result.data else None
            }), 200
            
        except Exception as e:
            logger.error(f"Supabase error: {str(e)}")
            logger.error(f"Failed record: {json.dumps(record, indent=2)}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Save API error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    """API endpoint for retrieving saved data."""
    try:
        # Query the extracted_data table with proper ordering
        response = supabase.table('extracted_data').select('*').order('created_at', desc=True).execute()
        
        # Check if response has data
        if not response.data:
            logger.info("No data found in database")
            return jsonify([])
            
        # Process the data to ensure it's in the correct format
        processed_data = []
        for item in response.data:
            try:
                # Ensure data field is properly formatted
                data = item.get('data', [])
                if not isinstance(data, list):
                    data = [data] if data else []
                
                processed_item = {
                    'id': item.get('id'),
                    'content_type': item.get('content_type'),
                    'source': item.get('source'),
                    'data': data,
                    'url': item.get('url'),
                    'filename': item.get('filename'),
                    'stats': item.get('stats', {}),
                    'created_at': item.get('created_at')
                }
                processed_data.append(processed_item)
            except Exception as e:
                logger.error(f"Error processing item {item.get('id')}: {str(e)}")
                continue
            
        logger.info(f"Successfully retrieved {len(processed_data)} records")
        return jsonify(processed_data)
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def delete_data():
    """API endpoint for deleting saved data."""
    try:
        data = request.json
        record_id = data.get('id')
        
        if not record_id:
            return jsonify({'error': 'Record ID is required'}), 400
            
        # Delete the specific record from extracted_data table
        response = supabase.table('extracted_data').delete().eq('id', record_id).execute()
        
        if not response.data:
            return jsonify({'error': 'Record not found'}), 404
            
        return jsonify({
            'success': True,
            'message': 'Data deleted successfully',
            'deleted_id': record_id
        })
    except Exception as e:
        logger.error(f"Error deleting data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/store-chroma', methods=['POST'])
def store_chroma():
    try:
        data = request.json.get('data', [])
        user_id = request.json.get('user_id')
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400

        success = store_data_in_chroma(data, user_id)
        if success:
            return jsonify({'message': 'Data successfully stored in ChromaDB'}), 200
        else:
            return jsonify({'error': 'Failed to store data in ChromaDB'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chat functionality using ChromaDB."""
    try:
        data = request.get_json()
        message = data.get('message')
        user_id = data.get('user_id')
        
        logger.info(f"Chat request received - Message: {message[:100]}..., User ID: {user_id}")
        
        if not message:
            logger.error("No message provided in chat request")
            return jsonify({"error": "No message provided"}), 400
            
        if not user_id:
            logger.error("No user ID provided in chat request")
            return jsonify({"error": "User ID is required"}), 400
            
        # Check if GEMINI_API_KEY is configured
        if not os.environ.get("GEMINI_API_KEY"):
            logger.error("GEMINI_API_KEY not configured")
            return jsonify({
                "error": "AI model is not properly configured. Please contact your administrator to set up the GEMINI_API_KEY."
            }), 500
            
        # Get relevant context from ChromaDB
        try:
            logger.info(f"Querying ChromaDB for user {user_id} with message: {message[:100]}...")
            # Query ChromaDB for relevant context with more results
            results = query_chroma(message, user_id, n_results=10)  # Increased from 5 to 10
            
            logger.info(f"ChromaDB query results: {results}")
            
            if not results or not results.get('documents'):
                logger.warning(f"No results found in ChromaDB for user {user_id}")
                return jsonify({
                    "response": "Hi! I'm having trouble finding specific information about that. Could you try:\n\n1. Rephrasing your question (e.g., 'Do you have chocolate brownies?' instead of 'brownies')\n2. Asking about a specific product category (like 'tea cakes' or 'brownies')\n3. Or just ask me about our general product offerings! I'm here to help! 😊"
                })
            
            # Extract relevant context from results
            context = []
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                if doc:  # Ensure document is not None
                    try:
                        # Try to parse the document as JSON for better formatting
                        parsed_doc = json.loads(doc)
                        # Add metadata to the document for better context
                        parsed_doc['metadata'] = metadata
                        context.append(json.dumps(parsed_doc, indent=2))
                    except json.JSONDecodeError:
                        # If not JSON, use as is
                        context.append(doc)
            
            logger.info(f"Extracted {len(context)} context items")
            
            # If no valid context found, return a default message
            if not context:
                logger.warning(f"No valid context found in ChromaDB results for user {user_id}")
                return jsonify({
                    "response": "Hi! I'm having trouble finding specific information about that. Could you try:\n\n1. Rephrasing your question (e.g., 'Do you have chocolate brownies?' instead of 'brownies')\n2. Asking about a specific product category (like 'tea cakes' or 'brownies')\n3. Or just ask me about our general product offerings! I'm here to help! 😊"
                })
            
            # Generate response using the context
            try:
                logger.info(f"Generating response using Gemini API for user {user_id}")
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""You are a friendly and knowledgeable customer service representative for a bakery business. Your role is to help customers with their inquiries about products, pricing, and services.

Context from the bakery's product database:
{chr(10).join(context)}

Customer's question: {message}

Please respond as a helpful customer service representative who:
1. **Speaks in a warm, friendly, and conversational tone** - like you're talking to a friend
2. **Gives SHORT, CONCISE answers** - keep responses brief and to the point
3. **Directly answers the customer's question** using the product information available
4. **Provides specific details** about products, prices, and features when asked
5. **Uses natural, everyday language** - avoid overly formal or technical business jargon
6. **Shows enthusiasm** about the products
7. **Mention specific product names, prices, and descriptions** from the data when relevant
8. **Be proactive** - if someone asks about one product, briefly suggest 1-2 related items
9. **Keep responses under 3-4 sentences** unless the customer asks for detailed information

**Response Style Guidelines:**
- Start with a friendly greeting or acknowledgment
- Use "we" and "our" to show you're representing the bakery
- Include specific prices and product names from the data
- Keep it brief and conversational
- Use emojis sparingly (1-2 max per response)

**Example short responses:**
- "Hi! Yes, we have the Overload Brownie for ₹120 - it's packed with rich dark chocolate! 🍫"
- "Our Mava Cake is ₹310 and it's one of our most popular items!"
- "We have several brownie options starting at ₹110. Would you like me to tell you about our eggless varieties?"

Remember: Keep responses short, friendly, and informative!"""

                response = model.generate_content(prompt)
                logger.info(f"Successfully generated response for user {user_id}")
                
                return jsonify({
                    "response": response.text
                })
            except Exception as e:
                logger.error(f"Gemini API error: {str(e)}")
                return jsonify({
                    "error": "Failed to generate response from AI model. Please try again later."
                }), 500
                
        except Exception as e:
            logger.error(f"ChromaDB query error: {str(e)}")
            return jsonify({
                "error": "Failed to retrieve context from database. Please make sure you've stored some data first."
            }), 500
            
    except Exception as e:
        logger.error(f"Chat API error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/delete-chroma', methods=['POST'])
def delete_chroma():
    """API endpoint for deleting user data from ChromaDB."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
            
        success = delete_user_data(user_id)
        if success:
            return jsonify({"message": "User data successfully deleted from ChromaDB"}), 200
        else:
            return jsonify({"error": "Failed to delete user data from ChromaDB"}), 500
            
    except Exception as e:
        logger.error(f"Delete ChromaDB error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/data/<id>', methods=['PUT'])
def update_data(id):
    """API endpoint for updating saved data."""
    try:
        data = request.get_json()
        logger.debug(f"Received update request for ID {id} with data: {json.dumps(data, indent=2)}")
        
        # Validate input
        if not data:
            logger.error("No data provided in request")
            return jsonify({"error": "No data provided"}), 400
            
        # Extract required fields
        content_type = data.get('content_type')
        extracted_data = data.get('data')
        
        if not all([content_type, extracted_data]):
            missing_fields = []
            if not content_type: missing_fields.append('content_type')
            if not extracted_data: missing_fields.append('data')
            logger.error(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
            
        # Prepare data for Supabase update
        update_data = {
            'content_type': content_type,
            'data': extracted_data,
            'updated_at': datetime.now().isoformat()
        }
        
        logger.debug(f"Prepared update data for Supabase: {json.dumps(update_data, indent=2)}")
        
        # Update in Supabase
        try:
            result = supabase.table('extracted_data').update(update_data).eq('id', id).execute()
            logger.info(f"Successfully updated data in Supabase: {json.dumps(result.data, indent=2)}")
            
            return jsonify({
                "success": True,
                "message": "Data updated successfully",
                "record_id": id
            }), 200
            
        except Exception as e:
            logger.error(f"Supabase error: {str(e)}")
            logger.error(f"Failed update data: {json.dumps(update_data, indent=2)}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Update API error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Telegram Bot API Endpoints
@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get user settings including Telegram configuration."""
    try:
        # Get user ID from request (in production, get from auth token)
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # In production, fetch from database
        # For now, return from memory storage
        user_settings = telegram_settings.get(user_id, {})
        
        return jsonify({
            "success": True,
            "settings": user_settings
        }), 200
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/settings/telegram', methods=['POST'])
def save_telegram_settings():
    """Save Telegram bot settings - simplified version."""
    try:
        data = request.get_json()
        logger.info(f"=== SAVING TELEGRAM SETTINGS ===")
        logger.info(f"Received data: {json.dumps(data, indent=2)}")
        
        enabled = data.get('enabled', False)
        token = data.get('token', '').strip()
        user_id = data.get('user_id')
        
        logger.info(f"Parsed settings - enabled: {enabled}, token: {'***' if token else 'None'}, user_id: {user_id}")
        
        if not user_id:
            logger.error("User ID is missing")
            return jsonify({"error": "User ID is required"}), 400
        
        if enabled and not token:
            logger.error("Token is required when enabling bot")
            return jsonify({"error": "Telegram bot token is required when enabling the bot"}), 400
        
        # Validate token if provided
        webhook_success = False
        if token:
            try:
                logger.info(f"Validating token for user {user_id}")
                bot = TelegramBot(token, user_id)
                bot_info = bot.get_me()
                if not bot_info or not bot_info.get('ok'):
                    logger.error(f"Invalid token for user {user_id}")
                    return jsonify({"error": "Invalid Telegram bot token"}), 400
                
                bot_name = bot_info['result'].get('first_name', 'Unknown')
                bot_username = bot_info['result'].get('username', 'Unknown')
                logger.info(f"Validated Telegram bot: {bot_name} (@{bot_username})")
                
                # Auto-setup webhook if enabled
                if enabled:
                    logger.info(f"Setting up webhook for user {user_id}")
                    webhook_success = setup_webhook_for_bot(token, user_id)
                    if webhook_success:
                        logger.info(f"Webhook setup successful for user {user_id}")
                    else:
                        logger.warning(f"Webhook setup failed for user {user_id}, but continuing...")
                
            except Exception as e:
                logger.error(f"Error validating Telegram token: {str(e)}")
                return jsonify({"error": "Failed to validate Telegram bot token"}), 400
        
        # Store settings for specific user
        if user_id not in telegram_settings:
            telegram_settings[user_id] = {}
        
        telegram_settings[user_id]['telegram'] = {
            'enabled': enabled,
            'token': token,
            'updated_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Telegram settings saved successfully for user {user_id}")
        logger.info(f"Current telegram_settings: {json.dumps(telegram_settings, indent=2)}")
        
        if enabled and token:
            # Check if webhook was set up successfully
            webhook_status = "✅ Automatic responses enabled"
            if webhook_success:
                webhook_status = "✅ Webhook setup successful - bot will respond automatically!"
            else:
                webhook_status = "⚠️ Webhook setup failed - use 'Poll Messages' for testing"
            
            response_data = {
                "success": True, 
                "message": f"✅ Telegram bot configured successfully! Your bot @{bot_username} is ready to answer questions.",
                "bot_info": {
                    "name": bot_name,
                    "username": bot_username
                },
                "webhook_status": webhook_status
            }
            logger.info(f"Sending success response: {json.dumps(response_data, indent=2)}")
            return jsonify(response_data), 200
        else:
            response_data = {
                "success": True, 
                "message": "Telegram bot disabled"
            }
            logger.info(f"Sending disabled response: {json.dumps(response_data, indent=2)}")
            return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error saving Telegram settings: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Handle incoming Telegram webhook messages - simplified to respond to any message."""
    try:
        data = request.get_json()
        logger.info(f"=== RECEIVED TELEGRAM MESSAGE ===")
        logger.info(f"Webhook data: {json.dumps(data, indent=2)}")
        
        # Extract message data
        if 'message' not in data:
            logger.info("No message in webhook data")
            return jsonify({"ok": True}), 200
        
        message = data['message']
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        logger.info(f"Processing message - Chat ID: {chat_id}, Text: {text[:100]}...")
        
        if not chat_id:
            logger.info("Missing chat_id in message")
            return jsonify({"ok": True}), 200
        
        # Find which user's bot this message is for
        bot_token = None
        target_user_id = None
        
        for user_id_key, settings in telegram_settings.items():
            if settings.get('telegram', {}).get('enabled') and settings.get('telegram', {}).get('token'):
                bot_token = settings['telegram']['token']
                target_user_id = user_id_key
                break
        
        if not bot_token or not target_user_id:
            logger.warning(f"No enabled bot found. Available settings: {telegram_settings}")
            return jsonify({"ok": True}), 200
        
        # Create bot instance
        bot = TelegramBot(bot_token, target_user_id)
        
        # Process ANY message (including /start) using AI
        try:
            logger.info("Getting context from ChromaDB...")
            # Get relevant context from ChromaDB
            results = query_chroma(text, target_user_id, n_results=10)
            
            if not results or not results.get('documents'):
                logger.warning("No data found in ChromaDB")
                response_text = "Hi! 👋 I'm your bakery assistant. I'm having trouble finding specific information about that. Could you try:\n\n1. Rephrasing your question\n2. Asking about a specific product category\n3. Or just ask me about our general offerings! I'm here to help! 😊"
            else:
                logger.info(f"Found {len(results['documents'][0])} documents in ChromaDB")
                # Extract relevant context from results
                context = []
                for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                    if doc:
                        try:
                            parsed_doc = json.loads(doc)
                            parsed_doc['metadata'] = metadata
                            context.append(json.dumps(parsed_doc, indent=2))
                        except json.JSONDecodeError:
                            context.append(doc)
                
                if not context:
                    logger.warning("No valid context extracted")
                    response_text = "Hi! 👋 I'm your bakery assistant. I'm having trouble finding specific information about that. Could you try:\n\n1. Rephrasing your question\n2. Asking about a specific product category\n3. Or just ask me about our general offerings! I'm here to help! 😊"
                else:
                    logger.info("Generating AI response...")
                    # Generate response using Gemini API
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""You are a friendly and knowledgeable customer service representative for a bakery business. Your role is to help customers with their inquiries about products, pricing, and services.

Context from the bakery's product database:
{chr(10).join(context)}

Customer's question: {text}

Please respond as a helpful customer service representative who:
1. **Speaks in a warm, friendly, and conversational tone** - like you're talking to a friend
2. **Gives SHORT, CONCISE answers** - keep responses brief and to the point
3. **Directly answers the customer's question** using the product information available
4. **Provides specific details** about products, prices, and features when asked
5. **Uses natural, everyday language** - avoid overly formal or technical business jargon
6. **Shows enthusiasm** about the products
7. **Mention specific product names, prices, and descriptions** from the data when relevant
8. **Be proactive** - if someone asks about one product, briefly suggest 1-2 related items
9. **Keep responses under 3-4 sentences** unless the customer asks for detailed information

**Response Style Guidelines:**
- Start with a friendly greeting or acknowledgment
- Use "we" and "our" to show you're representing the bakery
- Include specific prices and product names from the data
- Keep it brief and conversational
- Use emojis sparingly (1-2 max per response)

**Example short responses:**
- "Hi! Yes, we have the Overload Brownie for ₹120 - it's packed with rich dark chocolate! 🍫"
- "Our Mava Cake is ₹310 and it's one of our most popular items!"
- "We have several brownie options starting at ₹110. Would you like me to tell you about our eggless varieties?"

Remember: Keep responses short, friendly, and informative!"""

                    response = model.generate_content(prompt)
                    response_text = response.text
            
            logger.info(f"Sending response to Telegram chat {chat_id}...")
            # Send response back to Telegram
            success = bot.send_message(str(chat_id), response_text)
            if success:
                logger.info(f"Successfully sent response to Telegram chat {chat_id}")
            else:
                logger.error(f"Failed to send response to Telegram chat {chat_id}")
                
        except Exception as e:
            logger.error(f"Error processing Telegram message: {str(e)}")
            # Send error message to user
            error_message = "Sorry, I'm having some technical difficulties right now. Please try again later! 😊"
            bot.send_message(str(chat_id), error_message)
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Telegram webhook error: {str(e)}")
        return jsonify({"ok": True}), 200  # Always return 200 to Telegram

@app.route('/api/telegram/setup', methods=['POST'])
def setup_telegram_webhook():
    """Setup Telegram webhook for a user's bot."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        token = data.get('token')
        
        if not user_id or not token:
            return jsonify({"error": "User ID and token are required"}), 400
        
        # Create bot instance
        bot = TelegramBot(token, user_id)
        
        # Get webhook URL from environment or try to use ngrok
        webhook_domain = os.getenv("WEBHOOK_DOMAIN")
        
        # If no webhook domain is set, try to get ngrok URL automatically
        if not webhook_domain or webhook_domain == "localhost:5000":
            logger.info("No webhook domain configured, trying to get ngrok URL...")
            ngrok_url = get_ngrok_url()
            if ngrok_url:
                webhook_domain = ngrok_url.replace("https://", "").replace("http://", "")
                logger.info(f"Found ngrok URL: {webhook_domain}")
            else:
                logger.warning("No ngrok URL found. Bot will work with polling only.")
                # Delete any existing webhook to avoid conflicts
                bot.delete_webhook()
                return True
        
        # Set up the webhook
        webhook_url = f"https://{webhook_domain}/api/telegram/webhook"
        logger.info(f"Setting up webhook: {webhook_url}")
        
        success = bot.set_webhook(webhook_url)
        if success:
            logger.info(f"✅ Webhook setup successful for user {user_id}")
            logger.info(f"   Bot will now automatically respond to messages!")
            return True
        else:
            logger.error(f"Failed to setup webhook for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up webhook: {str(e)}")
        return False

def get_ngrok_url():
    """Try to get ngrok URL automatically."""
    try:
        # Try to get ngrok tunnels
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            tunnels = response.json()
            for tunnel in tunnels.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    return tunnel.get('public_url')
        return None
    except Exception as e:
        logger.debug(f"Could not get ngrok URL: {str(e)}")
        return None

@app.route('/api/telegram/status', methods=['GET'])
def telegram_status():
    """Get Telegram bot status."""
    try:
        # Return status of all configured bots
        bot_statuses = {}
        
        for user_id, settings in telegram_settings.items():
            if settings.get('telegram', {}).get('enabled') and settings.get('telegram', {}).get('token'):
                try:
                    bot = TelegramBot(settings['telegram']['token'], user_id)
                    bot_info = bot.get_me()
                    if bot_info and bot_info.get('ok'):
                        bot_statuses[user_id] = {
                            "status": "active",
                            "username": bot_info['result'].get('username'),
                            "first_name": bot_info['result'].get('first_name')
                        }
                    else:
                        bot_statuses[user_id] = {"status": "inactive", "error": "Invalid token"}
                except Exception as e:
                    bot_statuses[user_id] = {"status": "error", "error": str(e)}
        
        return jsonify({
            "success": True,
            "bots": bot_statuses
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting Telegram status: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/telegram/test-message', methods=['POST'])
def test_telegram_message():
    """Test endpoint to send a message to Telegram bot - simplified version."""
    try:
        data = request.get_json()
        logger.info(f"=== TELEGRAM TEST MESSAGE DEBUG ===")
        logger.info(f"Received data: {json.dumps(data, indent=2)}")
        
        user_id = data.get('user_id')
        message_text = data.get('message', 'Hello')
        
        logger.info(f"User ID: {user_id}")
        logger.info(f"Message: {message_text}")
        
        if not user_id:
            logger.error("No user_id provided")
            return jsonify({"error": "User ID is required"}), 400
        
        logger.info(f"Testing Telegram message for user {user_id}: {message_text}")
        
        # Find the user's bot settings
        bot_token = None
        logger.info(f"Available telegram settings: {list(telegram_settings.keys())}")
        
        if user_id in telegram_settings:
            user_settings = telegram_settings[user_id]
            logger.info(f"User settings: {json.dumps(user_settings, indent=2)}")
            
            if user_settings.get('telegram', {}).get('enabled'):
                bot_token = user_settings['telegram']['token']
                logger.info(f"Found bot token: {bot_token[:10]}..." if bot_token else "No token")
            else:
                logger.error("Telegram not enabled for this user")
        else:
            logger.error(f"User {user_id} not found in telegram_settings")
        
        if not bot_token:
            logger.error("No active bot found for this user")
            return jsonify({"error": "No active bot found for this user. Please save your Telegram settings first."}), 400
        
        # Create bot instance
        bot = TelegramBot(bot_token, user_id)
        
        # Process message using the same AI logic as the web chat
        try:
            logger.info("Getting context from ChromaDB...")
            # Get relevant context from ChromaDB
            results = query_chroma(message_text, user_id, n_results=10)
            
            if not results or not results.get('documents'):
                logger.warning("No data found in ChromaDB")
                response_text = "Hi! I'm having trouble finding specific information about that. Could you try:\n\n1. Rephrasing your question\n2. Asking about a specific product category\n3. Or just ask me about our general offerings! I'm here to help! 😊"
            else:
                logger.info(f"Found {len(results['documents'][0])} documents in ChromaDB")
                # Extract relevant context from results
                context = []
                for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                    if doc:
                        try:
                            parsed_doc = json.loads(doc)
                            parsed_doc['metadata'] = metadata
                            context.append(json.dumps(parsed_doc, indent=2))
                        except json.JSONDecodeError:
                            context.append(doc)
                
                if not context:
                    logger.warning("No valid context extracted")
                    response_text = "Hi! I'm having trouble finding specific information about that. Could you try:\n\n1. Rephrasing your question\n2. Asking about a specific product category\n3. Or just ask me about our general offerings! I'm here to help! 😊"
                else:
                    logger.info("Generating AI response...")
                    # Generate response using Gemini API
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""You are a friendly and knowledgeable customer service representative for a bakery business. Your role is to help customers with their inquiries about products, pricing, and services.

Context from the bakery's product database:
{chr(10).join(context)}

Customer's question: {message_text}

Please respond as a helpful customer service representative who:
1. **Speaks in a warm, friendly, and conversational tone** - like you're talking to a friend
2. **Gives SHORT, CONCISE answers** - keep responses brief and to the point
3. **Directly answers the customer's question** using the product information available
4. **Provides specific details** about products, prices, and features when asked
5. **Uses natural, everyday language** - avoid overly formal or technical business jargon
6. **Shows enthusiasm** about the products
7. **Mention specific product names, prices, and descriptions** from the data when relevant
8. **Be proactive** - if someone asks about one product, briefly suggest 1-2 related items
9. **Keep responses under 3-4 sentences** unless the customer asks for detailed information

**Response Style Guidelines:**
- Start with a friendly greeting or acknowledgment
- Use "we" and "our" to show you're representing the bakery
- Include specific prices and product names from the data
- Keep it brief and conversational
- Use emojis sparingly (1-2 max per response)

**Example short responses:**
- "Hi! Yes, we have the Overload Brownie for ₹120 - it's packed with rich dark chocolate! 🍫"
- "Our Mava Cake is ₹310 and it's one of our most popular items!"
- "We have several brownie options starting at ₹110. Would you like me to tell you about our eggless varieties?"

Remember: Keep responses short, friendly, and informative!"""

                    response = model.generate_content(prompt)
                    response_text = response.text
            
            logger.info(f"Generated response: {response_text[:100]}...")
            
            return jsonify({
                "success": True,
                "message": "✅ Bot is working correctly!",
                "response": response_text,
                "note": "🎉 Your bot will now respond to ANY message automatically when users send messages to it on Telegram!"
            })
                
        except Exception as e:
            logger.error(f"Error processing test message: {str(e)}")
            return jsonify({
                "error": f"Failed to process message: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"Test message error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/telegram/poll', methods=['GET'])
def telegram_poll():
    """Poll for new Telegram messages - for development when webhooks aren't available."""
    try:
        # Get the first enabled bot
        bot_token = None
        user_id = None
        
        for uid, settings in telegram_settings.items():
            if settings.get('telegram', {}).get('enabled') and settings.get('telegram', {}).get('token'):
                bot_token = settings['telegram']['token']
                user_id = uid
                break
        
        if not bot_token:
            return jsonify({"error": "No active bot found"}), 400
        
        bot = TelegramBot(bot_token, user_id)
        
        # Get updates from Telegram with offset to only get new messages
        try:
            # Use offset to get only new messages
            offset = len(processed_message_ids) + 1 if processed_message_ids else 1
            response = requests.get(f"{bot.base_url}/getUpdates?offset={offset}&timeout=10")
            
            if response.status_code == 200:
                updates = response.json()
                new_messages = []
                
                if updates.get('ok') and updates.get('result'):
                    for update in updates['result']:
                        if 'message' in update:
                            message = update['message']
                            message_id = update.get('update_id')
                            chat_id = message.get('chat', {}).get('id')
                            text = message.get('text', '')
                            
                            # Skip if we've already processed this message
                            if message_id in processed_message_ids:
                                continue
                            
                            # Skip if it's not a text message
                            if not text or not chat_id:
                                processed_message_ids.add(message_id)
                                continue
                            
                            logger.info(f"Processing NEW message {message_id}: {text[:50]}...")
                            
                            # Process the message using the same logic as webhook
                            try:
                                # Get relevant context from ChromaDB
                                results = query_chroma(text, user_id, n_results=10)
                                
                                if not results or not results.get('documents'):
                                    response_text = "Hi! 👋 I'm your bakery assistant. I'm having trouble finding specific information about that. Could you try:\n\n1. Rephrasing your question\n2. Asking about a specific product category\n3. Or just ask me about our general offerings! I'm here to help! 😊"
                                else:
                                    # Extract relevant context from results
                                    context = []
                                    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                                        if doc:
                                            try:
                                                parsed_doc = json.loads(doc)
                                                parsed_doc['metadata'] = metadata
                                                context.append(json.dumps(parsed_doc, indent=2))
                                            except json.JSONDecodeError:
                                                context.append(doc)
                                        
                                    if not context:
                                        response_text = "Hi! 👋 I'm your bakery assistant. I'm having trouble finding specific information about that. Could you try:\n\n1. Rephrasing your question\n2. Asking about a specific product category\n3. Or just ask me about our general offerings! I'm here to help! 😊"
                                    else:
                                        # Generate response using Gemini API
                                        model = genai.GenerativeModel('gemini-1.5-flash')
                                        prompt = f"""You are a friendly and knowledgeable customer service representative for a bakery business. Your role is to help customers with their inquiries about products, pricing, and services.

Context from the bakery's product database:
{chr(10).join(context)}

Customer's question: {text}

Please respond as a helpful customer service representative who:
1. **Speaks in a warm, friendly, and conversational tone** - like you're talking to a friend
2. **Gives SHORT, CONCISE answers** - keep responses brief and to the point
3. **Directly answers the customer's question** using the product information available
4. **Provides specific details** about products, prices, and features when asked
5. **Uses natural, everyday language** - avoid overly formal or technical business jargon
6. **Shows enthusiasm** about the products
7. **Mention specific product names, prices, and descriptions** from the data when relevant
8. **Be proactive** - if someone asks about one product, briefly suggest 1-2 related items
9. **Keep responses under 3-4 sentences** unless the customer asks for detailed information

**Response Style Guidelines:**
- Start with a friendly greeting or acknowledgment
- Use "we" and "our" to show you're representing the bakery
- Include specific prices and product names from the data
- Keep it brief and conversational
- Use emojis sparingly (1-2 max per response)

**Example short responses:**
- "Hi! Yes, we have the Overload Brownie for ₹120 - it's packed with rich dark chocolate! 🍫"
- "Our Mava Cake is ₹310 and it's one of our most popular items!"
- "We have several brownie options starting at ₹110. Would you like me to tell you about our eggless varieties?"

Remember: Keep responses short, friendly, and informative!"""

                                        response = model.generate_content(prompt)
                                        response_text = response.text
                                
                                # Send response back to Telegram
                                success = bot.send_message(str(chat_id), response_text)
                                if success:
                                    new_messages.append({
                                        "message_id": message_id,
                                        "chat_id": chat_id,
                                        "question": text,
                                        "response": response_text[:100] + "..."
                                    })
                                    logger.info(f"Successfully responded to NEW message {message_id} from chat {chat_id}")
                                else:
                                    logger.error(f"Failed to send response to chat {chat_id}")
                                    
                            except Exception as e:
                                logger.error(f"Error processing message {message_id}: {str(e)}")
                                error_message = "Sorry, I'm having some technical difficulties right now. Please try again later! 😊"
                                bot.send_message(str(chat_id), error_message)
                            
                            # Mark this message as processed
                            processed_message_ids.add(message_id)
                
                return jsonify({
                    "success": True,
                    "messages_processed": len(new_messages),
                    "new_messages": new_messages,
                    "total_processed": len(processed_message_ids)
                })
            else:
                return jsonify({"error": f"Failed to get updates: {response.text}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error getting updates: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Poll error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/telegram/clear-history', methods=['POST'])
def clear_telegram_history():
    """Clear the processed message history for testing."""
    try:
        global processed_message_ids
        old_count = len(processed_message_ids)
        processed_message_ids.clear()
        
        logger.info(f"Cleared {old_count} processed message IDs")
        
        return jsonify({
            "success": True,
            "message": f"Cleared {old_count} processed messages",
            "remaining": 0
        })
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Error handlers
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 16MB."}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

def setup_webhook_for_bot(token, user_id):
    """Setup webhook for the bot to receive messages automatically."""
    try:
        bot = TelegramBot(token, user_id)
        
        # Get webhook URL from environment or try to use ngrok
        webhook_domain = os.getenv("WEBHOOK_DOMAIN")
        
        # If no webhook domain is set, try to get ngrok URL automatically
        if not webhook_domain or webhook_domain == "localhost:5000":
            logger.info("No webhook domain configured, trying to get ngrok URL...")
            ngrok_url = get_ngrok_url()
            if ngrok_url:
                webhook_domain = ngrok_url.replace("https://", "").replace("http://", "")
                logger.info(f"Found ngrok URL: {webhook_domain}")
            else:
                logger.warning("No ngrok URL found. Bot will work with polling only.")
                # Delete any existing webhook to avoid conflicts
                bot.delete_webhook()
                return True
        
        # Set up the webhook
        webhook_url = f"https://{webhook_domain}/api/telegram/webhook"
        logger.info(f"Setting up webhook: {webhook_url}")
        
        success = bot.set_webhook(webhook_url)
        if success:
            logger.info(f"✅ Webhook setup successful for user {user_id}")
            logger.info(f"   Bot will now automatically respond to messages!")
            return True
        else:
            logger.error(f"Failed to setup webhook for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up webhook: {str(e)}")
        return False

def get_ngrok_url():
    """Try to get ngrok URL automatically."""
    try:
        # Try to get ngrok tunnels
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            tunnels = response.json()
            for tunnel in tunnels.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    return tunnel.get('public_url')
        return None
    except Exception as e:
        logger.debug(f"Could not get ngrok URL: {str(e)}")
        return None

@app.route('/api/settings/debug', methods=['GET'])
def debug_settings():
    """Debug endpoint to check current settings."""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        user_settings = telegram_settings.get(user_id, {})
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "settings": user_settings,
            "all_settings": telegram_settings,
            "total_users": len(telegram_settings)
        }), 200
    except Exception as e:
        logger.error(f"Error in debug settings: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/settings/save-debug', methods=['POST'])
def save_settings_debug():
    """Debug endpoint to manually save settings."""
    try:
        data = request.get_json()
        logger.info(f"=== MANUAL SAVE DEBUG ===")
        logger.info(f"Received data: {json.dumps(data, indent=2)}")
        
        user_id = data.get('user_id')
        enabled = data.get('enabled', False)
        token = data.get('token', '').strip()
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Store settings
        if user_id not in telegram_settings:
            telegram_settings[user_id] = {}
        
        telegram_settings[user_id]['telegram'] = {
            'enabled': enabled,
            'token': token,
            'updated_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Settings saved manually for user {user_id}")
        logger.info(f"Current telegram_settings: {json.dumps(telegram_settings, indent=2)}")
        
        return jsonify({
            "success": True,
            "message": "Settings saved manually",
            "user_id": user_id,
            "settings": telegram_settings[user_id]
        }), 200
        
    except Exception as e:
        logger.error(f"Error in manual save: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/telegram/auto-poll', methods=['POST'])
def auto_poll_telegram():
    """Auto-poll for new Telegram messages and respond automatically - simple solution."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Find the user's bot settings
        bot_token = None
        for uid, settings in telegram_settings.items():
            if settings.get('telegram', {}).get('enabled') and settings.get('telegram', {}).get('token'):
                bot_token = settings['telegram']['token']
                user_id = uid
                break
        
        if not bot_token:
            return jsonify({"error": "No active bot found"}), 400
        
        bot = TelegramBot(bot_token, user_id)
        
        # Get updates from Telegram
        try:
            response = requests.get(f"{bot.base_url}/getUpdates?timeout=1")
            
            if response.status_code == 200:
                updates = response.json()
                new_messages = []
                
                if updates.get('ok') and updates.get('result'):
                    for update in updates['result']:
                        if 'message' in update:
                            message = update['message']
                            message_id = update.get('update_id')
                            chat_id = message.get('chat', {}).get('id')
                            text = message.get('text', '')
                            
                            # Skip if we've already processed this message
                            if message_id in processed_message_ids:
                                continue
                            
                            # Skip if it's not a text message
                            if not text or not chat_id:
                                processed_message_ids.add(message_id)
                                continue
                            
                            logger.info(f"Processing NEW message {message_id}: {text[:50]}...")
                            
                            # Process the message using AI
                            try:
                                # Get relevant context from ChromaDB
                                results = query_chroma(text, user_id, n_results=10)
                                
                                if not results or not results.get('documents'):
                                    response_text = "Hi! 👋 I'm your bakery assistant. I'm having trouble finding specific information about that. Could you try:\n\n1. Rephrasing your question\n2. Asking about a specific product category\n3. Or just ask me about our general offerings! I'm here to help! 😊"
                                else:
                                    # Extract relevant context from results
                                    context = []
                                    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                                        if doc:
                                            try:
                                                parsed_doc = json.loads(doc)
                                                parsed_doc['metadata'] = metadata
                                                context.append(json.dumps(parsed_doc, indent=2))
                                            except json.JSONDecodeError:
                                                context.append(doc)
                                        
                                    if not context:
                                        response_text = "Hi! 👋 I'm your bakery assistant. I'm having trouble finding specific information about that. Could you try:\n\n1. Rephrasing your question\n2. Asking about a specific product category\n3. Or just ask me about our general offerings! I'm here to help! 😊"
                                    else:
                                        # Generate response using Gemini API
                                        model = genai.GenerativeModel('gemini-1.5-flash')
                                        prompt = f"""You are a friendly and knowledgeable customer service representative for a bakery business. Your role is to help customers with their inquiries about products, pricing, and services.

Context from the bakery's product database:
{chr(10).join(context)}

Customer's question: {text}

Please respond as a helpful customer service representative who:
1. **Speaks in a warm, friendly, and conversational tone** - like you're talking to a friend
2. **Gives SHORT, CONCISE answers** - keep responses brief and to the point
3. **Directly answers the customer's question** using the product information available
4. **Provides specific details** about products, prices, and features when asked
5. **Uses natural, everyday language** - avoid overly formal or technical business jargon
6. **Shows enthusiasm** about the products
7. **Mention specific product names, prices, and descriptions** from the data when relevant
8. **Be proactive** - if someone asks about one product, briefly suggest 1-2 related items
9. **Keep responses under 3-4 sentences** unless the customer asks for detailed information

**Response Style Guidelines:**
- Start with a friendly greeting or acknowledgment
- Use "we" and "our" to show you're representing the bakery
- Include specific prices and product names from the data
- Keep it brief and conversational
- Use emojis sparingly (1-2 max per response)

**Example short responses:**
- "Hi! Yes, we have the Overload Brownie for ₹120 - it's packed with rich dark chocolate! 🍫"
- "Our Mava Cake is ₹310 and it's one of our most popular items!"
- "We have several brownie options starting at ₹110. Would you like me to tell you about our eggless varieties?"

Remember: Keep responses short, friendly, and informative!"""

                                        response = model.generate_content(prompt)
                                        response_text = response.text
                                
                                # Send response back to Telegram
                                success = bot.send_message(str(chat_id), response_text)
                                if success:
                                    new_messages.append({
                                        "message_id": message_id,
                                        "chat_id": chat_id,
                                        "question": text,
                                        "response": response_text[:100] + "..."
                                    })
                                    logger.info(f"Successfully responded to NEW message {message_id} from chat {chat_id}")
                                else:
                                    logger.error(f"Failed to send response to chat {chat_id}")
                                    
                            except Exception as e:
                                logger.error(f"Error processing message {message_id}: {str(e)}")
                                error_message = "Sorry, I'm having some technical difficulties right now. Please try again later! 😊"
                                bot.send_message(str(chat_id), error_message)
                            
                            # Mark this message as processed
                            processed_message_ids.add(message_id)
                
                return jsonify({
                    "success": True,
                    "messages_processed": len(new_messages),
                    "new_messages": new_messages,
                    "total_processed": len(processed_message_ids),
                    "note": "🎉 Auto-polling working! Your bot is responding to messages automatically!"
                })
            else:
                return jsonify({"error": f"Failed to get updates: {response.text}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error getting updates: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Auto-poll error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    # Check for required environment variables
    if not os.environ.get("GEMINI_API_KEY"):
        logger.warning("⚠️  GEMINI_API_KEY not found in environment variables")
        logger.warning("⚠️  Set your API key: export GEMINI_API_KEY=your_api_key")
    
    logger.info("🌟 Starting BusinessAI Platform Backend Server...")
    logger.info("🔑 Make sure to set your GEMINI_API_KEY in environment variables")
    logger.info("🌐 Frontend should connect to: http://localhost:5000")
    logger.info("📖 API Documentation available at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 