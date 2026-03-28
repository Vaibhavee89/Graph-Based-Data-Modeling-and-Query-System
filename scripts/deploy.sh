#!/bin/bash

# Production Deployment Script
# Helps automate deployment to Railway (backend) and Vercel (frontend)

set -e

echo "🚀 Graph System - Production Deployment Helper"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    exit 1
fi

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

# Check git
if ! command_exists git; then
    echo -e "${RED}❌ Git not found. Please install Git first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Git installed"

# Check Railway CLI
if ! command_exists railway; then
    echo -e "${YELLOW}⚠️  Railway CLI not found.${NC}"
    echo "Install with: npm i -g @railway/cli"
    read -p "Install now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        npm i -g @railway/cli
    else
        echo -e "${YELLOW}⚠️  You'll need Railway CLI for backend deployment${NC}"
    fi
else
    echo -e "${GREEN}✓${NC} Railway CLI installed"
fi

# Check Vercel CLI
if ! command_exists vercel; then
    echo -e "${YELLOW}⚠️  Vercel CLI not found.${NC}"
    echo "Install with: npm i -g vercel"
    read -p "Install now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        npm i -g vercel
    else
        echo -e "${YELLOW}⚠️  You'll need Vercel CLI for frontend deployment${NC}"
    fi
else
    echo -e "${GREEN}✓${NC} Vercel CLI installed"
fi

echo ""
echo "=============================================="
echo ""

