from flask import Flask, request, render_template, send_file, jsonify
import os
from PyPDF2 import PdfMerger, PdfReader
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import tempfile
from io import BytesIO

app = Flask(__name__)

# Folder to store uploaded files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Convert PDF to Text (OCR)
@app.route('/convert_pdf_to_text', methods=['POST'])
def convert_pdf_to_text():
    pdf_file = request.files['pdf_file']
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
    pdf_file.save(pdf_path)
    
    # Convert PDF to image and use OCR to extract text
    text = ""
    images = convert_from_path(pdf_path)
    for img in images:
        text += pytesseract.image_to_string(img)
    
    # Return the extracted text
    return jsonify({'text': text})

# Convert PDF to Image
@app.route('/convert_pdf_to_image', methods=['POST'])
def convert_pdf_to_image():
    pdf_file = request.files['pdf_file']
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
    pdf_file.save(pdf_path)
    
    # Convert PDF to images
    images = convert_from_path(pdf_path)
    
    # Save images to disk or return as response
    image_paths = []
    for i, img in enumerate(images):
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], f'page_{i + 1}.jpg')
        img.save(img_path, 'JPEG')
        image_paths.append(img_path)
    
    # Return image paths as JSON
    return jsonify({'images': image_paths})

# Convert Image to PDF
@app.route('/image_to_pdf', methods=['POST'])
def image_to_pdf():
    image_file = request.files['image_file']
    img = Image.open(image_file)
    
    # Convert image to PDF
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{image_file.filename.split('.')[0]}.pdf")
    img.save(pdf_path, 'PDF')
    
    return send_file(pdf_path, as_attachment=True)

# Merge PDFs
@app.route('/merge_pdfs', methods=['POST'])
def merge_pdfs():
    pdf_files = request.files.getlist('pdf_files')
    merger = PdfMerger()
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
        pdf_file.save(pdf_path)
        merger.append(pdf_path)
    
    # Save the merged PDF
    merged_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged_output.pdf')
    merger.write(merged_pdf_path)
    merger.close()
    
    return send_file(merged_pdf_path, as_attachment=True)

# Split PDF
@app.route('/split_pdf', methods=['POST'])
def split_pdf():
    pdf_file = request.files['pdf_file']
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
    pdf_file.save(pdf_path)
    
    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)
    
    # Split the PDF into individual pages
    temp_dir = tempfile.mkdtemp()
    for i in range(num_pages):
        writer = PdfMerger()
        writer.append(pdf_path, pages=(i, i + 1))
        split_pdf_path = os.path.join(temp_dir, f'page_{i + 1}.pdf')
        writer.write(split_pdf_path)
    
    # Create a ZIP file of all split PDFs
    import zipfile
    zip_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'split_pdfs.zip')
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for i in range(num_pages):
            zipf.write(os.path.join(temp_dir, f'page_{i + 1}.pdf'), arcname=f'page_{i + 1}.pdf')
    
    return send_file(zip_file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)