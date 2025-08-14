"""
Export engine for PolicyCraft - handles exporting recommendations and analysis results
to various formats (PDF, Word, Excel).

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import os
import io
import json
import base64
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

# PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, ListFlowable, ListItem

# Word document generation
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Excel generation
import xlsxwriter

logger = logging.getLogger(__name__)

class ExportEngine:
    """
    Handles exporting recommendations and analysis results to various formats.
    """
    
    def __init__(self, export_dir: str = "exports"):
        """
        Initialize the export engine.
        
        Args:
            export_dir: Directory to store exported files
        """
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
        
        # Define common styles
        self.title_color = "#3498db"  # Blue
        self.heading_color = "#2c3e50"  # Dark blue
        self.accent_color = "#e74c3c"  # Red
        self.text_color = "#34495e"  # Dark gray
        
        # Chart image settings
        self.chart_width = 600
        self.chart_height = 400
        
    def _format_date(self, date_str: str) -> str:
        """Format date string to British DD/MM/YYYY style."""
        try:
            if isinstance(date_str, str):
                if "T" in date_str:
                    # ISO format
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    return dt.strftime("%d/%m/%Y")
                elif "-" in date_str:
                    # YYYY-MM-DD format
                    parts = date_str.split("-")
                    if len(parts) == 3:
                        return f"{parts[2]}/{parts[1]}/{parts[0]}"
            return date_str
        except Exception:
            return date_str
            
    def _convert_chart_to_image(self, chart_data: Dict) -> Optional[bytes]:
        """
        Convert a Plotly chart to an image.
        
        Args:
            chart_data: Dictionary containing Plotly chart data and layout
            
        Returns:
            Image as bytes or None if conversion fails
        """
        try:
            # Import plotly here to avoid circular imports
            import plotly.graph_objects as go
            import plotly.io as pio
            
            # Create a figure from the chart data
            if isinstance(chart_data, dict) and 'data' in chart_data and 'layout' in chart_data:
                fig = go.Figure(data=chart_data['data'], layout=chart_data['layout'])
                
                # Set the size of the image
                fig.update_layout(
                    width=self.chart_width,
                    height=self.chart_height
                )
                
                # Convert to PNG image
                img_bytes = pio.to_image(fig, format='png')
                return img_bytes
            else:
                logger.warning("Invalid chart data format: %s", type(chart_data))
                return None
        except Exception as e:
            logger.warning("Error converting chart to image: %s", str(e))
            return None
            
    def _process_charts_for_export(self, charts: Dict) -> Dict[str, bytes]:
        """
        Process charts for export to different formats.
        
        Args:
            charts: Dictionary containing chart data
            
        Returns:
            Dictionary of chart images as bytes
        """
        chart_images = {}
        
        try:
            # Process each chart type
            if charts.get('themes_bar'):
                chart_images['themes_bar'] = self._convert_chart_to_image(charts['themes_bar'])
                
            if charts.get('classification_gauge'):
                chart_images['classification_gauge'] = self._convert_chart_to_image(charts['classification_gauge'])
                
            if charts.get('themes_pie'):
                chart_images['themes_pie'] = self._convert_chart_to_image(charts['themes_pie'])
                
            if charts.get('ethics_radar'):
                chart_images['ethics_radar'] = self._convert_chart_to_image(charts['ethics_radar'])
                
            logger.info("Processed %d charts for export", len(chart_images))
        except Exception as e:
            logger.warning("Error processing charts for export: %s", str(e))
            
        return chart_images
    
    def export_to_pdf(self, data: Dict[str, Any]) -> bytes:
        """
        Export recommendations and analysis results to PDF.
        
        Args:
            data: Dictionary containing analysis and recommendations data
            
        Returns:
            PDF file as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
                               
        # Process charts if available
        chart_images = {}
        if data.get('charts'):
            chart_images = self._process_charts_for_export(data['charts'])
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor(self.title_color),
            spaceAfter=12
        )
        heading1_style = ParagraphStyle(
            'Heading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor(self.heading_color),
            spaceBefore=12,
            spaceAfter=6
        )
        heading2_style = ParagraphStyle(
            'Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(self.heading_color),
            spaceBefore=10,
            spaceAfter=6
        )
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor(self.text_color),
            spaceBefore=6,
            spaceAfter=6
        )
        
        # Build document content
        content = []
        
        # Title
        content.append(Paragraph("PolicyCraft Analysis Report", title_style))
        content.append(Spacer(1, 12))
        
        # Document information
        if data and data.get('analysis'):
            analysis = data['analysis']
            content.append(Paragraph("Document Information", heading1_style))
            
            # Create document info table
            doc_info = [
                ["Document", analysis.get('filename', 'Unknown')],
                ["Classification", analysis.get('classification', 'Unknown')],
                ["Generated Date", self._format_date(data.get('generated_date', 'Unknown'))],
                ["Total Recommendations", str(len(data.get('recommendations', [])))],
            ]
            
            doc_table = Table(doc_info, colWidths=[100, 350])
            doc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f9fa")),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(self.heading_color)),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e1e8ed")),
            ]))
            
            content.append(doc_table)
            content.append(Spacer(1, 12))
            
            # Analysis Results
            if analysis.get('themes'):
                content.append(Paragraph("Analysis Results", heading1_style))
                content.append(Paragraph("Key Themes", heading2_style))
                
                # Create themes table
                themes_data = [["Theme", "Score", "Confidence"]]
                for theme in analysis.get('themes', [])[:8]:  # Top 8 themes
                    themes_data.append([
                        theme.get('name', 'Unknown'),
                        str(theme.get('score', 0)),
                        f"{theme.get('confidence', 0)}%"
                    ])
                
                themes_table = Table(themes_data, colWidths=[250, 100, 100])
                themes_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8f9fa")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(self.heading_color)),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e1e8ed")),
                ]))
                
                content.append(themes_table)
                content.append(Spacer(1, 12))
                
                # Add charts if available
                if chart_images:
                    content.append(Paragraph("Visualisations", heading2_style))
                    
                    # Themes bar chart
                    if chart_images.get('themes_bar'):
                        content.append(Paragraph("Theme Distribution", ParagraphStyle(
                            'ChartTitle',
                            parent=normal_style,
                            fontName='Helvetica-Bold'
                        )))
                        img = Image(io.BytesIO(chart_images['themes_bar']))
                        img.drawHeight = 3 * inch
                        img.drawWidth = 5 * inch
                        content.append(img)
                        content.append(Spacer(1, 6))
                    
                    # Classification gauge
                    if chart_images.get('classification_gauge'):
                        content.append(Paragraph("Policy Classification", ParagraphStyle(
                            'ChartTitle',
                            parent=normal_style,
                            fontName='Helvetica-Bold'
                        )))
                        img = Image(io.BytesIO(chart_images['classification_gauge']))
                        img.drawHeight = 3 * inch
                        img.drawWidth = 5 * inch
                        content.append(img)
                        content.append(Spacer(1, 6))
                    
                    # Themes pie chart
                    if chart_images.get('themes_pie'):
                        content.append(Paragraph("Theme Proportions", ParagraphStyle(
                            'ChartTitle',
                            parent=normal_style,
                            fontName='Helvetica-Bold'
                        )))
                        img = Image(io.BytesIO(chart_images['themes_pie']))
                        img.drawHeight = 3 * inch
                        img.drawWidth = 5 * inch
                        content.append(img)
                        content.append(Spacer(1, 6))
                    
                    # Ethics radar chart
                    if chart_images.get('ethics_radar'):
                        content.append(Paragraph("Ethical Dimensions Coverage", ParagraphStyle(
                            'ChartTitle',
                            parent=normal_style,
                            fontName='Helvetica-Bold'
                        )))
                        img = Image(io.BytesIO(chart_images['ethics_radar']))
                        img.drawHeight = 3 * inch
                        img.drawWidth = 5 * inch
                        content.append(img)
                        content.append(Spacer(1, 12))
            
            # Recommendations
            content.append(Paragraph("Strategic Recommendations", heading1_style))
            
            if data.get('recommendations'):
                for i, rec in enumerate(data.get('recommendations', []), 1):
                    # Recommendation title
                    title = rec.get('title', f'Recommendation {i}')
                    content.append(Paragraph(f"{i}. {title}", heading2_style))
                    
                    # Description
                    description = rec.get('description', '')
                    content.append(Paragraph(description, normal_style))
                    content.append(Spacer(1, 6))
                    
                    # Implementation steps
                    if rec.get('implementation_steps'):
                        content.append(Paragraph("Implementation Steps:", ParagraphStyle(
                            'Steps',
                            parent=normal_style,
                            fontName='Helvetica-Bold'
                        )))
                        
                        steps = []
                        for step in rec.get('implementation_steps', []):
                            steps.append(ListItem(Paragraph(step, normal_style)))
                        
                        content.append(ListFlowable(
                            steps,
                            bulletType='1',
                            start=1,
                            bulletFontSize=10,
                            leftIndent=20,
                            bulletFormat='%s.'
                        ))
                        content.append(Spacer(1, 6))
                    
                    # Sources
                    if rec.get('sources'):
                        content.append(Paragraph("Sources:", ParagraphStyle(
                            'Sources',
                            parent=normal_style,
                            fontName='Helvetica-Bold'
                        )))
                        
                        sources = []
                        for source in rec.get('sources', []):
                            sources.append(ListItem(Paragraph(source, ParagraphStyle(
                                'SourceItem',
                                parent=normal_style,
                                fontName='Helvetica-Oblique'
                            ))))
                        
                        content.append(ListFlowable(
                            sources,
                            bulletType='bullet',
                            leftIndent=20
                        ))
                        content.append(Spacer(1, 6))
                    
                    # Timeframe
                    if rec.get('timeframe'):
                        content.append(Paragraph(f"Timeframe: {rec.get('timeframe')}", ParagraphStyle(
                            'Timeframe',
                            parent=normal_style,
                            fontName='Helvetica-Bold',
                            textColor=colors.HexColor(self.accent_color)
                        )))
                    
                    content.append(Spacer(1, 12))
            else:
                content.append(Paragraph("No specific recommendations are available for this policy document.", normal_style))
            
            # Footer
            content.append(Spacer(1, 24))
            content.append(Paragraph(f"Generated by PolicyCraft on {self._format_date(data.get('generated_date', datetime.now().isoformat()))}", ParagraphStyle(
                'Footer',
                parent=normal_style,
                fontSize=8,
                textColor=colors.HexColor("#7f8c8d"),
                alignment=1  # Center alignment
            )))
        else:
            content.append(Paragraph("No data available for export.", normal_style))
        
        # Build PDF
        doc.build(content)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    def export_to_word(self, data: Dict[str, Any]) -> bytes:
        """
        Export recommendations and analysis results to Word document.
        
        Args:
            data: Dictionary containing analysis and recommendations data
            
        Returns:
            Word document as bytes
        """
        doc = Document()
        
        # Set document properties
        doc.core_properties.title = "PolicyCraft Analysis Report"
        doc.core_properties.author = "PolicyCraft"
        doc.core_properties.created = datetime.now()
        
        # Process charts if available
        chart_images = {}
        if data.get('charts'):
            chart_images = self._process_charts_for_export(data['charts'])
        
        # Set margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Cm(2.54)
            section.bottom_margin = Cm(2.54)
            section.left_margin = Cm(2.54)
            section.right_margin = Cm(2.54)
        
        # Title
        title = doc.add_heading("PolicyCraft Analysis Report", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.style.font.color.rgb = RGBColor.from_string(self.title_color.replace('#', ''))
        
        # Document information
        if data and data.get('analysis'):
            analysis = data['analysis']
            doc.add_heading("Document Information", level=1)
            
            # Create document info table
            table = doc.add_table(rows=4, cols=2)
            table.style = 'Table Grid'
            
            # Add data to table
            rows = table.rows
            rows[0].cells[0].text = "Document"
            rows[0].cells[1].text = analysis.get('filename', 'Unknown')
            rows[1].cells[0].text = "Classification"
            rows[1].cells[1].text = analysis.get('classification', 'Unknown')
            rows[2].cells[0].text = "Generated Date"
            rows[2].cells[1].text = self._format_date(data.get('generated_date', 'Unknown'))
            rows[3].cells[0].text = "Total Recommendations"
            rows[3].cells[1].text = str(len(data.get('recommendations', [])))
            
            # Format table
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(10)
            
            doc.add_paragraph()
            
            # Add visualisations section if charts are available
            if chart_images:
                doc.add_heading('Visualisations', level=2)
                
                # Themes bar chart
                if chart_images.get('themes_bar'):
                    doc.add_paragraph('Theme Distribution', style='Heading 3')
                    doc.add_picture(io.BytesIO(chart_images['themes_bar']), width=Cm(15))
                    doc.add_paragraph()
                
                # Classification gauge
                if chart_images.get('classification_gauge'):
                    doc.add_paragraph('Policy Classification', style='Heading 3')
                    doc.add_picture(io.BytesIO(chart_images['classification_gauge']), width=Cm(15))
                    doc.add_paragraph()
                
                # Themes pie chart
                if chart_images.get('themes_pie'):
                    doc.add_paragraph('Theme Proportions', style='Heading 3')
                    doc.add_picture(io.BytesIO(chart_images['themes_pie']), width=Cm(15))
                    doc.add_paragraph()
                
                # Ethics radar chart
                if chart_images.get('ethics_radar'):
                    doc.add_paragraph('Ethical Dimensions Coverage', style='Heading 3')
                    doc.add_picture(io.BytesIO(chart_images['ethics_radar']), width=Cm(15))
                    doc.add_paragraph()
                
                doc.add_paragraph()
            
            # Recommendations
            doc.add_heading("Strategic Recommendations", level=1)
            
            if data.get('recommendations'):
                for i, rec in enumerate(data.get('recommendations', []), 1):
                    # Recommendation title
                    title = rec.get('title', f'Recommendation {i}')
                    doc.add_heading(f"{i}. {title}", level=2)
                    
                    # Description
                    doc.add_paragraph(rec.get('description', ''))
                    
                    # Implementation steps
                    if rec.get('implementation_steps'):
                        p = doc.add_paragraph()
                        p.add_run("Implementation Steps:").bold = True
                        
                        for j, step in enumerate(rec.get('implementation_steps', []), 1):
                            doc.add_paragraph(f"{j}. {step}", style='List Number')
                    
                    # Sources
                    if rec.get('sources'):
                        p = doc.add_paragraph()
                        p.add_run("Sources:").bold = True
                        
                        for source in rec.get('sources', []):
                            p = doc.add_paragraph(source, style='List Bullet')
                            p.style.font.italic = True
                    
                    # Timeframe
                    if rec.get('timeframe'):
                        p = doc.add_paragraph()
                        run = p.add_run(f"Timeframe: {rec.get('timeframe')}")
                        run.bold = True
                        run.font.color.rgb = RGBColor.from_string(self.accent_color.replace('#', ''))
                    
                    doc.add_paragraph()
            else:
                doc.add_paragraph("No specific recommendations are available for this policy document.")
            
            # Footer
            footer = doc.sections[0].footer
            footer_para = footer.paragraphs[0]
            footer_para.text = f"Generated by PolicyCraft on {self._format_date(data.get('generated_date', datetime.now().isoformat()))}"
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            doc.add_paragraph("No data available for export.")
        
        # Save document to memory
        buffer = io.BytesIO()
        doc.save(buffer)
        docx_data = buffer.getvalue()
        buffer.close()
        
        return docx_data
    
    def export_to_excel(self, data: Dict[str, Any]) -> bytes:
        """
        Export recommendations and analysis results to Excel spreadsheet.
        
        Args:
            data: Dictionary containing analysis and recommendations data
            
        Returns:
            Excel spreadsheet as bytes
        """
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer)
        
        # Create formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'font_color': self.title_color,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#f8f9fa',
            'border': 1,
            'border_color': '#e1e8ed',
            'font_color': self.heading_color,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'border_color': '#e1e8ed',
            'font_color': self.text_color,
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True
        })
        
        # Document Information sheet
        info_sheet = workbook.add_worksheet('Document Info')
        info_sheet.set_column('A:A', 20)
        info_sheet.set_column('B:B', 50)
        
        # Add title
        info_sheet.merge_range('A1:B1', 'PolicyCraft Analysis Report', title_format)
        
        if data and data.get('analysis'):
            analysis = data['analysis']
            
            # Add document info
            info_sheet.write('A3', 'Document', header_format)
            info_sheet.write('B3', analysis.get('filename', 'Unknown'), cell_format)
            
            info_sheet.write('A4', 'Classification', header_format)
            info_sheet.write('B4', analysis.get('classification', 'Unknown'), cell_format)
            
            info_sheet.write('A5', 'Generated Date', header_format)
            info_sheet.write('B5', self._format_date(data.get('generated_date', 'Unknown')), cell_format)
            
            info_sheet.write('A6', 'Total Recommendations', header_format)
            info_sheet.write('B6', len(data.get('recommendations', [])), cell_format)
            
            # Themes sheet
            if analysis.get('themes'):
                themes_sheet = workbook.add_worksheet('Themes')
                themes_sheet.set_column('A:A', 40)
                themes_sheet.set_column('B:B', 15)
                themes_sheet.set_column('C:C', 15)
                
                # Add title
                themes_sheet.merge_range('A1:C1', 'Key Themes Analysis', title_format)
                
                # Add header row
                themes_sheet.write('A3', 'Theme', header_format)
                themes_sheet.write('B3', 'Score', header_format)
                themes_sheet.write('C3', 'Confidence', header_format)
                
                # Add theme data
                row = 3
                for theme in analysis.get('themes', []):
                    themes_sheet.write(row, 0, theme.get('name', 'Unknown'), cell_format)
                    themes_sheet.write(row, 1, theme.get('score', 0), cell_format)
                    themes_sheet.write(row, 2, f"{theme.get('confidence', 0)}%", cell_format)
                    row += 1
            
            # Recommendations sheet
            recs_sheet = workbook.add_worksheet('Recommendations')
            recs_sheet.set_column('A:A', 5)
            recs_sheet.set_column('B:B', 30)
            recs_sheet.set_column('C:C', 50)
            recs_sheet.set_column('D:D', 50)
            recs_sheet.set_column('E:E', 50)
            recs_sheet.set_column('F:F', 15)
            
            # Add title
            recs_sheet.merge_range('A1:F1', 'Strategic Recommendations', title_format)
            
            # Add header row
            recs_sheet.write('A3', '#', header_format)
            recs_sheet.write('B3', 'Title', header_format)
            recs_sheet.write('C3', 'Description', header_format)
            recs_sheet.write('D3', 'Implementation Steps', header_format)
            recs_sheet.write('E3', 'Sources', header_format)
            recs_sheet.write('F3', 'Timeframe', header_format)
            
            # Add recommendation data
            row = 3
            for i, rec in enumerate(data.get('recommendations', []), 1):
                recs_sheet.write(row, 0, i, cell_format)
                recs_sheet.write(row, 1, rec.get('title', f'Recommendation {i}'), cell_format)
                recs_sheet.write(row, 2, rec.get('description', ''), cell_format)
                
                # Implementation steps
                steps_text = ""
                for j, step in enumerate(rec.get('implementation_steps', []), 1):
                    steps_text += f"{j}. {step}\n"
                recs_sheet.write(row, 3, steps_text, cell_format)
                
                # Sources
                sources_text = ""
                for source in rec.get('sources', []):
                    sources_text += f"• {source}\n"
                recs_sheet.write(row, 4, sources_text, cell_format)
                
                # Timeframe
                recs_sheet.write(row, 5, rec.get('timeframe', ''), cell_format)
                
                row += 1
        else:
            info_sheet.write('A3', 'No data available for export.', cell_format)
        
        workbook.close()
        excel_data = buffer.getvalue()
        buffer.close()
        
        return excel_data