# Show deployment options
echo "What would you like to deploy?"
echo ""
echo "1) Backend to Railway"
echo "2) Frontend to Vercel"
echo "3) Both (Full Deployment)"
echo "4) Load data on Railway backend"
echo "5) Just build and push to GitHub"
echo "6) Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}🚂 Deploying Backend to Railway...${NC}"
        echo ""

        # Check if logged in
        if ! railway whoami >/dev/null 2>&1; then
            echo "Please login to Railway first:"
            railway login
        fi

        cd backend

        # Check if linked to project
        if [ ! -f ".railway" ]; then
            echo ""
            echo "Link to Railway project:"
            railway link
        fi

        echo ""
        echo "Deploying backend..."
        railway up

        echo ""
        echo -e "${GREEN}✅ Backend deployed!${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Set environment variables in Railway dashboard"
        echo "2. Add PostgreSQL database if not already added"
        echo "3. Run: ./scripts/deploy.sh and choose option 4 to load data"

        cd ..
        ;;

    2)
        echo ""
        echo -e "${BLUE}🔷 Deploying Frontend to Vercel...${NC}"
        echo ""

        cd frontend

        # Check if VITE_API_URL is set
        if [ -f ".env" ]; then
            source .env
            if [ -z "$VITE_API_URL" ]; then
                echo -e "${YELLOW}⚠️  VITE_API_URL not set in .env${NC}"
                read -p "Enter your Railway backend URL (https://your-app.railway.app): " backend_url
                echo "VITE_API_URL=$backend_url" > .env
            else
                echo "Using VITE_API_URL: $VITE_API_URL"
            fi
        else
            read -p "Enter your Railway backend URL (https://your-app.railway.app): " backend_url
            echo "VITE_API_URL=$backend_url" > .env
        fi

        echo ""
        echo "Deploying to Vercel..."
        vercel --prod

        echo ""
        echo -e "${GREEN}✅ Frontend deployed!${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Copy your Vercel URL from above"
        echo "2. Update CORS_ORIGINS in Railway backend environment variables"
        echo "3. Add: https://your-app.vercel.app"

        cd ..
        ;;

    3)
        echo ""
        echo -e "${BLUE}🚀 Full Deployment (Backend + Frontend)${NC}"
        echo ""

        # Deploy backend first
        echo "Step 1: Backend deployment"
        echo "------------------------"

        if ! railway whoami >/dev/null 2>&1; then
            echo "Please login to Railway first:"
            railway login
        fi

        cd backend

        if [ ! -f ".railway" ]; then
            echo "Link to Railway project:"
            railway link
        fi

        echo "Deploying backend..."
        railway up
        echo -e "${GREEN}✓${NC} Backend deployed"

        cd ..

        # Get Railway URL
        echo ""
        read -p "Enter your Railway backend URL (check Railway dashboard): " railway_url

        # Deploy frontend
        echo ""
        echo "Step 2: Frontend deployment"
        echo "-------------------------"

        cd frontend
        echo "VITE_API_URL=$railway_url" > .env

        echo "Deploying frontend..."
        vercel --prod

        echo ""
        echo -e "${GREEN}✅ Full deployment complete!${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Copy your Vercel URL from above"
        echo "2. Update CORS_ORIGINS in Railway: $railway_url"
        echo "3. Load data: ./scripts/deploy.sh → option 4"
        echo "4. Test your app at your Vercel URL"

        cd ..
        ;;

    4)
        echo ""
        echo -e "${BLUE}📊 Loading Data on Railway...${NC}"
        echo ""

        if ! railway whoami >/dev/null 2>&1; then
            echo "Please login to Railway first:"
            railway login
        fi

        cd backend

        if [ ! -f ".railway" ]; then
            echo "Link to Railway project:"
            railway link
        fi

        echo ""
        echo "What data would you like to load?"
        echo "1) Sample data (quick test)"
        echo "2) Load from CSV files"
        echo "3) Just rebuild graph (data already loaded)"
        echo ""
        read -p "Enter choice [1-3]: " data_choice

        case $data_choice in
            1)
                echo ""
                echo "Initializing database..."
                railway run python scripts/init_db.py

                echo "Loading sample data..."
                railway run python scripts/load_sample_data.py

                echo "Building graph..."
                railway run python scripts/build_graph.py

                echo ""
                echo -e "${GREEN}✅ Sample data loaded!${NC}"
                echo "140 nodes, 212 edges created"
                ;;
            2)
                read -p "Enter path to CSV files directory: " csv_path

                if [ ! -d "$csv_path" ]; then
                    echo -e "${RED}❌ Directory not found: $csv_path${NC}"
                    exit 1
                fi

                echo "Loading CSV data..."
                railway run python scripts/load_from_api.py csv "$csv_path"

                echo "Building graph..."
                railway run python scripts/build_graph.py

                echo ""
                echo -e "${GREEN}✅ CSV data loaded!${NC}"
                ;;
            3)
                echo "Building graph from existing data..."
                railway run python scripts/build_graph.py

                echo ""
                echo -e "${GREEN}✅ Graph rebuilt!${NC}"
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                exit 1
                ;;
        esac

        echo ""
        echo "Verifying deployment..."
        echo "Getting graph stats..."
        railway run python -c "from app.utils.graph_builder import GraphBuilder; from app.core.database import SessionLocal; g = GraphBuilder(SessionLocal()).build(); print(f'Nodes: {g.number_of_nodes()}, Edges: {g.number_of_edges()}')"

        cd ..
        ;;

    5)
        echo ""
        echo -e "${BLUE}📦 Building and Pushing to GitHub...${NC}"
        echo ""

        # Check git status
        if [ -n "$(git status --porcelain)" ]; then
            echo "Uncommitted changes found:"
            git status --short
            echo ""
            read -p "Commit all changes? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                read -p "Enter commit message: " commit_msg
                git add -A
                git commit -m "$commit_msg"
            fi
        else
            echo "No changes to commit"
        fi

        # Push to GitHub
        echo ""
        echo "Pushing to GitHub..."
        git push origin main

        echo ""
        echo -e "${GREEN}✅ Pushed to GitHub!${NC}"
        echo ""
        echo "Railway and Vercel will auto-deploy if configured."
        ;;

    6)
        echo "Exiting..."
        exit 0
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "=============================================="
echo -e "${GREEN}✅ Done!${NC}"
echo ""
echo "📚 For detailed deployment guide, see:"
echo "   docs/PRODUCTION_DEPLOYMENT.md"
echo ""
