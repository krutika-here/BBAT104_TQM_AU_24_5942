"""
WSGI Entrypoint for Production Deployment
Online Quiz System (BBAT104 - TQM Project, Roll No: 39)
Quality Goal: Q04 - Improve Security
"""
import os
from app import app
import database

# Initialize database schema and ensure default evaluation accounts exist
database.init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
