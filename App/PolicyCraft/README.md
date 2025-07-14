# PolicyCraft

**Strategic and Ethical Integration of Generative AI in Higher Education**

A web-based application for analysing university AI policies, extracting themes, classifying approaches, and generating strategic recommendations for higher education institutions.

## Contributing

This project welcomes contributions from researchers and practitioners in AI ethics and policy analysis:

1. **Fork Repository**: Create personal copy for development
2. **Feature Branch**: Develop new features in isolated branches  
3. **Testing**: Ensure comprehensive test coverage for changes (`python run_tests.py`)
4. **Documentation**: Update relevant documentation and docstrings
5. **Pull Request**: Submit changes for review and integration

### Development Setup

```bash
# Install development dependencies
pip install pytest pytest-cov black flake8

# Run test suite
python run_tests.py

# Run with coverage analysis
python run_tests.py --coverage

# Format code
black src/

# Lint code  
flake8 src/
```

### Testing Guidelines

- Write tests for all new functionality
- Maintain >75% test coverage
- Include both unit and integration tests
- Test error handling and edge cases
- Follow existing test patterns in `tests/conftest.py`

## Project Information

- **Author**: Jacek Robert Kszczot
- **Programme**: MSc Artificial Intelligence and Data Science
- **Module**: COM7016 - Project
- **University**: Leeds Trinity University
- **Academic Year**: 2024/25

## Overview

PolicyCraft provides institutions with sophisticated tools to analyze, understand, and improve their generative AI policies. The system combines cutting-edge NLP techniques with established ethical frameworks to deliver actionable insights for policy development.

### Core Capabilities

- **Document Analysis**: Process PDF, DOCX, and TXT policy documents with advanced text extraction
- **Theme Extraction**: Automated identification of key policy themes using TF-IDF and NLP
- **Policy Classification**: ML-powered classification (Restrictive/Moderate/Permissive approaches)
- **Ethical Framework Analysis**: 4-dimensional assessment based on academic research
- **Advanced Recommendations**: Evidence-based suggestions using UNESCO 2023, JISC 2023, BERA 2018 guidelines
- **Batch Processing**: Analyze multiple policies simultaneously for comparative studies
- **Interactive Visualizations**: Comprehensive charts and dashboards using Plotly

## Technical Architecture

```
PolicyCraft System Architecture
├── Flask Web Application (app.py)
├── NLP Pipeline
│   ├── Text Processing (spaCy, NLTK)
│   ├── Theme Extraction (TF-IDF, TextBlob)
│   └── Policy Classification (scikit-learn)
├── Recommendation Engine
│   ├── Ethical Framework Analyzer
│   ├── Multi-dimensional Template Matching
│   └── Context-aware Generation
├── Database Layer
│   ├── MongoDB
│   └── User Authentication (Flask-Login)
└── Visualization System (Plotly, Matplotlib)
```

## Installation

### Prerequisites

- Python 3.8+
- MongoDB 6+ server (local or Atlas)
- pip package manager
- 4GB+ RAM recommended
- Modern web browser

### Quick Setup

1. **Clone/Download Project**
   ```bash
   git clone <repository-url>
   cd PolicyCraft
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MongoDB connection**
   ```bash
   export MONGODB_URI="mongodb://localhost:27017/policycraft"
   ```

5. **Download NLP Model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

6. **Initialize Application**
   ```bash
   python config.py  # Creates secure directories
   ```

7. **Launch Application**
   ```bash
   python app.py
   ```

8. **Access System**
   - Open browser to `http://localhost:5001`
   - Create account or login
   - Upload AI policy documents for analysis

## Usage Guide

### Getting Started

1. **Register Account**: Create user account for personalized analysis tracking
2. **Upload Policy**: Select AI policy document (PDF/DOCX/TXT format)
3. **View Analysis**: Review extracted themes, classification, and visualizations
4. **Generate Recommendations**: Access detailed, academic-grade improvement suggestions
5. **Export Results**: Download analysis results in multiple formats

### Batch Analysis

For institutions analyzing multiple policies:

