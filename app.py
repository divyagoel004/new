from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import PyPDF2
import io
import os
import logging
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')

# Create directories for templates and static files if they don't exist
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# Create template and static files
with open('templates/index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Content Extractor</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>PDF Content Extraction Service</h1>
           
        </header>
        
        <div class="tabs">
            <button class="tab-btn active" data-tab="url-tab">URL Method</button>
            <button class="tab-btn" data-tab="upload-tab">Upload Method</button>
        </div>
        
        <div class="tab-content">
            <div id="url-tab" class="tab-pane active">
                <div class="input-group">
                    <label for="pdf-url">PDF URL:</label>
                    <input type="url" id="pdf-url" placeholder="https://example.com/document.pdf" required>
                </div>
                <button id="extract-btn" class="primary-btn">Extract Text</button>
            </div>
            
           
        </div>
        
        <div class="result-container">
            <div class="result-header">
                <h2>Extracted Text</h2>
                <span id="page-count"></span>
            </div>
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Processing PDF...</p>
            </div>
            <div class="controls">
                <button id="copy-btn" class="secondary-btn" disabled>Copy to Clipboard</button>
                <button id="download-btn" class="secondary-btn" disabled>Download as TXT</button>
            </div>
            <div class="text-container">
                <pre id="extracted-text"></pre>
            </div>
        </div>

        
    </div>
    <script src="/static/js/main.js"></script>
</body>
</html>
''')

with open('static/css/style.css', 'w') as f:
    f.write('''
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f7fa;
}

.container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem;
}

header {
    text-align: center;
    margin-bottom: 2rem;
}

header h1 {
    color: #2c3e50;
    margin-bottom: 0.5rem;
}

header p {
    color: #7f8c8d;
}

.tabs {
    display: flex;
    border-bottom: 1px solid #ddd;
    margin-bottom: 2rem;
}

.tab-btn {
    padding: 0.75rem 1.5rem;
    background: none;
    border: none;
    border-bottom: 3px solid transparent;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
    color: #7f8c8d;
    transition: all 0.3s ease;
}

.tab-btn.active {
    color: #3498db;
    border-bottom-color: #3498db;
}

.tab-pane {
    display: none;
    padding: 1.5rem 0;
}

.tab-pane.active {
    display: block;
}

.input-group {
    margin-bottom: 1.5rem;
}

.input-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

input[type="url"], input[type="file"] {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

.primary-btn {
    display: inline-block;
    background-color: #3498db;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.primary-btn:hover {
    background-color: #2980b9;
}

.secondary-btn {
    background-color: #ecf0f1;
    color: #2c3e50;
    border: 1px solid #ddd;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.3s ease;
    margin-right: 0.5rem;
}

.secondary-btn:hover {
    background-color: #dfe6e9;
}

.secondary-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.result-container {
    margin-top: 2rem;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    padding: 1.5rem;
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #eee;
}

.controls {
    margin-bottom: 1rem;
}

.text-container {
    background-color: #f8f9fa;
    border: 1px solid #eee;
    border-radius: 4px;
    padding: 1rem;
    max-height: 400px;
    overflow-y: auto;
}

pre#extracted-text {
    white-space: pre-wrap;
    font-family: monospace;
    font-size: 0.9rem;
    line-height: 1.5;
}

.loading {
    display: none;
    text-align: center;
    padding: 2rem 0;
}

