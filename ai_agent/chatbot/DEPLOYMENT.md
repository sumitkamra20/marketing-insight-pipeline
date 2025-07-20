# 🚀 GCP Cloud Run Deployment Guide

Deploy your Marketing Insight Chatbot to Google Cloud Platform with persistent memory using Firestore.

## 📋 Prerequisites

### 1. GCP Setup
- Google Cloud Platform account
- Billing enabled
- gcloud CLI installed and configured

### 2. Install gcloud CLI
```bash
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate
gcloud auth login
gcloud auth application-default login
```

### 3. Required APIs
The deployment script will automatically enable:
- Cloud Build API
- Cloud Run API
- Firestore API
- Container Registry API

## 🔑 Credentials Setup

### **IMPORTANT: Do NOT put GCP credentials in .env file!**

Instead, use one of these secure methods:

### Option A: Service Account (Recommended for Production)
```bash
# Create service account
gcloud iam service-accounts create chatbot-service \
    --display-name="Marketing Chatbot Service"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:chatbot-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:chatbot-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

# Download key file (keep this secure!)
gcloud iam service-accounts keys create chatbot-key.json \
    --iam-account=chatbot-service@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Option B: User Credentials (Recommended for Development)
```bash
# Already done if you ran gcloud auth login
gcloud auth application-default login
```

## 🔧 Environment Configuration

### 1. Create .env file
The deployment script will create a template if none exists:

```bash
# OpenAI API Key (Required)
OPENAI_API_KEY=sk-your-openai-key

# Snowflake Configuration (Required for data queries)
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema

# Pinecone Configuration (Required for document processing)
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENV=your_pinecone_environment
PINECONE_INDEX_NAME=rag-index

# Cloud Configuration (automatically set)
GOOGLE_CLOUD_PROJECT=your_project_id
USE_CLOUD_MEMORY=true
```

### 2. Set Project ID
```bash
export GCP_PROJECT_ID="your-gcp-project-id"
```

## 🚀 Deployment

### 1. Quick Deployment
```bash
cd ai_agent/chatbot
chmod +x deploy.sh
./deploy.sh
```

### 2. Manual Steps (if needed)
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/marketing-insight-chatbot .

# Deploy to Cloud Run
gcloud run deploy marketing-insight-chatbot \
  --image gcr.io/YOUR_PROJECT_ID/marketing-insight-chatbot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --port 8501 \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY,USE_CLOUD_MEMORY=true
```

## 🗄️ Memory Persistence

### How it Works
- **Local Development**: Uses SQLite database (`ai_agent/data/agent_memory.db`)
- **Cloud Deployment**: Uses Google Firestore for persistent conversation memory
- **Automatic Fallback**: If Firestore isn't available, falls back to in-memory storage

### Firestore Collections
- **chat_sessions**: Stores conversation history with metadata
- **Automatic Cleanup**: Old sessions (30+ days) are automatically cleaned up

### Memory Features
- **Session Isolation**: Each browser session gets a unique conversation thread
- **Cross-Container Persistence**: Memory survives container restarts
- **Conversation Context**: Maintains context for follow-up questions
- **Metadata Tracking**: Stores query types, timestamps, and session info

## 🔍 Monitoring & Debugging

### View Logs
```bash
# Real-time logs
gcloud logs tail --follow --service=marketing-insight-chatbot

# Historical logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=marketing-insight-chatbot"
```

### Firestore Data
```bash
# View chat sessions
gcloud firestore export gs://your-bucket/backup --collection-ids=chat_sessions
```

### Cloud Run Metrics
Visit: `https://console.cloud.google.com/run/detail/us-central1/marketing-insight-chatbot/metrics`

## 🛠️ Troubleshooting

### Common Issues

#### 1. Build Fails
```bash
# Check build logs
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")

# Common fix: ensure Dockerfile is in correct location
ls -la Dockerfile
```

#### 2. Memory Not Persisting
```bash
# Check Firestore is enabled
gcloud services list --enabled | grep firestore

# Verify environment variables
gcloud run services describe marketing-insight-chatbot --region=us-central1 --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"
```

#### 3. Permission Errors
```bash
# Add Cloud Run invoker role
gcloud run services add-iam-policy-binding marketing-insight-chatbot \
  --region=us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

#### 4. Service Account Issues
```bash
# Check current account
gcloud auth list

# Re-authenticate if needed
gcloud auth application-default login
```

## 💰 Cost Optimization

### Cloud Run Pricing
- **CPU**: Pay per 100ms of CPU time
- **Memory**: Pay per GB-second
- **Requests**: First 2 million requests/month free

### Resource Recommendations
- **Development**: 1 CPU, 1Gi memory
- **Production**: 2 CPU, 2Gi memory (current setting)

### Auto-scaling
- **Min instances**: 0 (scales to zero when not used)
- **Max instances**: 100 (default)
- **Concurrency**: 80 requests per instance

## 🔒 Security

### Environment Variables
- Never commit API keys to git
- Use Google Secret Manager for production secrets
- Rotate keys regularly

### Network Security
- Cloud Run provides HTTPS by default
- Consider VPC connector for private resources
- Use IAM for access control

## 🔄 Updates & Maintenance

### Update Deployment
```bash
# Make changes to code
# Run deployment script again
./deploy.sh
```

### Database Maintenance
```bash
# Cleanup old sessions (runs automatically)
# Manual cleanup via Firestore console if needed
```

### Monitoring
- Set up Cloud Monitoring alerts
- Monitor error rates and latency
- Review logs regularly

## 📞 Support

### Deployment Issues
1. Check the deployment script output for specific errors
2. Review Cloud Build logs
3. Verify environment variables are set correctly
4. Ensure all required APIs are enabled

### Runtime Issues
1. Check Cloud Run logs
2. Verify Firestore connectivity
3. Test API keys and external service connectivity
4. Monitor resource usage

---

**🎉 Your chatbot will be live at**: `https://marketing-insight-chatbot-[random].a.run.app`
