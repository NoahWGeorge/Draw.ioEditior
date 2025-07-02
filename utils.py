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

    tables = {k.strip(): v for k, v in tables.items() if k and k.strip() and k.strip().lower() not in ["none", "null"]}
    table_names = list(tables.keys())

    canvas_width = 1600  # Make canvas larger for big tables!
    table_width = 700
    height_per_field = 54
    base_height = 150
    gap = 180

    total_width = table_width * len(table_names) + gap * (len(table_names) - 1)
    start_x = max((canvas_width - total_width) // 2, 20)

    root = ET.Element("mxGraphModel")
    root_elem = ET.SubElement(root, "root")
    ET.SubElement(root_elem, "mxCell", id="0")
    ET.SubElement(root_elem, "mxCell", id="1", parent="0")

    table_cell_ids = {}

    for i, (table, fields) in enumerate(tables.items()):
        if not table:
            continue

        # Table as HTML label (NO swimlane!)
        label = f"""
<div>
  <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; font-size:20pt; min-width:540px;">
    <tr style="background:#a67c52; color:#fff;">
      <th colspan="3" style="font-size:24pt; font-weight:bold; text-align:center;">{table}</th>
    </tr>
    <tr style="background:#333; color:#fff;">
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
        x = start_x + i * (table_width + gap)
        cell = ET.SubElement(root_elem, "mxCell", id=cell_id, value=label,
                             style="html=1;whiteSpace=wrap;rounded=1;shadow=1;",
                             vertex="1", parent="1")
        geom = ET.SubElement(cell, "mxGeometry", x=str(x), y="250",
                             width=str(table_width), height=str(height))
        geom.set("as", "geometry")
        table_cell_ids[table] = cell_id

    # Draw connectors for FK relationships
    for src_table, fields in tables.items():
        for field in fields:
            key_val = field.get("Key", "")
            if key_val.startswith("FK:"):
                fk_ref = key_val[3:]
                ref_table = fk_ref.split(".")[0]
                if ref_table in table_cell_ids and src_table in table_cell_ids:
                    ET.SubElement(root_elem, "mxCell",
                        id=str(9000 + len(root_elem)),
                        style="edgeStyle=orthogonalEdgeStyle;endArrow=block;html=1;strokeColor=#666;",
                        edge="1",
                        parent="1",
                        source=table_cell_ids[src_table],
                        target=table_cell_ids[ref_table]
                    )

    model_xml_str = ET.tostring(root, encoding='utf-8', method='xml')
    compressed = zlib.compress(model_xml_str)[2:-4]
    encoded = base64.b64encode(compressed).decode('utf-8')

    mxfile = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(mxfile, "diagram", name="ERD")
    diagram.text = encoded

    ET.ElementTree(mxfile).write(output_path, encoding="utf-8", xml_declaration=True)

