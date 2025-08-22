# PolicyCraft

**Strategic and Ethical Integration of Generative AI in Higher Education**

A web-based application for analysing university AI policies, extracting themes, classifying approaches, and generating strategic recommendations for higher education institutions.

## 🚀 Quick Start Installation

**Get PolicyCraft running in minutes with these simple steps:**

### 1. Prerequisites (First Time Setup)
**If this is your first time using Python or you're on a fresh computer:**

#### Install Python
- **macOS**: Download from [python.org](https://python.org) or use Homebrew: `brew install python`
- **Windows**: Download from [python.org](https://python.org) - make sure to check "Add Python to PATH"
- **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install python3 python3-pip python3-venv`

#### Verify Python Installation
```bash
python --version  # Should show Python 3.9 or higher
pip --version     # Should show pip version
```

### 2. Clone and Navigate
```bash
git clone https://github.com/yourusername/PolicyCraft.git
cd PolicyCraft
```

### 3. Create Virtual Environment (Required)
**Virtual environments keep your project dependencies isolated from other Python projects.**

#### macOS/Linux:
```bash
python3 -m venv policycraft-env
source policycraft-env/bin/activate
```

#### Windows:
```bash
python -m venv policycraft-env
policycraft-env\Scripts\activate
```

**You'll know it's activated when you see `(policycraft-env)` at the start of your command line.**

#### Example Terminal Session
```bash
# Your command line should look like this:
username@computer:~$ cd PolicyCraft
username@computer:~/PolicyCraft$ python3 -m venv policycraft-env
username@computer:~/PolicyCraft$ source policycraft-env/bin/activate
(policycraft-env) username@computer:~/PolicyCraft$ pip install -r requirements.txt
# ... installation progress ...
(policycraft-env) username@computer:~/PolicyCraft$ python -m spacy download en_core_web_sm
# ... model download ...
(policycraft-env) username@computer:~/PolicyCraft$ python app.py
# ... application starts ...
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```
**This may take several minutes as it downloads and installs all required packages.**

### 5. Download Required Models
```bash
# Download spaCy English model (required for NLP processing)
python -m spacy download en_core_web_sm

# Download NLTK data (for enhanced text analysis)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"
```
**These models are essential for text analysis and may take a few minutes to download.**

### 6. Run the Application
```bash
python app.py
```

**🎉 That's it!** Open http://localhost:5001 in your browser to access PolicyCraft.

### 7. Verify Installation (Optional)
```bash
python check_setup.py
```
This script will verify that all components are properly installed and configured.

---

## 🚨 Common Issues & Solutions

### First Time Setup Issues

#### Python Not Found
```bash
# If you get "python: command not found" or "python3: command not found"
# macOS: brew install python
# Windows: Download from python.org and check "Add to PATH"
# Linux: sudo apt install python3 python3-pip python3-venv
```

#### pip Not Found
```bash
# If you get "pip: command not found"
# macOS: brew install python (includes pip)
# Windows: Download from python.org (includes pip)
# Linux: sudo apt install python3-pip
```

#### Virtual Environment Issues
**Always activate your virtual environment before running commands:**
```bash
# macOS/Linux:
source policycraft-env/bin/activate

# Windows:
policycraft-env\Scripts\activate

# You should see (policycraft-env) at the start of your command line
```

### Runtime Issues

#### Port Already in Use
If you see "Address already in use", another instance is running:
```bash
# Find and stop the process using port 5001
lsof -ti:5001 | xargs kill -9  # macOS/Linux
# Or simply use a different port in app.py
```

#### Missing Dependencies
If you encounter import errors, ensure all models are downloaded:
```bash
# Re-run the model downloads
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt')"
```

#### Permission Errors (macOS/Linux)
```bash
# If you get permission errors, try:
sudo pip install -r requirements.txt
# Or better, use virtual environment (recommended)
```

---

## ❓ Frequently Asked Questions (FAQ)

### For New Users

**Q: I've never used Python before. Is this difficult?**
A: Not at all! Follow the step-by-step instructions above. The setup script (`python check_setup.py`) will help you verify everything is working.

**Q: What if I get errors during installation?**
A: Most common issues are covered in the "Common Issues & Solutions" section above. If you're still stuck, the setup checker will tell you exactly what's missing.

**Q: How long does the first installation take?**
A: Typically 5-15 minutes depending on your internet speed. The NLP models are the largest downloads.

**Q: Can I use this without a virtual environment?**
A: While possible, it's not recommended. Virtual environments prevent conflicts with other Python projects on your computer.

**Q: What if I accidentally close my terminal?**
A: Just navigate back to the PolicyCraft folder and reactivate the virtual environment:
```bash
cd PolicyCraft
source policycraft-env/bin/activate  # macOS/Linux
# or
policycraft-env\Scripts\activate     # Windows
```

---

## 🔧 Development Setup

For developers and contributors:

### Development Dependencies
```bash
# Install development tools
pip install -r requirements-dev.txt

# Run test suite
python -m pytest tests/

# Code formatting
black src/
flake8 src/
```

### Testing Guidelines
- Write tests for all new functionality
- Maintain >75% test coverage
- Include both unit and integration tests
- Test error handling and edge cases
- Follow existing test patterns in `tests/conftest.py`

## 📋 System Requirements

### Hardware
- **Processor**: 2+ GHz (4 cores recommended)
- **RAM**: 8GB minimum, 16GB recommended  
- **Storage**: 1GB free space (plus space for documents)
- **Display**: 1280x720 minimum resolution

### Software
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.9 or higher (3.12+ recommended)
- **Browser**: Latest version of Chrome, Firefox, Safari, or Edge

### Dependencies
All required Python packages are automatically installed via `requirements.txt`. The application will guide you through any additional setup steps.

For development, additional tools are available in `requirements-dev.txt`:
```bash
pip install -r requirements-dev.txt
```

## Project Information

- **Author**: Jacek Robert Kszczot
- **Programme**: MSc Data Science & AI
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
- **Interactive Visualisations**: Comprehensive charts and dashboards using Plotly

## Technical Architecture

```mermaid
graph LR
    A[Web UI] --> B[API Endpoints]
    B --> C[NLP Pipeline]
    C --> D[Policy Classifier]
    C --> E[Recommendation Engine]
    B --> F[Database]
    B --> G[PDF Generator]
    B --> H[Visualisation]
    
    style F fill:#d0e0ff,stroke:#333,stroke-width:2px
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
   git clone <https://github.com/jacekkszczot/PolicyCraft.git>
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

6. **Initialise Application**
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
3. **View Analysis**: Review extracted themes, classification, and visualisations
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
MSc Data Science & AI Student  
Leeds Trinity University  
Email: jacek.kszczot@icloud.com  
Project Repository: [[GitHub URL](https://github.com/jacekkszczot/PolicyCraft.git)]

---

*PolicyCraft - Empowering evidence-based AI policy development in higher education*