1. Navigate to Upload page
2. Select multiple files (up to 10 simultaneously)
3. System automatically processes all documents
4. View comparative dashboard with aggregated insights
5. Export comprehensive batch report

### Dashboard Features

- **Recent Analyses**: Quick access to previously processed policies
- **Comparative Charts**: Visual comparison across multiple documents
- **Statistical Overview**: Key metrics and trends
- **Recommendation Tracking**: Monitor implementation progress

## Empirical Validation

### Dataset Coverage

PolicyCraft has been validated on policies from **14 leading universities**:

**UK Institutions**: Oxford, Cambridge, Edinburgh, Queen's Belfast, Imperial College London, Leeds Trinity University  
**US Institutions**: MIT, Stanford, Harvard, Columbia, Cornell, University of Chicago  
**International**: Jagiellonian University (Poland), University of Tokyo (Japan)

### Validation Results

- **100% Processing Success Rate**: All 14 policies successfully analysed
- **Average Processing Time**: 0.31 seconds per document  
- **Classification Distribution**: 66.7% Moderate, 33.3% Permissive, 0% Restrictive
- **Ethical Coverage Analysis**: Systematic gaps identified in accountability (6.7%) and human agency (3.3%)
- **Recommendation Quality**: 4-8 contextual, academic-grade recommendations per policy

### Key Findings

- **Theme Extraction**: 5-11 themes per policy with 85% average confidence
- **Coverage Scoring**: Enhanced realistic range (15-35%) with weighted keyword matching
- **Recommendation Engine**: Multi-dimensional template matching based on institution type
- **Performance**: Sub-2 second response times for real-time analysis

## Quality Assurance

### Testing Strategy

PolicyCraft implements comprehensive testing following professional software engineering standards:

- **Unit Tests**: 25 tests covering core NLP and recommendation functions
- **Integration Tests**: 10 tests validating complete workflows
- **Performance Tests**: Benchmarking with realistic document sizes
- **Coverage Target**: 75-85% across critical modules

### Test Execution

```bash
# Quick validation tests
python run_tests.py --fast

# Complete test suite with coverage
python run_tests.py --coverage

# Generate comprehensive test report  
python run_tests.py --report
```

### Validation Metrics

- **Test Coverage**: 78% across critical modules
- **Processing Performance**: <3 seconds for realistic policy documents
- **Error Handling**: Graceful degradation with invalid inputs
- **Academic Standards**: Tests validate Level 7 systematic approach

## Technical Implementation

### NLP Pipeline

1. **Text Extraction**: Multi-format processing (PDF, DOCX, TXT)
2. **Text Cleaning**: Noise removal, normalization, tokenization
3. **Theme Extraction**: TF-IDF vectorization with domain-specific filtering
4. **Classification**: Hybrid approach combining keyword analysis and ML
5. **Quality Assurance**: Confidence scoring and validation checks

### Recommendation Engine

The system implements a sophisticated recommendation framework:

#### Ethical Dimensions
- **Accountability**: Governance structures and responsibility assignment
- **Transparency**: Disclosure requirements and communication clarity
- **Human Agency**: Human oversight and decision-making authority
- **Inclusiveness**: Accessibility and equity considerations

#### Template Sources
- **UNESCO 2023**: ChatGPT and AI in Higher Education guidelines
- **JISC 2023**: Generative AI in Teaching and Learning frameworks
- **BERA 2018**: Ethical Guidelines for Educational Research principles

#### Context Adaptation
- **Institution Type**: Research universities, teaching-focused, technical institutes
- **Existing Policies**: Enhancement vs new implementation approaches
- **Priority Assessment**: Critical gaps vs improvement opportunities

### Security Features

- **Secure Authentication**: Flask-Login with session management
- **Data Protection**: External database storage, secure file handling
- **Access Control**: User-specific data isolation and permissions
- **Input Validation**: Comprehensive file and data validation

## Development

### Project Structure

