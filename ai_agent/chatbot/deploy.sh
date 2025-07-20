#!/bin/bash

# Marketing Insight Chatbot - GCP Cloud Run Deployment Script
# Developed by: Sumit Kamra, FoundryAI

set -e  # Exit on any error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID}"
SERVICE_NAME="marketing-insight-chatbot"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Marketing Insight Chatbot Deployment${NC}"
echo -e "${BLUE}Developed by: Sumit Kamra, FoundryAI${NC}"
echo "=============================================="

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  Not authenticated with gcloud. Please run:${NC}"
    echo "gcloud auth login"
    echo "gcloud auth application-default login"
    exit 1
fi

# Check if project ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}📝 Enter your GCP Project ID:${NC}"
    read -r PROJECT_ID
    export GCP_PROJECT_ID="$PROJECT_ID"
fi

echo -e "${GREEN}📋 Configuration:${NC}"
echo "Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo "Image: $IMAGE_NAME"
echo ""

# Set the project
echo -e "${BLUE}🔧 Setting GCP project...${NC}"
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo -e "${BLUE}🔌 Enabling required APIs...${NC}"
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  firestore.googleapis.com \
  containerregistry.googleapis.com

# Check if .env file exists for environment variables
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating template...${NC}"
    cat > .env << EOF
# OpenAI API Key (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Snowflake Configuration (Required for data queries)
SNOWFLAKE_USER=your_snowflake_username
SNOWFLAKE_PASSWORD=your_snowflake_password
SNOWFLAKE_ACCOUNT=your_snowflake_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema

# Pinecone Configuration (Required for document processing)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENV=your_pinecone_environment
PINECONE_INDEX_NAME=rag-index

# Cloud Configuration
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
USE_CLOUD_MEMORY=true
EOF
    echo -e "${RED}❌ Please edit .env file with your credentials and run again${NC}"
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
echo -e "${BLUE}🔍 Validating environment variables...${NC}"
REQUIRED_VARS=("OPENAI_API_KEY")
OPTIONAL_VARS=("SNOWFLAKE_USER" "PINECONE_API_KEY")

for var in "${REQUIRED_VARS[@]}"; do
    # Convert variable name to lowercase for comparison
    var_lower=$(echo "$var" | tr '[:upper:]' '[:lower:]')
    if [ -z "${!var}" ] || [ "${!var}" = "your_${var_lower}_here" ]; then
        echo -e "${RED}❌ Required environment variable $var not set${NC}"
        exit 1
    fi
done

# Check optional variables and warn
for var in "${OPTIONAL_VARS[@]}"; do
    if [ -z "${!var}" ] || [[ "${!var}" == *"your_"* ]]; then
        echo -e "${YELLOW}⚠️  Optional variable $var not set - some features may be disabled${NC}"
    fi
done

# Build the container image
echo -e "${BLUE}🏗️  Building container image...${NC}"

# Find the project root (where Dockerfile is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if we have Dockerfile in current directory or need to go to project root
if [ -f "Dockerfile" ]; then
    # Already in project root
    BUILD_DIR="."
elif [ -f "$PROJECT_ROOT/Dockerfile" ]; then
    # Need to build from project root
    BUILD_DIR="$PROJECT_ROOT"
else
    echo -e "${RED}❌ Dockerfile not found${NC}"
    exit 1
fi

echo "Building from: $BUILD_DIR"
gcloud builds submit --tag "$IMAGE_NAME" "$BUILD_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

# Create Firestore database for memory persistence
echo -e "${BLUE}🗄️  Setting up Firestore for memory persistence...${NC}"
gcloud firestore databases create --region="$REGION" 2>/dev/null || echo "Firestore database already exists"

# Deploy to Cloud Run
echo -e "${BLUE}☁️  Deploying to Cloud Run...${NC}"

# Build environment variables for Cloud Run
ENV_VARS="OPENAI_API_KEY=${OPENAI_API_KEY}"
ENV_VARS="${ENV_VARS},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},USE_CLOUD_MEMORY=true"

# Add Snowflake variables if available
if [ ! -z "$SNOWFLAKE_USER" ] && [[ "$SNOWFLAKE_USER" != *"your_"* ]]; then
    ENV_VARS="${ENV_VARS},SNOWFLAKE_USER=${SNOWFLAKE_USER}"
    ENV_VARS="${ENV_VARS},SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}"
    ENV_VARS="${ENV_VARS},SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}"
    ENV_VARS="${ENV_VARS},SNOWFLAKE_WAREHOUSE=${SNOWFLAKE_WAREHOUSE}"
    ENV_VARS="${ENV_VARS},SNOWFLAKE_DATABASE=${SNOWFLAKE_DATABASE}"
    ENV_VARS="${ENV_VARS},SNOWFLAKE_SCHEMA=${SNOWFLAKE_SCHEMA}"
fi

# Add Pinecone variables if available
if [ ! -z "$PINECONE_API_KEY" ] && [[ "$PINECONE_API_KEY" != *"your_"* ]]; then
    ENV_VARS="${ENV_VARS},PINECONE_API_KEY=${PINECONE_API_KEY}"
    ENV_VARS="${ENV_VARS},PINECONE_ENV=${PINECONE_ENV}"
    ENV_VARS="${ENV_VARS},PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}"
fi

# Deploy the service
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_NAME" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --port 8501 \
  --set-env-vars "$ENV_VARS"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo ""

    # Get the service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

    echo -e "${GREEN}🌐 Your chatbot is live at:${NC}"
    echo -e "${BLUE}$SERVICE_URL${NC}"
    echo ""
    echo -e "${GREEN}📊 Monitor your deployment:${NC}"
    echo "Cloud Run Console: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
    echo "Logs: gcloud logs tail --follow --service=$SERVICE_NAME"
    echo ""
    echo -e "${GREEN}🛠️  Useful commands:${NC}"
    echo "Update deployment: ./deploy.sh"
    echo "View logs: gcloud run logs tail $SERVICE_NAME --region=$REGION"
    echo "Delete service: gcloud run services delete $SERVICE_NAME --region=$REGION"

else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi
