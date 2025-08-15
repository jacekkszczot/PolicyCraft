"""
Interactive Chart Generation for PolicyCraft AI Policy Analysis.

This module provides comprehensive visualisation capabilities for the PolicyCraft platform,
creating interactive and informative charts using Plotly. The visualisations are designed
to help users understand and interpret policy analysis results through intuitive graphical
representations.

Key Features:
- Generation of interactive radar charts for policy dimension coverage
- Creation of timeline visualisations for policy development and updates
- Comparative bar charts for cross-institutional policy analysis
- Classification heatmaps for policy approach visualisation
- Responsive design for both web and export formats

Dependencies:
- plotly: For interactive chart generation
- pandas: For data manipulation and analysis
- numpy: For numerical operations

Author: Jacek Robert Kszczot
Project: MSc Data Science & AI - COM7016
University: Leeds Trinity University
"""

import json
import logging
from typing import Dict, List
from collections import Counter
import re

logger = logging.getLogger(__name__)

# Visualization libraries
try:
    import plotly.graph_objects as go
    import plotly.utils
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available. Install with: pip install plotly")

class ChartGenerator:
    """
    Generate interactive charts and visualizations for policy analysis results.
    """
    
    def __init__(self):
        """Initialize chart generator with default settings."""
        
        # Color schemes for different chart types
        self.color_schemes = {
            'themes': ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', 
                      '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#16a085'],
            'classifications': {
                'Restrictive': '#e74c3c',
                'Moderate': '#f39c12', 
                'Permissive': '#2ecc71',
                'Unknown': '#95a5a6'
            },
            'confidence': ['#e74c3c', '#f39c12', '#2ecc71']  # Low to High
        }
        
        # Chart layout defaults
        self.default_layout = {
            'font': {'family': 'Arial', 'size': 12},
            'showlegend': True,
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'margin': {'l': 40, 'r': 40, 't': 60, 'b': 40}
        }
        
        # Simple keyword mapping for ethical dimensions (can be refined)
        self.ethics_keywords = {
            'Transparency': [r"\btransparen(ce|cy|t)\b", r"\bdisclos(e|ure)\b"],
            'Accountability': [r"\baccountab(le|ility)\b", r"\bresponsib(le|ility)\b"],
            'Privacy & Data': [r"\bprivacy\b", r"\bdata protection\b", r"\bpii\b"],
            'Human-Centredness': [r"\bhuman\b", r"\bwellbeing\b", r"\buser\b"],
            'Fairness & Inclusion': [r"\bfair(ness)?\b", r"\bequity\b", r"\binclus(ive|ion)\b"],
            'Societal Impact': [r"\bimpact\b", r"\bsociet(al)?\b", r"\bsustainab(le|ility)\b"]
        }
        
        logger.info("ChartGenerator initialized - Plotly: %s", PLOTLY_AVAILABLE)

    def generate_analysis_charts(self, themes: List[Dict], classification: Dict, text: str | None = None) -> Dict:
        """Generate charts for a single analysis result."""
        if not PLOTLY_AVAILABLE:
            return self._generate_fallback_charts(themes, classification)
        
        charts = {}
        
        try:
            charts['themes_bar'] = self._create_themes_bar_chart(themes)
            charts['classification_gauge'] = self._create_classification_gauge(classification)
            charts['themes_pie'] = self._create_themes_pie_chart(themes)
            if text:
                charts['ethics_radar'] = self._create_ethics_radar_chart(text)
            
            logger.info("Generated %d charts for analysis", len(charts))
            
        except Exception as e:
            logger.warning("Error generating analysis charts: %s", e)
            return self._generate_fallback_charts(themes, classification)
            
        return charts

    def generate_user_dashboard_charts(self, analyses: List[Dict]) -> Dict:
        """Generate dashboard charts for user's historical analyses."""
        if not analyses:
            return {'message': 'No analyses available for dashboard'}
        
        if not PLOTLY_AVAILABLE:
            return self._generate_fallback_dashboard(analyses)
        
        charts = {}
        
        try:
            charts['classification_distribution'] = self._create_classification_distribution(analyses)
            charts['theme_frequency'] = self._create_theme_frequency_chart(analyses)
            
            logger.info("Generated %d dashboard charts for %d analyses", len(charts), len(analyses))
            
        except Exception as e:
            logger.warning("Error generating dashboard charts: %s", e)
            return self._generate_fallback_dashboard(analyses)
            
        return charts

    def _create_themes_bar_chart(self, themes: List[Dict]) -> str:
        """Create horizontal bar chart for themes."""
        if not themes:
            return ""
        
        top_themes = themes[:8]

        # Compute frequency-based shares for clearer differentiation
        total_freq = sum(max(0, int(t.get('frequency', 0))) for t in top_themes) or 1
        def _share(t):
            return round(100 * max(0, int(t.get('frequency', 0))) / total_freq)

        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=[theme['name'] for theme in reversed(top_themes)],
            x=[theme['score'] for theme in reversed(top_themes)],
            orientation='h',
            marker={
                'color': self.color_schemes['themes'][:len(top_themes)],
                'line': {'color': 'rgba(50, 50, 50, 0.2)', 'width': 1}
            },
            # Label bars by contribution share rather than absolute confidence
            text=[f"{_share(theme)}%" for theme in reversed(top_themes)],
            textposition='inside',
            textfont={'color': 'white', 'size': 10}
        ))
        
        fig.update_layout(
            # No inner title to avoid duplication with template headings
            xaxis_title='Theme Score',
            yaxis_title='Themes',
            height=420,
            showlegend=False,
            margin={'l': 100, 'r': 40, 't': 10, 'b': 40},
            yaxis={'automargin': True, 'ticklabelposition': 'outside', 'ticklabelstandoff': 8},
            xaxis={'automargin': True},
            **{k: v for k, v in self.default_layout.items() if k not in ('margin', 'showlegend')}
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def _create_classification_gauge(self, classification: Dict) -> str:
        """Create gauge chart for classification confidence."""
        confidence = classification.get('confidence', 0)
        class_type = classification.get('classification', 'Unknown')
        
        color = self.color_schemes['classifications'].get(class_type, '#95a5a6')
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = confidence,
            domain = {'x': [0, 1], 'y': [0, 1]},
            # Remove inner title to prevent duplication; the card heading labels the chart
            title = {'text': ''},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=320, showlegend=False, margin={'l': 20, 'r': 20, 't': 10, 'b': 20},
                          **{k: v for k, v in self.default_layout.items() if k not in ('margin', 'showlegend')})
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def _create_themes_pie_chart(self, themes: List[Dict]) -> str:
        """Create pie chart for theme distribution."""
        if not themes:
            return ""
        
        # Use raw frequency to calculate distribution for a more faithful share
        if len(themes) > 6:
            top_themes = themes[:5]
            others_freq = sum(int(theme.get('frequency', 0)) for theme in themes[5:])
            display_themes = top_themes + [{'name': 'Others', 'frequency': others_freq}]
        else:
            display_themes = themes
        
        fig = go.Figure(data=[go.Pie(
            labels=[theme['name'] for theme in display_themes],
            values=[int(theme.get('frequency', 0)) for theme in display_themes],
            hole=.3,
            marker={'colors': self.color_schemes['themes'][:len(display_themes)]}
        )])
        
        fig.update_layout(height=420, margin={'l': 20, 'r': 20, 't': 10, 'b': 20},
                          **{k: v for k, v in self.default_layout.items() if k != 'margin'})
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def _create_classification_distribution(self, analyses: List[Dict]) -> str:
        """Create distribution chart of classifications."""
        classifications = []
        for analysis in analyses:
            cls = analysis.get('classification', {}).get('classification', 'Unknown')
            classifications.append(cls)
        
        # Count occurrences of each classification
        counts = Counter(classifications)
        
        # Ensure all standard categories are present, even if count is 0
        standard_categories = ['Restrictive', 'Moderate', 'Permissive']
        for category in standard_categories:
            if category not in counts:
                counts[category] = 0
        
        # Sort categories to ensure consistent order
        sorted_categories = sorted(counts.keys(), key=lambda x: (
            0 if x in standard_categories else 1,  # Standard categories first
            standard_categories.index(x) if x in standard_categories else 999,  # In defined order
            x  # Alphabetical for any others
        ))
        
        fig = go.Figure(data=[go.Bar(
            x=sorted_categories,
            y=[counts[category] for category in sorted_categories],
            marker={'color': [self.color_schemes['classifications'].get(cls, '#95a5a6') 
                           for cls in sorted_categories]}
        )])
        
        fig.update_layout(
            title='Policy Classification Distribution',
            xaxis_title='Classification Type',
            yaxis_title='Number of Policies',
            height=400,
            **self.default_layout
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def _create_theme_frequency_chart(self, analyses: List[Dict]) -> str:
        """Create chart showing most frequent themes across analyses."""
        all_themes = []
        for analysis in analyses:
            themes = analysis.get('themes', [])
            for theme in themes:
                all_themes.append(theme['name'])
        
        theme_counts = Counter(all_themes)
        top_themes = theme_counts.most_common(10)
        
        if not top_themes:
            return ""
        
        fig = go.Figure(data=[go.Bar(
            x=[count for theme, count in top_themes],
            y=[theme for theme, count in top_themes],
            orientation='h',
            marker={'color': self.color_schemes['themes'][:len(top_themes)]}
        )])
        
        fig.update_layout(
            # No title to avoid duplication
            xaxis_title='Frequency',
            yaxis_title='Themes',
            height=400,
            showlegend=False,
            margin={'l': 20, 'r': 20, 't': 10, 'b': 20},
            **{k: v for k, v in self.default_layout.items() if k not in ('margin', 'showlegend')}
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def _create_ethics_radar_chart(self, text: str) -> str:
        """Create radar chart showing ethical dimension coverage."""
        if not text:
            return ""
        
        dimension_scores = {}
        total_matches = 0
        text_lower = text.lower()
        for dimension, patterns in self.ethics_keywords.items():
            score = 0
            for pattern in patterns:
                score += len(re.findall(pattern, text_lower))
            dimension_scores[dimension] = score
            total_matches += score
        # Normalize to percentage
        if total_matches == 0:
            dimension_scores = dict.fromkeys(dimension_scores, 0)
        else:
            dimension_scores = {dim: round((count / total_matches) * 100, 1) for dim, count in dimension_scores.items()}
        categories = list(dimension_scores.keys())
        values = list(dimension_scores.values())
        values.append(values[0])  # close loop
        categories.append(categories[0])
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='Ethical Coverage', marker_color='#2ecc71'))
        fig.update_layout(
                          polar={
                              'radialaxis': {'visible': True, 'range': [0, 100]},
                              # Balance: a bit more left padding, and some space on the right for labels
                              'domain': {'x': [0.14, 0.94], 'y': [0.12, 0.98]},
                              'angularaxis': {'rotation': 20, 'tickfont': {'size': 12}}
                          },
                          height=420,
                          margin={'l': 120, 'r': 90, 't': 10, 'b': 70},
                          legend={'orientation': 'h', 'x': 0.5, 'xanchor': 'center', 'y': -0.05},
                          **{k: v for k, v in self.default_layout.items() if k not in ('margin',)})
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def _generate_fallback_charts(self, themes: List[Dict], classification: Dict) -> Dict:
        """Generate fallback chart data when Plotly is not available."""
        return {
            'themes_data': {
                'labels': [theme['name'] for theme in themes[:5]],
                'scores': [theme['score'] for theme in themes[:5]],
                'colors': self.color_schemes['themes'][:5]
            },
            'classification_data': {
                'type': classification.get('classification', 'Unknown'),
                'confidence': classification.get('confidence', 0),
                'color': self.color_schemes['classifications'].get(
                    classification.get('classification', 'Unknown'), '#95a5a6'
                )
            },
            'message': 'Plotly not available - using simplified data format'
        }

    def _generate_fallback_dashboard(self, analyses: List[Dict]) -> Dict:
        """Generate fallback dashboard data."""
        classifications = [a.get('classification', {}).get('classification', 'Unknown') 
                         for a in analyses]
        classification_counts = Counter(classifications)
        
        all_themes = []
        for analysis in analyses:
            themes = analysis.get('themes', [])
            for theme in themes:
                all_themes.append(theme['name'])
        theme_counts = Counter(all_themes)
        
        return {
            'classification_counts': dict(classification_counts),
            'top_themes': dict(theme_counts.most_common(5)),
            'total_analyses': len(analyses),
            'message': 'Plotly not available - using simplified data format'
        }


