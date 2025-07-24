# PolicyCraft System Architecture

```mermaid
graph TD
    %% Main Components
    A[Web Browser] -->|HTTPS| B[Flask Web Server]
    B --> C[Authentication Service]
    B --> D[Document Processor]
    B --> E[Analysis Engine]
    B --> F[Validation Service]
    
    %% Analysis Engine Components
    E --> E1[NLP Pipeline]
    E1 --> E2[Policy Classifier]
    E1 --> E3[Recommendation Engine]
    E1 --> E4[Citation Validator]
    
    %% Data Storage
    B -->|MongoDB| G[Analyses Storage]
    C -->|SQLite| H[User Accounts]
    F --> I[Academic References]
    
    %% Output Generation
    B --> J[Report Generator]
    J --> K[PDF Export]
    J --> L[Visualisation Engine]
    
    %% External Services
    B -->|SMTP| M[Email Service]
    
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style E fill:#bfb,stroke:#333
    style F fill:#fbb,stroke:#333
```

## Core Components

1. **Web Interface**
   - Responsive HTML5/CSS3 frontend
   - Interactive visualisations using Plotly.js
   - Accessible UI components (WCAG 2.2 AA compliant)

2. **Backend Services**
   - **Authentication Service**: Manages user sessions and permissions
   - **Document Processor**: Handles file uploads and text extraction
   - **Analysis Engine**: Coordinates the policy analysis workflow
   - **Validation Service**: Verifies academic citations and references

3. **Analysis Components**
   - **NLP Pipeline**: Text preprocessing and feature extraction
   - **Policy Classifier**: Hybrid model for policy categorisation
   - **Recommendation Engine**: Suggests policy improvements
   - **Citation Validator**: Ensures academic rigour of sources

4. **Data Storage**
   - **MongoDB**: Stores analysis results and document metadata
   - **SQLite**: Manages user accounts and authentication
   - **Reference Database**: Curated collection of academic sources

5. **Output Generation**
   - **Report Generator**: Creates comprehensive policy analysis reports
   - **Visualisation Engine**: Generates interactive charts and metrics
   - **PDF Export**: Produces printable policy documents

## Data Flow

1. User uploads a policy document through the web interface
2. Document is processed and analysed by the NLP pipeline
3. Policy Classifier categorises the document
4. Recommendation Engine generates improvement suggestions
5. Validation Service checks academic citations
6. Results are stored and presented to the user
7. User can export findings in multiple formats

## Security Considerations

- All communications are encrypted using TLS 1.3
- Authentication uses secure, HTTP-only cookies
- Passwords are hashed using Bcrypt
- Regular security audits are performed

_Last Updated: 24 July 2025_
