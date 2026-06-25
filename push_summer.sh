#!/bin/bash
echo "Enter your GitHub Personal Access Token:"
read -s TOKEN
echo ""
echo "Pushing to summer-internship-project..."
git push https://$TOKEN@github.com/srivigneshr07-IT/summer-internship-project.git main --force 2>&1 | grep -v "Username\|Password"
