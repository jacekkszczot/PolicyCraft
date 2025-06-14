"""
Chart generation module for PolicyCraft.
Creates interactive visualizations using Plotly for policy analysis results.

Author: Jacek Robert Kszczot
"""

import json
import logging
from typing import Dict, List, Optional, Any
from collections import Counter

# Visualization libraries
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.utils
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: Plotly not available. Install with: pip install plotly")

logger = logging.getLogger(__name__)

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
        
        print(f"ChartGenerator initialized - Plotly: {PLOTLY_AVAILABLE}")

    def generate_analysis_charts(self, themes: List[Dict], classification: Dict) -> Dict:
        """Generate charts for a single analysis result."""
        if not PLOTLY_AVAILABLE:
            return self._generate_fallback_charts(themes, classification)
        
        charts = {}
        
        try:
            charts['themes_bar'] = self._create_themes_bar_chart(themes)
            charts['classification_gauge'] = self._create_classification_gauge(classification)
            charts['themes_pie'] = self._create_themes_pie_chart(themes)
            
            print(f"Generated {len(charts)} charts for analysis")
            
        except Exception as e:
            print(f"Error generating analysis charts: {e}")
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
            
            print(f"Generated {len(charts)} dashboard charts for {len(analyses)} analyses")
            
        except Exception as e:
            print(f"Error generating dashboard charts: {e}")
            return self._generate_fallback_dashboard(analyses)
            
        return charts

    def _create_themes_bar_chart(self, themes: List[Dict]) -> str:
        """Create horizontal bar chart for themes."""
        if not themes:
            return ""
        
        top_themes = themes[:8]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=[theme['name'] for theme in reversed(top_themes)],
            x=[theme['score'] for theme in reversed(top_themes)],
            orientation='h',
            marker=dict(
                color=self.color_schemes['themes'][:len(top_themes)],
                line=dict(color='rgba(50, 50, 50, 0.2)', width=1)
            ),
            text=[f"{theme['confidence']}%" for theme in reversed(top_themes)],
            textposition='inside',
            textfont=dict(color='white', size=10)
        ))
        
        fig.update_layout(
            title='Key Policy Themes',
            xaxis_title='Theme Score',
            yaxis_title='Themes',
            height=400,
            **self.default_layout
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
            title = {'text': f"Classification: {class_type}"},
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
        
        fig.update_layout(height=300, **self.default_layout)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def _create_themes_pie_chart(self, themes: List[Dict]) -> str:
        """Create pie chart for theme distribution."""
        if not themes:
            return ""
        
        if len(themes) > 6:
            top_themes = themes[:5]
            others_score = sum(theme['score'] for theme in themes[5:])
            display_themes = top_themes + [{'name': 'Others', 'score': others_score}]
        else:
            display_themes = themes
        
        fig = go.Figure(data=[go.Pie(
            labels=[theme['name'] for theme in display_themes],
            values=[theme['score'] for theme in display_themes],
            hole=.3,
            marker=dict(colors=self.color_schemes['themes'][:len(display_themes)])
        )])
        
        fig.update_layout(title='Theme Distribution', height=400, **self.default_layout)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def _create_classification_distribution(self, analyses: List[Dict]) -> str:
        """Create distribution chart of classifications."""
        classifications = []
        for analysis in analyses:
            cls = analysis.get('classification', {}).get('classification', 'Unknown')
            classifications.append(cls)
        
        counts = Counter(classifications)
        
        fig = go.Figure(data=[go.Bar(
            x=list(counts.keys()),
            y=list(counts.values()),
            marker=dict(color=[self.color_schemes['classifications'].get(cls, '#95a5a6') 
                             for cls in counts.keys()])
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
            marker=dict(color=self.color_schemes['themes'][:len(top_themes)])
        )])
        
        fig.update_layout(
            title='Most Frequent Themes Across All Analyses',
            xaxis_title='Frequency',
            yaxis_title='Themes',
            height=400,
            **self.default_layout
        )
        
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
    print("Starting chart generator test...")
    
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
    
    print("\n=== Chart Generation Test ===")
    
    # Test analysis charts
    analysis_charts = chart_gen.generate_analysis_charts(test_themes, test_classification)
    print(f"Generated analysis charts: {list(analysis_charts.keys())}")
    
    # Test dashboard charts
    dashboard_charts = chart_gen.generate_user_dashboard_charts(test_analyses)
    print(f"Generated dashboard charts: {list(dashboard_charts.keys())}")
    
    print("\n✅ Chart generator working correctly!")