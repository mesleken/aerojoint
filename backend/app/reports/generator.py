"""
WeasyPrint + Jinja2 PDF Sertifikasyon Rapor Oluşturucu.
"""
from pathlib import Path
from datetime import datetime
import uuid

try:
    import weasyprint
    HAS_WEASYPRINT = True
except (ImportError, OSError):
    HAS_WEASYPRINT = False

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"


class CertificationReportGenerator:
    """MIL-HDBK-17 Sertifikasyon PDF Raporu Üreticisi."""

    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=True
        )

    def generate_pdf(self, analysis_result: dict, output_path: str) -> str:
        context = {
            'report_id': f"AJ-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'layup_notation': analysis_result.get('layup_notation', 'N/A'),
            'total_thickness': analysis_result.get('total_thickness', 0.0),
            'applied_load': analysis_result.get('applied_load', 0.0),
            'min_mos': analysis_result.get('min_mos', 0.0),
            'overall_status': analysis_result.get('overall_status', 'FAIL'),
            'critical_ply': analysis_result.get('critical_ply', 0),
            'critical_angle': analysis_result.get('critical_angle', 0),
            'critical_mode': analysis_result.get('critical_mode', 'N/A'),
            'ply_results': analysis_result.get('ply_results', []),
            'A_matrix': analysis_result.get('A_matrix', []),
            'B_matrix': analysis_result.get('B_matrix', []),
            'D_matrix': analysis_result.get('D_matrix', []),
        }

        template = self.jinja_env.get_template("report.html")
        html_content = template.render(**context)

        if HAS_WEASYPRINT:
            css_path = TEMPLATES_DIR / "styles.css"
            html = weasyprint.HTML(string=html_content, base_url=str(TEMPLATES_DIR))
            css = weasyprint.CSS(filename=str(css_path))
            html.write_pdf(output_path, stylesheets=[css])
        else:
            # Fallback to HTML file if WeasyPrint binary isn't available
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        return output_path