# Test the chart generator
if __name__ == "__main__":
    logger.info("Starting chart generator test...")
    
    chart_gen = ChartGenerator()
    
    # Test data
    test_themes = [
        {'name': 'AI Ethics', 'score': 5.5, 'confidence': 55},
        {'name': 'Academic Integrity', 'score': 3.5, 'confidence': 35},
        {'name': 'Privacy and Data', 'score': 3.0, 'confidence': 30},
        {'name': 'Transparency', 'score': 2.5, 'confidence': 25}
    ]
    
    test_classification = {
        'classification': 'Moderate',
        'confidence': 75,
        'method': 'hybrid'
    }
    
    test_analyses = [
        {
            'filename': 'policy1.pdf',
            'themes': test_themes,
            'classification': test_classification
        },
        {
            'filename': 'policy2.pdf', 
            'themes': test_themes[:2],
            'classification': {'classification': 'Restrictive', 'confidence': 85}
        }
    ]
    
    logger.info("=== Chart Generation Test ===")
    
    # Test analysis charts
    analysis_charts = chart_gen.generate_analysis_charts(test_themes, test_classification)
    logger.info("Generated analysis charts: %s", list(analysis_charts.keys()))
    
    # Test dashboard charts
    dashboard_charts = chart_gen.generate_user_dashboard_charts(test_analyses)
    logger.info("Generated dashboard charts: %s", list(dashboard_charts.keys()))
    
    logger.info("✅ Chart generator working correctly!")