from flask import Flask, request, jsonify
import requests
import PyPDF2
import io
import os
import logging
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "PDF Content Extraction Service is running!"

@app.route('/extract-pdf', methods=['POST'])
def extract_pdf():
    """
    Endpoint to extract text from a PDF file.
    Expects a JSON with a 'pdf_url' field containing the URL to the PDF.
    Returns the extracted text.
    """
    try:
        # Get JSON data
        data = request.get_json()
        if not data or 'pdf_url' not in data:
            return jsonify({'error': 'Missing PDF URL in request'}), 400
        
        pdf_url = data['pdf_url']
        logger.info(f"Received request to extract PDF from URL: {pdf_url}")
        
        # Download the PDF file
        try:
            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading PDF: {str(e)}")
            return jsonify({'error': f'Failed to download PDF: {str(e)}'}), 400
        
        # Extract text from the PDF
        try:
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from each page
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            
            return jsonify({
                'success': True,
                'text': text,
                'pages': len(pdf_reader.pages)
            })
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return jsonify({'error': f'Failed to extract text from PDF: {str(e)}'}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
