# 🚀 Deployment Guide

Complete guide for deploying the Pharmaceutical Product Monograph Generator in different environments.

---

## Table of Contents
1. [Local Development](#local-development)
2. [Streamlit Cloud (Free)](#streamlit-cloud)
3. [Docker (Any Cloud)](#docker)
4. [AWS Deployment](#aws)
5. [Azure Deployment](#azure)
6. [Self-Hosted Linux](#self-hosted-linux)
7. [Production Checklist](#production-checklist)

---

## Local Development

### Quick Start
```bash
git clone https://github.com/yourusername/monograph-generator.git
cd monograph-generator

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API key

# Create directories
mkdir -p data/monographs data/skill_files data/feedback

# Launch
streamlit run app.py
```

**Access:** http://localhost:8501

---

## Streamlit Cloud (Free Hosting)

### Easiest Deployment Option ⭐

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect to Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Click "New app"
   - Select your GitHub repo
   - Choose branch: `main`
   - Set main file: `app.py`

3. **Configure Secrets**
   - Go to Settings → Secrets
   - Add your API key:
     ```toml
     ANTHROPIC_API_KEY = "sk-ant-..."
     ```

4. **Deploy!**
   - Click "Deploy"
   - Your app is live at: `https://your-username-monograph-generator.streamlit.app`

### Cost: **FREE** (with some limitations)
- Free tier includes 1 app per account
- CPU: 2 cores, RAM: 512MB
- Sufficient for MVP (<10 concurrent users)

### Limitations
- 48-hour session timeout
- Auto-sleep after 7 days of inactivity
- Shared resources

---

## Docker (Production-Ready)

### Build & Run Locally

```bash
# Build image
docker build -t monograph-generator:latest .

# Run container
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v $(pwd)/data:/app/data \
  monograph-generator:latest
```

### Push to Docker Hub
```bash
# Tag image
docker tag monograph-generator:latest yourname/monograph-generator:latest

# Push to hub
docker login
docker push yourname/monograph-generator:latest
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  monograph-generator:
    image: monograph-generator:latest
    ports:
      - "8501:8501"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_PORT=8501
    volumes:
      - ./data:/app/data
      - ./data/monographs:/app/data/monographs
    restart: unless-stopped

  # Optional: nginx reverse proxy
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - monograph-generator
```

---

## AWS Deployment

### Option 1: AWS Elastic Beanstalk (Easiest)

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 monograph-generator
eb create monograph-env

# Deploy
git add .
git commit -m "Deployment"
eb deploy
```

### Option 2: ECS + Fargate (Scalable)

```bash
# Create ECR repository
aws ecr create-repository --repository-name monograph-generator

# Build and push image
docker build -t monograph-generator:latest .
docker tag monograph-generator:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/monograph-generator:latest

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/monograph-generator:latest
```

Then create ECS cluster and Fargate service through AWS Console.

### Cost Estimate
- **Elastic Beanstalk**: $5-30/month
- **Fargate**: $0.04638/hour per vCPU + $0.00512/hour per GB RAM
- **S3 (data storage)**: $0.023/GB/month

---

## Azure Deployment

### Azure Container Instances (Simple)

```bash
# Create resource group
az group create --name monograph-rg --location eastus

# Build and push to ACR
az acr create --resource-group monograph-rg \
  --name monographregistry --sku Basic

az acr build --registry monographregistry \
  --image monograph-generator:latest .

# Deploy container
az container create \
  --resource-group monograph-rg \
  --name monograph-container \
  --image monographregistry.azurecr.io/monograph-generator:latest \
  --environment-variables \
    ANTHROPIC_API_KEY=sk-ant-... \
  --ports 8501 \
  --ip-address public
```

### Azure App Service (Recommended)

```bash
# Create App Service plan
az appservice plan create \
  --name monograph-plan \
  --resource-group monograph-rg \
  --sku B1 --is-linux

# Create web app
az webapp create \
  --resource-group monograph-rg \
  --plan monograph-plan \
  --name monograph-app \
  --runtime "PYTHON|3.11"

# Configure and deploy
az webapp deployment source config-zip \
  --resource-group monograph-rg \
  --name monograph-app \
  --src deployment.zip
```

### Cost Estimate
- **Container Instances**: $0.0000138/second (~$10/month)
- **App Service B1**: ~$10/month

---

## Self-Hosted Linux

### Ubuntu/Debian Server

1. **Install Dependencies**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3.11 python3-pip python3-venv git nginx supervisor
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/monograph-generator.git
   cd monograph-generator
   ```

3. **Setup Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   mkdir -p data/monographs data/skill_files data/feedback
   ```

4. **Configure Supervisor** (for auto-restart)
   ```bash
   sudo nano /etc/supervisor/conf.d/monograph.conf
   ```
   
   Add:
   ```ini
   [program:monograph]
   directory=/home/ubuntu/monograph-generator
   command=/home/ubuntu/monograph-generator/venv/bin/python -m streamlit run app.py --server.port=8501 --server.headless=true
   user=ubuntu
   autostart=true
   autorestart=true
   
   environment=ANTHROPIC_API_KEY="sk-ant-...",STREAMLIT_SERVER_HEADLESS="true"
   ```

5. **Configure Nginx** (reverse proxy)
   ```bash
   sudo nano /etc/nginx/sites-available/monograph
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

6. **Enable SSL** (Let's Encrypt)
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

7. **Start Services**
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start monograph
   sudo systemctl restart nginx
   ```

### Cost Estimate
- **VPS (2 vCPU, 2GB RAM)**: $5-15/month
- **Domain**: $10-15/year
- **SSL**: Free (Let's Encrypt)

---

## Production Checklist

### Security
- [ ] API keys stored in environment variables (not in code)
- [ ] .env file in .gitignore
- [ ] HTTPS/SSL enabled
- [ ] Firewall configured (block unnecessary ports)
- [ ] Rate limiting enabled on API endpoints
- [ ] Input validation on all user inputs
- [ ] CORS configured appropriately

### Performance
- [ ] Caching enabled (30-day PubMed cache)
- [ ] Parallel API requests working (max_workers=4)
- [ ] PDF generation optimized
- [ ] Database indexes created (if using PostgreSQL)
- [ ] CDN configured (if applicable)

### Reliability
- [ ] Error handling implemented
- [ ] Retry logic with backoff
- [ ] Monitoring/alerting configured
- [ ] Backup strategy in place
- [ ] Auto-restart on failure (supervisor/systemd)
- [ ] Health checks configured

### Compliance
- [ ] Disclaimer displayed prominently
- [ ] Medical review requirement communicated
- [ ] Data privacy policy created
- [ ] HIPAA compliance (if handling patient data)
- [ ] Regulatory review completed
- [ ] Legal review completed

### Operations
- [ ] Logging configured
- [ ] Log aggregation (CloudWatch, Datadog, etc.)
- [ ] Uptime monitoring
- [ ] Performance metrics tracked
- [ ] Backup schedule established
- [ ] Disaster recovery plan documented

---

## Monitoring & Logging

### Application Metrics
```python
# Add to app.py for tracking
import time
from datetime import datetime

st.sidebar.write(f"🕐 Session started: {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.write(f"API endpoint: {os.getenv('ANTHROPIC_API_KEY', 'Not set')[:10]}...")

# Log generation events
import logging
logging.basicConfig(filename='monograph_generator.log', level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Cloud Logging
- **AWS**: CloudWatch Logs
- **Azure**: Application Insights
- **GCP**: Cloud Logging
- **Self-hosted**: ELK Stack, Graylog

### Alerts
- API rate limit exceeded
- Generation timeout
- Compliance score < 85%
- Server errors (5xx)
- Uptime monitoring

---

## Scaling Strategy

### Phase 1: MVP (Current)
- Single instance
- File-based storage
- Streamlit Cloud or VPS

### Phase 2: Growing Usage
- Replace file storage with PostgreSQL
- Add Redis caching layer
- Implement job queue (Celery)
- Multi-instance load balancing

### Phase 3: Enterprise
- Kubernetes cluster (EKS, AKS, GKE)
- Managed database (RDS, Cosmos DB)
- CDN for static content
- Advanced monitoring & analytics

---

## Cost Comparison by Deployment

| Option | Monthly | Setup | Scaling |
|--------|---------|-------|---------|
| Streamlit Cloud | Free | 5 min | Manual |
| Heroku | $7+ | 10 min | Easy |
| Lightsail | $3.50+ | 15 min | Manual |
| EB | $5+ | 20 min | Automatic |
| Self-hosted VPS | $5+ | 30 min | Manual |
| ECS Fargate | $30+ | 45 min | Automatic |

---

## Troubleshooting Deployment

**App won't start**
→ Check logs: `docker logs -f container_name` or `eb logs`
→ Verify API key is set
→ Ensure Python 3.9+

**High response times**
→ Check available memory
→ Review PubMed query optimization
→ Consider max_results reduction

**API key exposed**
→ Immediately rotate key at console.anthropic.com
→ Review git history for accidental commits
→ Use git-secrets to prevent future incidents

**500 errors**
→ Check application logs
→ Verify all dependencies installed
→ Test with smaller max_results (10-20)

---

**Need help?** Check the README.md or open an issue on GitHub.

Happy deploying! 🚀