.spinner {
    display: inline-block;
    width: 40px;
    height: 40px;
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-radius: 50%;
    border-top-color: #3498db;
    animation: spin 1s ease-in-out infinite;
    margin-bottom: 1rem;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.api-info {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid #eee;
}

.api-info h3 {
    margin-bottom: 1rem;
}

.code-block {
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.9rem;
}
''')

with open('static/js/main.js', 'w') as f:
    f.write('''
document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to clicked button and corresponding pane
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
    
    // URL method extraction
    const extractBtn = document.getElementById('extract-btn');
    extractBtn.addEventListener('click', function() {
        const pdfUrl = document.getElementById('pdf-url').value.trim();
        if (!pdfUrl) {
            alert('Please enter a valid PDF URL');
            return;
        }
        extractPdfText(pdfUrl);
    });
    
    // Upload method extraction
    const uploadForm = document.getElementById('upload-form');
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const fileInput = document.getElementById('pdf-file');
        if (!fileInput.files[0]) {
            alert('Please select a PDF file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        uploadAndExtract(formData);
    });
    
    // Copy to clipboard functionality
    const copyBtn = document.getElementById('copy-btn');
    copyBtn.addEventListener('click', function() {
        const extractedText = document.getElementById('extracted-text').textContent;
        navigator.clipboard.writeText(extractedText)
            .then(() => {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                }, 2000);
            })
            .catch(err => {
                console.error('Could not copy text: ', err);
                alert('Failed to copy text to clipboard');
            });
    });
    
    // Download as TXT functionality
    const downloadBtn = document.getElementById('download-btn');
    downloadBtn.addEventListener('click', function() {
        const extractedText = document.getElementById('extracted-text').textContent;
        const blob = new Blob([extractedText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        a.href = url;
        a.download = 'extracted-text.txt';
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 0);
    });
    
    function extractPdfText(pdfUrl) {
        // Show loading indicator
        document.getElementById('loading').style.display = 'block';
        document.getElementById('extracted-text').textContent = '';
        document.getElementById('page-count').textContent = '';
        copyBtn.disabled = true;
        downloadBtn.disabled = true;
        
        // Send request to backend
        fetch('/extract-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pdf_url: pdfUrl }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Display the extracted text
            document.getElementById('extracted-text').textContent = data.text;
            document.getElementById('page-count').textContent = `${data.pages} pages`;
            
            // Enable buttons
            copyBtn.disabled = false;
            downloadBtn.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('extracted-text').textContent = `Error: ${error.message}`;
        })
        .finally(() => {
            // Hide loading indicator
            document.getElementById('loading').style.display = 'none';
        });
    }
    
    function uploadAndExtract(formData) {
        // Show loading indicator
        document.getElementById('loading').style.display = 'block';
        document.getElementById('extracted-text').textContent = '';
        document.getElementById('page-count').textContent = '';
        copyBtn.disabled = true;
        downloadBtn.disabled = true;
        
        // Send request to backend
        fetch('/upload-pdf', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Display the extracted text
            document.getElementById('extracted-text').textContent = data.text;
            document.getElementById('page-count').textContent = `${data.pages} pages`;
            
            // Enable buttons
            copyBtn.disabled = false;
            downloadBtn.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('extracted-text').textContent = `Error: ${error.message}`;
        })
        .finally(() => {
            // Hide loading indicator
            document.getElementById('loading').style.display = 'none';
        });
    }
});
''')

@app.route('/')
def index():
    return render_template('index.html')

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

# @app.route('/upload-pdf', methods=['POST'])
# def upload_pdf():
#     """
#     Endpoint to handle PDF file uploads and extract text.
#     """
#     try:
#         if 'file' not in request.files:
#             return jsonify({'error': 'No file part in the request'}), 400
            
#         file = request.files['file']
#         if file.filename == '':
#             return jsonify({'error': 'No file selected'}), 400
            
#         if file and file.filename.lower().endswith('.pdf'):
#             # Extract text from the uploaded PDF
#             try:
#                 pdf_file = io.BytesIO(file.read())
#                 pdf_reader = PyPDF2.PdfReader(pdf_file)
                
#                 # Extract text from each page
#                 text = ""
#                 for page_num in range(len(pdf_reader.pages)):
#                     page = pdf_reader.pages[page_num]
#                     text += page.extract_text() + "\n"
                
#                 logger.info(f"Successfully extracted {len(text)} characters from uploaded PDF")
                
#                 return jsonify({
#                     'success': True,
#                     'text': text,
#                     'pages': len(pdf_reader.pages)
#                 })
                
#             except Exception as e:
#                 logger.error(f"Error extracting text from uploaded PDF: {str(e)}")
#                 return jsonify({'error': f'Failed to extract text from PDF: {str(e)}'}), 500
#         else:
#             return jsonify({'error': 'File must be a PDF'}), 400
    
#     except Exception as e:
#         logger.error(f"Unexpected error in file upload: {str(e)}")
#         return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

