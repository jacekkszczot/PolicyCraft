# Deployment Guide and Production Setup
## PolicyCraft: AI Policy Analysis Framework

**Version:** 1.0  
**Date:** August 2025  
**Environment:** Production-Ready Deployment

---

## Executive Summary

This deployment guide provides comprehensive instructions for deploying the PolicyCraft application in production environments. The guide covers various deployment scenarios, from single-server setups to scalable cloud deployments, ensuring the application can be deployed reliably across different infrastructure configurations.

**Note:** PolicyCraft is accessible online at [https://policycraft.jaai.co.uk](https://policycraft.jaai.co.uk)

---

## Prerequisites

### System Requirements
- **Operating System:** Linux (Ubuntu 20.04+ recommended), macOS 12+, Windows Server 2019+
- **Python:** 3.10+ (3.12 recommended)
- **Memory:** Minimum 4GB RAM, 8GB+ recommended
- **Storage:** Minimum 20GB available space
- **Network:** Stable internet connection for package installation

### Software Dependencies
- **Database:** MongoDB 6.0+ or MongoDB Atlas
- **Web Server:** Nginx 1.18+ or Apache 2.4+
- **Process Manager:** PM2, Supervisor, or systemd
- **Reverse Proxy:** Nginx (recommended)

---

## Single Server Deployment

### Step 1: Server Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3 python3-pip python3-venv nginx git curl

# Install MongoDB (if not using Atlas)
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

### Step 2: Application Setup
```bash
# Clone repository
git clone https://github.com/yourusername/PolicyCraft.git
cd PolicyCraft

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-production.txt

# Set environment variables
cp .env.example .env
# Edit .env with production values
```

### Step 3: Environment Configuration
```bash
# Production environment variables
export FLASK_ENV=production
export SECRET_KEY=your-secure-secret-key-here
export MONGODB_URI=mongodb://localhost:27017/policycraft
export DATABASE_URL=sqlite:///production.db
export LOG_LEVEL=INFO
```

### Step 4: Database Initialisation
```bash
# Initialise databases
python -c "
from src.database.models import db, User
from src.database.mongo_operations import init_mongodb
from werkzeug.security import generate_password_hash

# Initialise SQLite
db.create_all()

# Create admin user
admin = User(
    email='admin@policycraft.com',
    username='admin',
    is_admin=True
)
admin.password_hash = generate_password_hash('secure-password-here')
db.session.add(admin)
db.session.commit()

# Initialise MongoDB
init_mongodb()
print('Databases initialised successfully')
"
```

### Step 5: Web Server Configuration
```bash
# Nginx configuration
sudo tee /etc/nginx/sites-available/policycraft << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /path/to/PolicyCraft/src/web/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/policycraft /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Process Management
```bash
# Install PM2
npm install -g pm2

# Create PM2 configuration
tee ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'policycraft',
    script: 'app.py',
    cwd: '/path/to/PolicyCraft',
    interpreter: '/path/to/PolicyCraft/venv/bin/python',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      FLASK_ENV: 'production'
    }
  }]
}
EOF

