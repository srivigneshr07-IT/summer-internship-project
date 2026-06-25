#!/bin/bash
echo "Enter your GitHub Personal Access Token:"
read -s TOKEN
echo ""
echo "Pushing to GitHub..."
git push https://$TOKEN@github.com/srivigneshr07-IT/internship-project-final.git main --force
