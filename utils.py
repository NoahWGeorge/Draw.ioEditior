import csv
from collections import defaultdict
import xml.etree.ElementTree as ET
import zlib
import base64
import os

def parse_columns_as_tables(file_path):
    import csv
    from collections import defaultdict
    tables = defaultdict(list)
    with open(file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = [fn.strip() for fn in reader.fieldnames]
        # Prepare one "table" per header
        for header in headers:
            tables[header] = []
        for row in reader:
            for header in headers:
                tables[header].append(row[header])
    return dict(tables)

def parse_qlik_csv(file_path):
    tables = defaultdict(list)
    table_rows = {}
    with open(file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = [fn.strip() for fn in reader.fieldnames]

        if 'TableName' in headers and 'FieldName' in headers:
            # Qlik semantic model style
            for row in reader:
                table = row['TableName'].strip()
                field = row['FieldName'].strip()
                keytype = row.get('KeyType', '').strip()
                if keytype:
                    field += f" ({keytype})"
                tables[table].append(field)
        else:
            # Data table style
            table_name = os.path.splitext(os.path.basename(file_path))[0]
            tables[table_name] = headers
            rows = []
            for row in reader:
                rows.append([row[h] for h in headers])
            table_rows[table_name] = rows
    return dict(tables), table_rows



def generate_dbml(tables, output_path):
    lines = []
    for table, fields in tables.items():
        lines.append(f"Table {table} {{")
        for field in fields:
            # Parse key type for DBML
            if "(PK)" in field:
                field_name = field.replace(" (PK)", "")
                lines.append(f"  {field_name} int [pk]")
            elif "(FK:" in field:
                import re
                m = re.match(r"(.+?) \(FK:(.+)\)", field)
                if m:
                    fname, ref = m.groups()
                    lines.append(f"  {fname} int [ref: > {ref}]")
                else:
                    lines.append(f"  {field}")
            else:
                lines.append(f"  {field} int")
        lines.append("}\n")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def create_valid_drawio_file(tables, table_rows, output_path):
    import xml.etree.ElementTree as ET
    import zlib
    import base64

    root = ET.Element("mxGraphModel")
    root_elem = ET.SubElement(root, "root")
    ET.SubElement(root_elem, "mxCell", id="0")
    ET.SubElement(root_elem, "mxCell", id="1", parent="0")

    x_offset = 20
    width = 200
    height_per_field = 26
    base_height = 40

    for i, (col_name, values) in enumerate(tables.items()):
        # Compose HTML table for column, using values from table_rows if present
        label = f"""<div style="text-align:left">
<b>{col_name}</b>
<table border="1" cellpadding="2" cellspacing="0" style="border-collapse:collapse; font-size:10pt">
"""
        # If table_rows is provided and not empty, display each row value
        if table_rows and col_name in table_rows:
            for val in table_rows[col_name]:
                label += f"<tr><td>{val}</td></tr>"
        else:
            # fallback: use values from tables dictionary
            for val in values:
                label += f"<tr><td>{val}</td></tr>"
        label += "</table></div>"

        height = base_height + (len(values) + 2) * height_per_field

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



