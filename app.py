from flask import Flask, request, send_file, render_template
import os
from utils import parse_qlik_csv, create_valid_drawio_file

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['qlik_csv']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    tables = parse_qlik_csv(file_path)
    output_file = os.path.join(OUTPUT_FOLDER, 'output.drawio')
    create_valid_drawio_file(tables, output_file)

    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
