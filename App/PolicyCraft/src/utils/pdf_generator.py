"""
PDF Export functionality for PolicyCraft analysis results.
"""

import os
from datetime import datetime
from typing import Dict, List
import json

# PDF Libraries
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class PDFExporter:
    """Generate PDF reports from PolicyCraft analysis results."""
    
    def __init__(self):
        """Initialize PDF exporter with styles."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab not available. Install with: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        ))
        
        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.HexColor('#2980b9')
        ))
    
    def generate_analysis_report(self, results: Dict, output_path: str) -> bool:
        """
        Generate PDF report for single analysis.
        
        Args:
            results: Analysis results dictionary
            output_path: Path where PDF should be saved
            
        Returns:
            bool: Success status
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build story (content)
            story = []
            
            # Title page
            story.append(Paragraph("PolicyCraft Analysis Report", self.styles['CustomTitle']))
            story.append(Spacer(1, 20))
            
            # Document info
            filename = results.get('filename', 'Unknown')
            clean_filename = filename.split('_', 2)[-1] if '_' in filename else filename
            
            story.append(Paragraph(f"Document: {clean_filename}", self.styles['CustomSubtitle']))
            story.append(Paragraph(f"Analysis Date: {results.get('analysis_date', 'Unknown')}", self.styles['Normal']))
            story.append(Spacer(1, 30))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
            
            classification = results.get('classification', {})
            summary_text = f"""
            This analysis examined the AI policy document "{clean_filename}" using PolicyCraft's 
            research-grade analysis framework. The policy was classified as 
            <b>{classification.get('classification', 'Unknown')}</b> with 
            {classification.get('confidence', 0)}% confidence. 
            The analysis identified {len(results.get('themes', []))} key themes 
            and provided evidence-based recommendations for improvement.
            """
            story.append(Paragraph(summary_text, self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Classification Results
            story.append(Paragraph("Policy Classification", self.styles['SectionHeading']))
            
            classification_data = [
                ['Classification Type', classification.get('classification', 'Unknown')],
                ['Confidence Score', f"{classification.get('confidence', 0)}%"],
                ['Analysis Method', classification.get('method', 'Hybrid NLP')],
            ]
            
            classification_table = Table(classification_data, colWidths=[2.5*inch, 3*inch])
            classification_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(classification_table)
            story.append(Spacer(1, 20))
            
            # Theme Analysis
            story.append(Paragraph("Key Themes Identified", self.styles['SectionHeading']))
            
            themes = results.get('themes', [])
            if themes:
                theme_data = [['Theme', 'Relevance Score', 'Confidence']]
                for theme in themes[:10]:  # Top 10 themes
                    theme_data.append([
                        theme.get('name', 'Unknown'),
                        str(theme.get('score', 0)),
                        f"{theme.get('confidence', 0)}%"
                    ])
                
                theme_table = Table(theme_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
                theme_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                
                story.append(theme_table)
            else:
                story.append(Paragraph("No themes identified in this analysis.", self.styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # Text Statistics
            text_stats = results.get('text_stats', {})
            if text_stats:
                story.append(Paragraph("Document Statistics", self.styles['SectionHeading']))
                
                stats_data = [
                    ['Word Count', f"{text_stats.get('word_count', 'N/A'):,}"],
                    ['Sentence Count', f"{text_stats.get('sentence_count', 'N/A'):,}"],
                    ['Average Sentence Length', f"{text_stats.get('avg_sentence_length', 'N/A'):.1f} words"],
                    ['Average Word Length', f"{text_stats.get('avg_word_length', 'N/A'):.1f} characters"],
                ]
                
                stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                story.append(stats_table)
                story.append(Spacer(1, 20))
            
            # Page break before recommendations
            story.append(PageBreak())
            
            # Recommendations Section (if available)
            if 'recommendations' in results:
                story.append(Paragraph("Recommendations", self.styles['SectionHeading']))
                story.append(Paragraph(
                    "The following recommendations are generated based on analysis of the policy "
                    "against established ethical frameworks and academic best practices.",
                    self.styles['Normal']
                ))
                story.append(Spacer(1, 15))
                
                # This would be populated when recommendations are working
                story.append(Paragraph("Recommendations feature coming soon.", self.styles['Normal']))
            
            # Footer
            story.append(Spacer(1, 30))
            story.append(Paragraph(
                f"Generated by PolicyCraft v1.0 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                "PolicyCraft: AI Policy Analysis for Higher Education",
                self.styles['Normal']
            ))
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return False


def generate_csv_export(results: Dict, output_path: str) -> bool:
    """
    Generate CSV export of analysis results.
    
    Args:
        results: Analysis results dictionary
        output_path: Path where CSV should be saved
        
    Returns:
        bool: Success status
    """
    try:
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header information
            writer.writerow(['PolicyCraft Analysis Export'])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # Document information
            writer.writerow(['Document Information'])
            filename = results.get('filename', 'Unknown')
            clean_filename = filename.split('_', 2)[-1] if '_' in filename else filename
            writer.writerow(['Filename', clean_filename])
            writer.writerow(['Analysis Date', results.get('analysis_date', 'Unknown')])
            writer.writerow([])
            
            # Classification
            classification = results.get('classification', {})
            writer.writerow(['Policy Classification'])
            writer.writerow(['Type', classification.get('classification', 'Unknown')])
            writer.writerow(['Confidence', f"{classification.get('confidence', 0)}%"])
            writer.writerow(['Method', classification.get('method', 'Hybrid')])
            writer.writerow([])
            
            # Themes
            themes = results.get('themes', [])
            if themes:
                writer.writerow(['Themes'])
                writer.writerow(['Theme Name', 'Relevance Score', 'Confidence %'])
                for theme in themes:
                    writer.writerow([
                        theme.get('name', 'Unknown'),
                        theme.get('score', 0),
                        theme.get('confidence', 0)
                    ])
                writer.writerow([])
            
            # Text Statistics
            text_stats = results.get('text_stats', {})
            if text_stats:
                writer.writerow(['Document Statistics'])
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Word Count', text_stats.get('word_count', 'N/A')])
                writer.writerow(['Sentence Count', text_stats.get('sentence_count', 'N/A')])
                writer.writerow(['Avg Sentence Length', f"{text_stats.get('avg_sentence_length', 0):.1f}"])
                writer.writerow(['Avg Word Length', f"{text_stats.get('avg_word_length', 0):.1f}"])
        
        return True
        
    except Exception as e:
        print(f"Error generating CSV: {str(e)}")
        return False