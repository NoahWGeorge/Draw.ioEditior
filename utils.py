import csv
from collections import defaultdict
import xml.etree.ElementTree as ET
import zlib
import base64

def parse_qlik_csv(file_path):
    tables = defaultdict(list)
    # Note 'utf-8-sig' removes the BOM automatically!
    with open(file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [fn.strip() for fn in reader.fieldnames]
        for row in reader:
            print("Row received:", row)
            if 'TableName' not in row or 'FieldName' not in row:
                print("Skipping row, missing keys:", row)
                continue
            table = row['TableName'].strip()
            field = row['FieldName'].strip()
            keytype = row['KeyType'].strip() if row['KeyType'] else ""
            if keytype:
                field += f" ({keytype})"
            tables[table].append(field)
    return dict(tables)



def create_valid_drawio_file(tables, output_path):
    root = ET.Element("mxGraphModel")
    root_elem = ET.SubElement(root, "root")
    ET.SubElement(root_elem, "mxCell", id="0")
    ET.SubElement(root_elem, "mxCell", id="1", parent="0")

    x_offset = 20
    width = 200
    height_per_field = 26
    base_height = 40

    for i, (table, fields) in enumerate(tables.items()):
        height = base_height + len(fields) * height_per_field
        cell_id = str(100 + i)
        # Create the table cell
        cell = ET.SubElement(root_elem, "mxCell", id=cell_id, value=table,
                             style="shape=swimlane;", vertex="1", parent="1")
        # Now add mxGeometry as a child of this cell
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



