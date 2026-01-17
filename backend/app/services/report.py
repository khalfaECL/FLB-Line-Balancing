import io
import os
import tempfile
from typing import Dict, Tuple

from fpdf import FPDF
from matplotlib.figure import Figure
from PIL import Image


class _ReportPDF(FPDF):
    def header(self) -> None:
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Line Balancing Report", ln=True, align="C")
        self.ln(4)

    def section_title(self, title: str) -> None:
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True)
        self.ln(2)

    def add_figure(self, fig: Figure) -> None:
        buf = io.BytesIO()
        fig.savefig(buf, format="PNG", bbox_inches="tight")
        buf.seek(0)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(buf.read())
            tmp_path = tmp.name

        buf.close()

        try:
            img = Image.open(tmp_path)
            img.save(tmp_path)
            self.image(tmp_path, x=10, y=25, w=270)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def add_text_block(self, text: str, x: int = 10, y: int = 160) -> None:
        self.set_xy(x, y)
        self.set_font("Courier", size=9)
        self.multi_cell(0, 5, text)


def generate_report_pdf(fig: Figure, assignments: Dict[str, Tuple], output_path: str) -> None:
    text_block = ""
    for method, (ws, times) in assignments.items():
        text_block += f"\nMethod: {method}\n"
        for i, (poste, t) in enumerate(zip(ws, times)):
            if poste:
                task_list = ", ".join([f"{task} ({dur:.2f})" for task, dur in poste])
                text_block += f"Station {i + 1} ({t:.2f} min): {task_list}\n"

    pdf = _ReportPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.section_title("Balancing Overview")
    pdf.add_figure(fig)
    pdf.add_text_block(text_block)
    pdf.output(output_path)
