#!/usr/bin/env python3
"""
One-shot setup and run script.
Usage: python start.py [--seed] [--reset]
  --seed   Seed the database with synthetic demo data
  --reset  Drop and recreate the database before seeding
"""

import os
import sys

# Make sure we're in the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
load_dotenv()

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--seed",  action="store_true", help="Seed synthetic demo data")
parser.add_argument("--reset", action="store_true", help="Reset DB before seeding")
args = parser.parse_args()

if args.reset or args.seed:
    from database.init_db import reset_db, init_db
    if args.reset:
        reset_db()
    else:
        init_db()

    from database.seed_data import seed_all
    seed_all()

    # Seed new PRITHVI-X tables
    from database.seed_prithvi import seed_prithvi_data
    seed_prithvi_data()
else:
    # Always ensure new tables exist and are seeded
    from models.database import Base, engine
    Base.metadata.create_all(bind=engine)
    try:
        from database.seed_prithvi import seed_prithvi_data
        seed_prithvi_data()
    except Exception as e:
        print(f"[startup] PRITHVI-X seed skipped: {e}")

import uvicorn
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    log_level=os.getenv("LOG_LEVEL", "info").lower(),
)
