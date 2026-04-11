import pdfkit

config = pdfkit.configuration(
    wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

def html_to_pdf(html_content, output_path):
    # ✅ Fix encoding
    html_content = html_content.encode("utf-8").decode("utf-8")

    pdfkit.from_string(
        html_content,
        output_path,
        configuration=config,
        options={"encoding": "UTF-8"}
    )