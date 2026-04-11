import pdfkit

# ⚠️ Update path if different on your system
config = pdfkit.configuration(
    wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

def html_to_pdf(html_content, output_path):
    pdfkit.from_string(html_content, output_path, configuration=config)