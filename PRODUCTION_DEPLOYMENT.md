# 🚀 Production Deployment Guide

## 🔐 Security Overview

This guide outlines the security measures and best practices implemented for production deployment of the Menu OCR application.

## 📋 Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Copy `.env.secrets` and fill in all required values
- [ ] Ensure `.env.secrets` is NOT committed to git
- [ ] Verify all API keys and secrets are properly configured
- [ ] Set `ENVIRONMENT=production` in production

### 2. Security Configuration
- [ ] Update allowed hosts in `main.py` for your domain
- [ ] Configure HTTPS certificates
- [ ] Set up proper CORS origins
- [ ] Enable rate limiting and security headers

### 3. Infrastructure Security
- [ ] Use Docker with security best practices
- [ ] Implement proper network segmentation
- [ ] Set up monitoring and logging
- [ ] Configure backup strategies

## 🔑 Secret Management

### Environment Variables Structure

```bash
# Copy and customize this file
cp .env.secrets .env.production
```

### Required Secrets

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJ...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key | `eyJ...` |
| `OPENROUTER_API_KEY` | OpenRouter API key | `sk-or-v1-...` |
| `JWT_SECRET_KEY` | JWT signing key (32+ chars) | Auto-generated |
| `SECRET_KEY` | Django-style secret (32+ chars) | Auto-generated |

## 🐳 Docker Security

### Production Docker Compose

```yaml
version: '3.8'
services:
  api:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    env_file:
      - .env.secrets
```

### Security Features Implemented

- ✅ **Non-root user**: Application runs as non-privileged user
- ✅ **Read-only filesystem**: Prevents file system modifications
- ✅ **No new privileges**: Container cannot gain additional privileges
- ✅ **Tmpfs**: Temporary files stored in memory only
- ✅ **Environment file**: Secrets loaded from external file

## 🔒 Security Headers

### Implemented Headers

```python
# Content Security Policy
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...

# Security Headers
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin

# HTTPS Only (Production)
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Rate Limiting

- **100 requests per minute** per IP address
- Automatic cleanup of old entries
- In-memory implementation (consider Redis for distributed rate limiting)

## 🔐 Authentication & Authorization

### API Key Authentication

```bash
# Enable with environment variable
API_KEY=your-production-api-key
```

### JWT Configuration

```python
JWT_SECRET_KEY: str  # 32+ characters required in production
JWT_ALGORITHM: HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: 30
```

## 📊 Monitoring & Logging

### Logging Configuration

```python
LOG_LEVEL: INFO  # Production default
SENTRY_DSN: https://...@sentry.io/...  # Error tracking
```

### Health Checks

```bash
# Health endpoint
GET /health

# Docker health checks
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## 🚀 Deployment Steps

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/menu-ocr
sudo chown $USER:$USER /opt/menu-ocr
cd /opt/menu-ocr
```

### 2. Application Deployment

```bash
# Clone repository (without secrets)
git clone https://github.com/your-repo/menu-ocr.git .
git checkout main

# Copy and configure secrets (NEVER commit this file)
cp .env.secrets .env.production
# Edit .env.production with your actual secrets

# Build and start services
docker-compose up -d --build

# Verify deployment
docker-compose ps
docker-compose logs -f api
```

### 3. SSL/TLS Configuration

```bash
# Using Let's Encrypt (Certbot)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Or using Docker with Traefik
# Configure Traefik for automatic SSL
```

### 4. Nginx Reverse Proxy (Recommended)

```nginx
# /etc/nginx/sites-available/menu-ocr
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/menu-ocr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔍 Security Auditing

### Regular Security Checks

```bash
# Check running containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Monitor logs for security events
docker-compose logs -f | grep -i "error\|security\|auth"

# Check environment variables are not exposed
docker exec menu-ocr-api env | grep -v "PATH\|HOME\|PWD"
```

### Vulnerability Scanning

```bash
# Scan Docker images
docker scan menu-ocr-api

# Check dependencies
pip audit
npm audit
```

## 🚨 Incident Response

### Security Breach Response

1. **Immediate Actions:**
   - Rotate all API keys and secrets
   - Check logs for unauthorized access
   - Notify affected users if necessary

2. **Investigation:**
   - Review access logs
   - Check for data exfiltration
   - Update security measures

3. **Recovery:**
   - Deploy security patches
   - Restore from clean backup
   - Monitor for similar attacks

## 📈 Performance Optimization

### Production Optimizations

```python
# Multi-worker configuration
workers = 4 if settings.is_production else 1

# Connection pooling
# Database connection pooling
# Redis connection pooling

# Caching strategies
# Static file caching
# API response caching
```

### Monitoring Metrics

- Response times
- Error rates
- Resource usage (CPU, memory, disk)
- Security events
- API usage patterns

## 🔄 Backup & Recovery

### Backup Strategy

```bash
# Database backups
# Redis data persistence
# Configuration backups
# Log archiving

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec menu-ocr-redis redis-cli --rdb /backup/redis_$DATE.rdb
# Upload to secure storage
```

## 📞 Support & Maintenance

### Regular Maintenance Tasks

- [ ] Weekly security updates
- [ ] Monthly dependency updates
- [ ] Quarterly security audits
- [ ] Annual penetration testing

### Contact Information

- **Security Issues:** security@yourcompany.com
- **Technical Support:** support@yourcompany.com
- **Emergency:** +1-XXX-XXX-XXXX

---

## ✅ Security Checklist

- [ ] All secrets stored in `.env.secrets`
- [ ] File excluded from git commits
- [ ] HTTPS enabled in production
- [ ] Security headers configured
- [ ] Rate limiting active
- [ ] CORS properly configured
- [ ] Input validation implemented
- [ ] SQL injection prevention
- [ ] XSS protection enabled
- [ ] CSRF protection active
- [ ] Secure session management
- [ ] Error messages don't leak information
- [ ] Logging configured (no sensitive data)
- [ ] Monitoring and alerting set up
- [ ] Regular backups configured
- [ ] Disaster recovery plan documented

**Remember: Security is an ongoing process, not a one-time setup!**