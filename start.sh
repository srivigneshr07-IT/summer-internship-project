#!/bin/bash

# 🚀 Quick Start Script - AI-Powered Car Valuation System

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║     🚗 AI-Powered Car Valuation System - Quick Start                ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Install Dependencies
echo "📦 Step 1: Installing dependencies..."
pip install -r backend/requirements.txt
echo "✅ Dependencies installed"
echo ""

# Step 2: Setup Environment
echo "🔧 Step 2: Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env with your credentials"
    echo "   (AWS keys and PostgreSQL details)"
else
    echo "✅ .env file exists"
fi
echo ""

# Step 3: Run Tests
echo "🧪 Step 3: Running comprehensive tests..."
python test_comprehensive.py
echo ""

# Step 4: Start Backend
echo "🚀 Step 4: Starting backend server..."
echo "   Backend will run on: http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
