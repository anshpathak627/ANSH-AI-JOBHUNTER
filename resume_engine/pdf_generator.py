"""
resume_engine/pdf_generator.py
Generates clean, single-column ATS-friendly PDF resumes using ReportLab.
"""

from __future__ import annotations

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable


class PDFGenerator:
    """Creates elegant, ATS-compliant PDF resumes."""

    def generate_pdf(
        self,
        resume_text: str,
        output_path: str,
        candidate_name: str = "Ansh Pathak",
    ) -> str:
        """
        Render textual resume into an ATS-friendly single-column PDF.

        Parameters
        ----------
        resume_text : str
            Plaintext or structured resume content.
        output_path : str
            Target destination path for the .pdf file.
        candidate_name : str
            Candidate full name for document header.

        Returns
        -------
        str
            The resolved output path.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ResumeTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1e293b"),
            alignment=1, # Center
            spaceAfter=4,
        )

        contact_style = ParagraphStyle(
            "ResumeContact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#475569"),
            alignment=1, # Center
            spaceAfter=12,
        )

        section_heading_style = ParagraphStyle(
            "ResumeSectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=10,
            spaceAfter=4,
        )

        body_style = ParagraphStyle(
            "ResumeBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
            spaceAfter=3,
        )

        story = []

        # Split text into lines
        lines = resume_text.splitlines()

        # Check if first line is title or comment
        content_lines = []
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("#"):
                continue # Skip internal comment headers in PDF render
            content_lines.append(line_str)

        # Header
        story.append(Paragraph(candidate_name.upper(), title_style))
        story.append(Paragraph("Noida / Delhi NCR, India &nbsp;|&nbsp; +91 9999999999 &nbsp;|&nbsp; pathakansh696@gmail.com &nbsp;|&nbsp; linkedin.com/in/anshpathak", contact_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

        known_sections = [
            "PROFESSIONAL SUMMARY", "SUMMARY", "CORE TECHNICAL SKILLS", "SKILLS",
            "WORK EXPERIENCE", "EXPERIENCE", "FEATURED PROJECTS", "PROJECTS",
            "EDUCATION", "CERTIFICATIONS", "ACHIEVEMENTS"
        ]

        for line in content_lines:
            if not line:
                story.append(Spacer(1, 4))
                continue

            # Check if this line is a section heading
            is_heading = False
            for section in known_sections:
                if line.upper() == section or line.upper() == f"{section}:":
                    story.append(Paragraph(section, section_heading_style))
                    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=4))
                    is_heading = True
                    break

            if not is_heading:
                # Format bullet points
                if line.startswith("•") or line.startswith("-") or line.startswith("*"):
                    clean_line = line.lstrip("•-* ").strip()
                    story.append(Paragraph(f"&bull;&nbsp; {clean_line}", body_style))
                else:
                    story.append(Paragraph(line, body_style))

        doc.build(story)
        return output_path
