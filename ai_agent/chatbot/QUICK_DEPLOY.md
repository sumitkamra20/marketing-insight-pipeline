# ⚡ Quick Deploy to GCP

**5-minute deployment guide for your Marketing Insight Chatbot**

## 🚀 Prerequisites

1. **Install gcloud CLI**:
   ```bash
   # macOS: brew install google-cloud-sdk
   # Linux: curl https://sdk.cloud.google.com | bash
   ```

2. **Authenticate**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

## 🔧 Setup

1. **Set your GCP project**:
   ```bash
   export GCP_PROJECT_ID="your-gcp-project-id"
   ```

2. **Create .env file in project root**:
   ```bash
   # Required for OpenAI
   OPENAI_API_KEY=sk-your-openai-key

   # For data queries (optional)
   SNOWFLAKE_USER=your_username
   SNOWFLAKE_PASSWORD=your_password
   SNOWFLAKE_ACCOUNT=your_account
   SNOWFLAKE_WAREHOUSE=your_warehouse
   SNOWFLAKE_DATABASE=your_database
   SNOWFLAKE_SCHEMA=your_schema

   # For document processing (optional)
   PINECONE_API_KEY=your_pinecone_key
   PINECONE_ENV=your_pinecone_environment
   ```

## 🚀 Deploy

```bash
cd ai_agent/chatbot
chmod +x deploy.sh
./deploy.sh
```

That's it! 🎉

## 📱 Access Your Chatbot

After deployment, you'll get a URL like:
`https://marketing-insight-chatbot-xyz.a.run.app`

## 🔍 Monitor

```bash
# View logs
gcloud logs tail --follow --service=marketing-insight-chatbot

# View in console
# Visit Cloud Run console in GCP
```

## 🛠️ Update

To update your chatbot, just run the deploy script again:
```bash
./deploy.sh
```

---

**✅ Features Enabled:**
- ✅ Persistent memory (Firestore)
- ✅ Auto-scaling (0 to 100 instances)
- ✅ HTTPS by default
- ✅ Health checks
- ✅ Graceful error handling
