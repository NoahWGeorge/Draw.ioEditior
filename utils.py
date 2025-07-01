import csv
from collections import defaultdict
import xml.etree.ElementTree as ET
import zlib
import base64
import os

def parse_columns_as_entities(file_path):
    # For Excel/CSV "data table" style
    with open(file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = [fn.strip() for fn in reader.fieldnames]
        rows = list(reader)
        fields = []
        for h in headers:
            key = "PK" if h.lower() in ["id", "participant id"] else ""
            fields.append({'Key': key, 'Field': h, 'Type': 'String'})  # You can infer type if you want
        table_name = os.path.splitext(os.path.basename(file_path))[0]
        return {table_name: fields}, rows  # Return a dict {table: fields} and rows for values

def parse_qlik_csv(file_path):
    tables = defaultdict(list)
    table_rows = {}
    with open(file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = [fn.strip() for fn in reader.fieldnames]
        # If Qlik semantic model style, treat differently
        if 'TableName' in headers and 'FieldName' in headers:
            for row in reader:
                field_dict = {
                    'Key': row.get('KeyType', '').strip(),
                    'Field': row.get('FieldName', '').strip(),
                    'Type': 'String'  # You can enhance this if type is known
                }
                table = row['TableName'].strip()
                tables[table].append(field_dict)
        else:
            # Data table style
            return parse_columns_as_entities(file_path)
    return dict(tables), table_rows

def generate_dbml(tables, output_path):
    lines = []
    for table, fields in tables.items():
        lines.append(f"Table {table} {{")
        for field in fields:
            # Parse key type for DBML
            if field.get("Key", "") == "PK":
                lines.append(f"  {field['Field']} int [pk]")
            else:
                lines.append(f"  {field['Field']} int")
        lines.append("}\n")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))



def create_valid_drawio_file(tables, table_rows, output_path):
    import xml.etree.ElementTree as ET
    import zlib
    import base64

    # Clean out any blank/invalid table names
    tables = {k.strip(): v for k, v in tables.items() if k and k.strip() and k.strip().lower() not in ["none", "null"]}
    print("Tables being drawn:", repr(list(tables.keys())))

    root = ET.Element("mxGraphModel")
    root_elem = ET.SubElement(root, "root")
    ET.SubElement(root_elem, "mxCell", id="0")
    ET.SubElement(root_elem, "mxCell", id="1", parent="0")

    x_offset = 20
    width = 380
    height_per_field = 32
    base_height = 64

    print("Tables being drawn:", repr(list(tables.keys())))


    for i, (table, fields) in enumerate(tables.items()):
        if not table:  # Extra protection (should never trigger now)
            continue

        # ERD-style label as HTML table
        label = f"""
<div>
  <table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse; font-size:10pt;">
    <tr style="background:#DEB197; color:#222;">
      <th colspan="3" style="font-size:13pt; font-weight:bold; text-align:center;">{table}</th>
    </tr>
    <tr style="background:#F2F2F2;">
      <th style="font-weight:bold;">Key</th>
      <th style="font-weight:bold;">Field</th>
      <th style="font-weight:bold;">Type</th>
    </tr>
"""
        for field in fields:
            label += f"""<tr>
<td>{field.get('Key', '')}</td>
<td>{field.get('Field', '')}</td>
<td>{field.get('Type', '')}</td>
</tr>
"""
        label += "</table></div>"

        height = base_height + len(fields) * height_per_field
        cell_id = str(100 + i)
        cell = ET.SubElement(root_elem, "mxCell", id=cell_id, value=label,
                             style="shape=swimlane;html=1;", vertex="1", parent="1")
        geom = ET.SubElement(cell, "mxGeometry", x=str(x_offset), y="50",
                             width=str(width), height=str(height))
        geom.set("as", "geometry")
        x_offset += width + 40

    model_xml_str = ET.tostring(root, encoding='utf-8', method='xml')
    compressed = zlib.compress(model_xml_str)[2:-4]
    encoded = base64.b64encode(compressed).decode('utf-8')

    mxfile = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(mxfile, "diagram", name="ERD")
    diagram.text = encoded

    ET.ElementTree(mxfile).write(output_path, encoding="utf-8", xml_declaration=True)




