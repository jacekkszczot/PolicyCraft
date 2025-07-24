# Security Policy

## Data Scope
* **User Data**: Email address, hashed password (using Bcrypt with work factor 12)
* **Analysis Data**: Policy text and metadata (institution name, analysis date, timestamps)
* **No Storage** of sensitive personal data (PII of students/staff) is permitted

## Security Measures

### Data Protection
- All user passwords are hashed using Bcrypt with a work factor of 12
- Sensitive data in transit is encrypted using TLS 1.2+ (HTTPS)
- Database connections use SSL/TLS encryption
- Regular security audits are performed to identify vulnerabilities

### Authentication & Authorisation
- Session management with secure, HTTP-only cookies
- CSRF protection on all forms
- Rate limiting on authentication endpoints
- Password complexity requirements enforced
- Automatic session expiration after 30 minutes of inactivity

## Vulnerability Disclosure
If you discover a security vulnerability:
1. **Do not** create a public issue
2. Report it privately to **security@jaai.co.uk**
3. Include detailed steps to reproduce the issue
4. Allow 5 business days for initial response

## Update Policy
- External dependencies are reviewed and updated quarterly
- Critical security patches are applied within 72 hours of release
- Semantic Versioning (SemVer) is strictly followed
- End-of-life dependencies are removed or updated promptly

## Access Control
- Only authorised maintainers have SSH access to production servers
- Multi-factor authentication is required for all administrative access
- API keys and credentials are stored in environment variables
- Access logs are maintained and regularly reviewed

## Incident Response
1. **Identification**: Monitor systems for security events
2. **Containment**: Isolate affected systems if necessary
3. **Investigation**: Determine the scope and impact
4. **Eradication**: Remove the cause of the incident
5. **Recovery**: Restore affected systems
6. **Review**: Document lessons learned and update policies

## Compliance
- General Data Protection Regulation (GDPR) compliant
- Follows OWASP Top 10 security practices
- Regular penetration testing by certified professionals

## Licence
MIT – see [LICENCE](LICENSE) for full terms.

_Last Updated: 24 July 2025_
