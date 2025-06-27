from flask import Flask, request, send_file, render_template
import os
from utils import parse_qlik_csv, parse_columns_as_tables, create_valid_drawio_file, generate_dbml

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
    output_type = request.form.get('output_type', 'drawio')
    table_mode = request.form.get('table_mode', 'standard')  # gets table mode from form
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    if table_mode == 'columns':
        tables = parse_columns_as_tables(file_path)
        table_rows = {}  # Not used in this mode
    else:
        tables, table_rows = parse_qlik_csv(file_path)

    if output_type == 'dbml':
        output_path = os.path.join(OUTPUT_FOLDER, 'output.dbml')
        generate_dbml(tables, output_path)
        return send_file(output_path, as_attachment=True)
    else:
        output_path = os.path.join(OUTPUT_FOLDER, 'output.drawio')
        create_valid_drawio_file(tables, table_rows, output_path)
        return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

