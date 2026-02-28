from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def generate_pdf(path, data):

    doc = SimpleDocTemplate(path)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Digital Media Forensic Report", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    table_data = [
        ["Case ID", data["case_id"]],
        ["Filename", data["filename"]],
        ["SHA-256 Hash", data["hash"]],
        ["Authenticity (%)", str(data["authenticity"])],
        ["Tamper Level", data["tamper_level"]]
    ]

    table = Table(table_data)
    elements.append(table)

    doc.build(elements)