# Start application
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-production.txt .
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 policycraft && chown -R policycraft:policycraft /app
USER policycraft

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["python", "app.py"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  policycraft:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - MONGODB_URI=mongodb://mongodb:27017/policycraft
      - DATABASE_URL=sqlite:///production.db
    depends_on:
      - mongodb
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=secure-password
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - policycraft
    restart: unless-stopped

volumes:
  mongodb_data:
```

### Deployment Commands
```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f policycraft

# Scale application
docker-compose up -d --scale policycraft=3

# Update application
docker-compose pull policycraft
docker-compose up -d policycraft
```

---

## Cloud Deployment

### AWS Deployment

#### EC2 Setup
```bash
# Launch EC2 instance (t3.medium recommended)
# Connect via SSH and follow single server deployment steps

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
```

#### RDS MongoDB Setup
```bash
# Create MongoDB cluster in DocumentDB
aws docdb create-db-cluster \
    --db-cluster-identifier policycraft-cluster \
    --engine docdb \
    --master-username admin \
    --master-user-password secure-password \
    --db-subnet-group-name default-vpc-subnet-group
```

#### Load Balancer Configuration
```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
    --name policycraft-alb \
    --subnets subnet-12345678 subnet-87654321 \
    --security-groups sg-12345678

# Create target group
aws elbv2 create-target-group \
    --name policycraft-tg \
    --protocol HTTP \
    --port 5000 \
    --vpc-id vpc-12345678

# Register targets
aws elbv2 register-targets \
    --target-group-arn arn:aws:elasticloadbalancing:region:account:targetgroup/policycraft-tg/12345678901234567890 \
    --targets Id=i-1234567890abcdef0
```

### Azure Deployment

#### Azure Container Instances
```bash
# Create resource group
az group create --name PolicyCraftRG --location "West Europe"

# Create container registry
az acr create --name policycraftacr --resource-group PolicyCraftRG --sku Basic

# Build and push image
az acr build --registry policycraftacr --image policycraft:latest .

# Deploy container
az container create \
    --resource-group PolicyCraftRG \
    --name policycraft-container \
    --image policycraftacr.azurecr.io/policycraft:latest \
    --dns-name-label policycraft-app \
    --ports 5000
```

---

## Security Configuration

### SSL/TLS Setup
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration
```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Check status
sudo ufw status verbose
```

### Environment Security
```bash
# Secure environment variables
sudo chmod 600 /path/to/PolicyCraft/.env
sudo chown www-data:www-data /path/to/PolicyCraft/.env

# Database security
sudo tee /etc/mongod.conf << EOF
security:
  authorization: enabled
net:
  bindIp: 127.0.0.1
EOF
sudo systemctl restart mongod
```

---

## Monitoring and Maintenance

### Health Checks
```bash
# Application health endpoint
curl -f http://localhost:5000/health

# Database connectivity
python -c "
from src.database.mongo_operations import test_connection
test_connection()
"

# System resources
htop
df -h
free -h
```

### Log Management
```bash
# Application logs
tail -f /path/to/PolicyCraft/logs/app.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u policycraft -f
```

### Backup Procedures
```bash
# Database backup
mongodump --db policycraft --out /backup/$(date +%Y%m%d)

# Application backup
tar -czf /backup/policycraft-$(date +%Y%m%d).tar.gz /path/to/PolicyCraft

# Automated backup script
sudo tee /usr/local/bin/backup-policycraft << EOF
#!/bin/bash
BACKUP_DIR="/backup"
DATE=\$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p \$BACKUP_DIR

# Backup MongoDB
mongodump --db policycraft --out \$BACKUP_DIR/mongodb_\$DATE

# Backup application
tar -czf \$BACKUP_DIR/policycraft_\$DATE.tar.gz /path/to/PolicyCraft

# Clean old backups (keep 7 days)
find \$BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \;
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: \$DATE"
EOF

sudo chmod +x /usr/local/bin/backup-policycraft
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-policycraft
```

---

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
pm2 logs policycraft

# Check environment
echo $FLASK_ENV
echo $MONGODB_URI

# Test database connection
python -c "
from src.database.mongo_operations import test_connection
test_connection()
"
```

#### Database Connection Issues
```bash
# Check MongoDB status
sudo systemctl status mongod

# Test MongoDB connection
mongo --host localhost --port 27017

# Check firewall
sudo ufw status
```

#### Performance Issues
```bash
# Monitor resources
htop
iotop
netstat -tulpn

# Check application metrics
curl http://localhost:5000/metrics
```

---

## Conclusion

This deployment guide provides comprehensive instructions for deploying PolicyCraft in various production environments. The application is designed to be deployment-ready and can be scaled according to specific requirements.

**Key Success Factors:**
- Proper environment configuration
- Secure database setup
- Monitoring and maintenance procedures
- Regular backup procedures

**Next Steps:**
1. Choose appropriate deployment method
2. Follow security best practices
3. Implement monitoring and alerting
4. Establish maintenance procedures
5. Test disaster recovery procedures

For additional support or custom deployment scenarios, refer to the application documentation or contact the development team.

---

## Appendices

### Appendix A: Environment Variables Reference
### Appendix B: Database Schema
### Appendix C: API Documentation
### Appendix D: Troubleshooting Guide

---

**Document Version:** 1.0  
**Last Updated:** August 2025  
**Next Review:** February 2025
