# PolicyCraft

**Strategic and Ethical Integration of Generative AI in Higher Education**

A web-based application for analysing university AI policies, extracting themes, classifying approaches, and generating strategic recommendations for higher education institutions.

## Project Information

- **Author**: Jacek Robert Kszczot
- **Programme**: MSc Artificial Intelligence and Data Science
- **Module**: COM7016 - Project
- **University**: Leeds Trinity University
- **Supervisors**: Dr Xin Lu, Dr Yashar Baradaranshokouhi

## Overview

This application provides a comprehensive framework for analysing generative AI policies in higher education. It combines Natural Language Processing (NLP), machine learning classification, and interactive visualisations to help institutions understand policy trends and develop strategic approaches to AI integration.

### Key Features

- **Policy Document Analysis**: Upload and analyse university AI policy documents (PDF, DOCX, TXT)
- **Theme Extraction**: Automatically extract key themes and topics from policy documents
- **Policy Classification**: Classify policies as restrictive, permissive, or balanced approaches
- **Interactive Dashboard**: Visualise trends and patterns across multiple institutions
- **Recommendation Engine**: Generate tailored policy recommendations based on analysis
- **Comparative Analysis**: Compare different institutional approaches to AI governance

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Interface │    │   NLP Engine     │    │   Database      │
│   (Flask)       │◄──►│   (spaCy/NLTK)   │◄──►│   (MongoDB)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Visualisation  │    │ Recommendation   │    │   File Storage  │
│  (Plotly/MPL)   │    │    Engine        │    │   (Local/PDF)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository** (or create project structure):
   ```bash
   git clone <repository-url>
   cd GenAI-Higher-Ed-Policy-Framework
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy language model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Create necessary directories**:
   ```bash
   python config.py
   ```

6. **Run the application**:
   ```bash
   python app.py
   ```

7. **Access the application**:
   Open your web browser and navigate to `http://localhost:5000`

## Usage

### 1. Upload Policy Documents

1. Navigate to the Upload page
2. Select a policy document (PDF, DOCX, or TXT)
3. Click "Upload and Analyse"

### 2. View Analysis Results

- **Themes**: Key topics and concepts extracted from the policy
- **Classification**: Policy approach (Restrictive/Permissive/Balanced)
- **Statistics**: Document length, complexity metrics
- **Visualisations**: Charts showing theme distribution

### 3. Dashboard

- Compare multiple policies
- View aggregated statistics
- Analyse trends across institutions
- Export visualisations

### 4. Recommendations

- Get tailored policy recommendations
- Compare with similar institutions
- Download recommendation reports

## Technical Details

### NLP Pipeline

1. **Text Extraction**: Extract text from uploaded documents
2. **Preprocessing**: Clean and normalise text data
3. **Theme Extraction**: Use TF-IDF and topic modeling to identify themes
4. **Classification**: Machine learning classification of policy approaches
5. **Sentiment Analysis**: Analyse policy tone and stance

### Database Schema

- **Policies Collection**: Store original policy documents and metadata
- **Analyses Collection**: Store analysis results and extracted features
- **Themes Collection**: Store theme definitions and frequencies
- **Recommendations Collection**: Store generated recommendations

### API Endpoints

- `GET /api/analysis/<id>` - Retrieve analysis results
- `POST /api/upload` - Upload new policy document
- `GET /api/dashboard/stats` - Get dashboard statistics

## Development

### Project Structure

```
GenAI-Higher-Ed-Policy-Framework/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── src/                           # Source code
│   ├── nlp/                       # NLP processing modules
│   ├── web/                       # Web interface components
│   ├── recommendation/            # Recommendation engine
│   ├── database/                  # Database operations
│   └── visualisation/             # Chart generation
├── data/                          # Data storage
│   ├── policies/                  # Policy documents
│   ├── processed/                 # Processed data
│   └── results/                   # Analysis results
└── tests/                         # Test files
```

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

This project follows PEP 8 style guidelines. Use `black` for code formatting:

```bash
black src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Data Sources

The application analyses AI policies from various universities including:

- Stanford University
- MIT
- Oxford University
- Cambridge University
- Imperial College London
- Columbia University

## Ethical Considerations

This project adheres to ethical research practices:

- No personal data collection
- Publicly available policy documents only
- Transparent analysis methods
- Open source implementation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Leeds Trinity University
- JISC AI in Education Guidelines
- spaCy and NLTK communities
- Flask development community

## Contact

**Jacek Robert Kszczot**  
MSc AI & Data Science Student  
Leeds Trinity University  
Email: [student email]

**Project Supervisors**:
- Dr Xin Lu (Primary Supervisor)
- Dr Yashar Baradaranshokouhi (Secondary Supervisor)

---

*This project is part of the MSc AI & Data Science programme at Leeds Trinity University, Module COM7016.*