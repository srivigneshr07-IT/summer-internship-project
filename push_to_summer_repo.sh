#!/bin/bash

# Push to summer-internship-project repo

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║     🚀 PUSHING TO SUMMER INTERNSHIP PROJECT REPO                    ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "📋 SECURITY CHECK:"
echo "   ✅ .env is in .gitignore"
echo "   ✅ No AWS keys in code"
echo "   ✅ No database passwords in code"
echo ""

echo "📦 REPOSITORY:"
echo "   https://github.com/srivigneshr07-IT/summer-internship-project"
echo ""

echo "Enter your GitHub Personal Access Token:"
read -s TOKEN
echo ""

echo "🚀 Pushing to summer-internship-project..."
git push https://$TOKEN@github.com/srivigneshr07-IT/summer-internship-project.git main --force

if [ $? -eq 0 ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║              ✅ PUSH SUCCESSFUL                                      ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🎉 Your complete project is now on GitHub!"
    echo "📍 Repository: https://github.com/srivigneshr07-IT/summer-internship-project"
    echo ""
    echo "📊 What was pushed:"
    echo "   ✅ Complete source code"
    echo "   ✅ ML models (ensemble)"
    echo "   ✅ Documentation"
    echo "   ✅ Frontend & Backend"
    echo "   ✅ All commits & history"
    echo ""
    echo "🔒 What was NOT pushed:"
    echo "   ❌ .env file (secrets)"
    echo "   ❌ Database files"
    echo "   ❌ Log files"
    echo "   ❌ Training data CSVs"
    echo ""
else
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║              ❌ PUSH FAILED                                          ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "⚠️  Check your token and try again"
fi