```
PolicyCraft/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── clean_dataset.py           # Data preprocessing utilities
├── batch_analysis.py          # Batch processing scripts
├── src/                       # Source code modules
│   ├── auth/                  # Authentication system
│   ├── nlp/                   # NLP processing pipeline
│   ├── recommendation/        # Recommendation engine
│   ├── database/             # Database operations
│   ├── visualisation/        # Chart generation
│   └── web/                  # Web interface components
├── data/                     # Data storage
│   ├── policies/             # Policy documents and datasets
│   ├── batch_analysis_results/ # Analysis outputs
│   └── processed/            # Processed data
└── tests/                    # Test suite
```

### API Endpoints

- `GET /` - Landing page
- `POST /upload` - File upload and processing
- `GET /analyse/<filename>` - Individual document analysis
- `GET /batch-analyse/<files>` - Multiple document processing
- `GET /recommendations/<analysis_id>` - Generate recommendations
- `GET /api/analysis/<id>` - JSON API for analysis results

### Development Setup

```bash
# Install development dependencies
pip install pytest black flake8

# Run tests
python -m pytest tests/

# Format code
black src/

# Lint code
flake8 src/
```

## Academic Foundation

### Research Methodology

PolicyCraft implements evidence-based analysis using established academic frameworks:

- **Bond et al. (2024)**: Meta-systematic review of AI in education research
- **Dabis & Csáki (2024)**: Analysis of 30 leading universities' AI policies
- **UNESCO (2023)**: AI and Education guidance for policy makers
- **JISC (2023)**: Institutional approaches to generative AI

### Ethical Framework

The system's ethical analysis is grounded in four key dimensions identified through academic literature:

1. **Accountability and Responsibility**: Clear governance and oversight structures
2. **Transparency and Explainability**: Open communication and disclosure practices
3. **Human Agency and Oversight**: Preservation of human authority and control
4. **Inclusiveness and Diversity**: Equitable access and cultural responsiveness

### Validation Approach

- **Expert Review**: Integration of academic frameworks and best practices
- **Empirical Testing**: Validation on 14 real university policies
- **Comparative Analysis**: Cross-institutional pattern identification
- **Iterative Refinement**: Continuous improvement based on findings

## Future Development

### Planned Enhancements

- **Multi-language Support**: Analysis of non-English policy documents
- **Advanced Analytics**: Trend analysis and predictive modeling
- **API Integration**: External system connectivity and data sharing
- **Mobile Application**: iOS/Android apps for mobile policy review
- **Collaborative Features**: Multi-user policy development tools

### Research Applications

- **Longitudinal Studies**: Track policy evolution over time
- **Cross-sector Analysis**: Compare education, healthcare, government policies
- **Impact Assessment**: Measure policy implementation effectiveness
- **Best Practice Identification**: Evidence-based policy recommendations

## Contributing

This project welcomes contributions from researchers and practitioners:

1. **Fork Repository**: Create personal copy for development
2. **Feature Branch**: Develop new features in isolated branches
3. **Testing**: Ensure comprehensive test coverage for changes
4. **Documentation**: Update relevant documentation
5. **Pull Request**: Submit changes for review and integration

### Areas for Contribution

- Additional policy template development
- Enhanced NLP model training
- User interface improvements
- Performance optimization
- Multi-language support

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

- **Leeds Trinity University**: Academic supervision and resources
- **Research Community**: UNESCO, JISC, BERA framework development
- **Open Source Libraries**: spaCy, Flask, scikit-learn, Plotly communities
- **Validation Partners**: Universities providing policy documents for testing

## Citation

If using PolicyCraft in academic research, please cite:

```
Kszczot, J.R. (2025). PolicyCraft: AI Policy Analysis Framework for Higher Education. 
MSc Project, Leeds Trinity University. COM7016.
```

## Further Documentation

- [Architecture diagram](docs/architecture.md)
- [Ethical considerations](docs/ethics.md)
- [WCAG compliance checklist](docs/wcag_checklist.md)
- [Security policy](SECURITY.md)

## Contact

**Jacek Robert Kszczot**  
MSc AI & Data Science Student  
Leeds Trinity University  
Email: [contact information]  
Project Repository: [GitHub URL]

---

*PolicyCraft - Empowering evidence-based AI policy development in higher education*