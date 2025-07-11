import os
from datetime import datetime
from pypdf import PdfWriter
from jinja2 import Environment, FileSystemLoader
from config import Config

class PDFGenerator:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.output_dir = os.path.join(Config.UPLOAD_FOLDER, 'pdf_reports')
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_analysis_report(self, analysis_data: dict) -> str:
        """
        Generate a PDF report for policy analysis.
        
        Args:
            analysis_data: Dictionary containing analysis data
            
        Returns:
            Path to the generated PDF file
        """
        try:
            # Render HTML template
            template = self.env.get_template('analysis_report.html')
            html_content = template.render(data=analysis_data)
            
            # Create PDF writer
            pdf_writer = PdfWriter()
            
            # Add HTML content as text
            pdf_writer.add_text(html_content)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"analysis_report_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Save PDF
            with open(filepath, 'wb') as f:
                pdf_writer.write(f)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Error generating PDF report: {str(e)}")

    def generate_policy_document(self, original_policy: str, recommendations: list) -> str:
        """
        Generate a PDF version of the improved policy document.
        
        Args:
            original_policy: Original policy text
            recommendations: List of recommendations
            
        Returns:
            Path to the generated PDF file
        """
        try:
            # Render HTML template
            template = self.env.get_template('policy_document.html')
            html_content = template.render(
                original_policy=original_policy,
                recommendations=recommendations
            )
            
            # Create PDF writer
            pdf_writer = PdfWriter()
            
            # Add HTML content as text
            pdf_writer.add_text(html_content)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"improved_policy_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Save PDF
            with open(filepath, 'wb') as f:
                pdf_writer.write(f)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Error generating policy PDF: {str(e)}")
