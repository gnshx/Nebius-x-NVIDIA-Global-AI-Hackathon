#!/usr/bin/env python3
"""
RepoMedic Demo Seed Script

Seeds a demo run into the database and triggers the agent.
Requires: running postgres, redis, and API server.

Usage: python scripts/seed_demo.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid

# Add API to path
API_DIR = os.path.join(os.path.dirname(__file__), "..", "apps", "api")
sys.path.insert(0, API_DIR)

DEMO_REPO_FULL_NAME = os.getenv("DEMO_REPO", "")
DEMO_ISSUE_NUMBER = int(os.getenv("DEMO_ISSUE_NUMBER", "1"))
API_URL = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")


async def seed_demo():
    import httpx

    print("\n🩺 RepoMedic Demo Seeder")
    print("=" * 40)

    if not DEMO_REPO_FULL_NAME:
        print(
            "\n⚠️  DEMO_REPO not set. Using local demo directory.\n"
            "   Set DEMO_REPO=owner/repo in .env to use a real GitHub repo.\n"
        )
        print("📋 Demo repository: demo/")
        print("   Bug: parse_user_id() uses split(' ') instead of split('-')")
        print("   Expected fix: change split(' ') to split('-')")
        print("\n🔧 To run the full demo:")
        print("   1. Push the demo/ directory to a GitHub repo")
        print("   2. Install the RepoMedic GitHub App on that repo")
        print("   3. Create an issue with the title from demo/ISSUE.md")
        print("   4. Comment '/repomedic fix' on the issue")
        print("\n   OR use the API directly:")
        print(f"   POST {API_URL}/api/runs")
        print('   {"repository_full_name": "your/repo", "issue_number": 1}')
        return

    print(f"\n→ Registering repository: {DEMO_REPO_FULL_NAME}")
    async with httpx.AsyncClient(base_url=API_URL) as client:
        # Register repo
        resp = await client.post("/api/repositories", json={"full_name": DEMO_REPO_FULL_NAME})
        if resp.status_code not in (200, 201):
            print(f"❌ Failed to register repo: {resp.text}")
            return
        print("✅ Repository registered")

        # Trigger run
        print(f"\n→ Triggering agent run for issue #{DEMO_ISSUE_NUMBER}...")
        resp = await client.post(
            "/api/runs",
            json={
                "repository_full_name": DEMO_REPO_FULL_NAME,
                "issue_number": DEMO_ISSUE_NUMBER,
                "max_iterations": 3,
            },
        )
        if resp.status_code not in (200, 201):
            print(f"❌ Failed to trigger run: {resp.text}")
            return

        run = resp.json()
        run_id = run["id"]
        print(f"✅ Run started: {run_id}")
        print(f"\n🌐 Dashboard: {API_URL.replace('8000', '3000')}/runs/{run_id}")
        print(f"📊 API:       {API_URL}/api/runs/{run_id}")


if __name__ == "__main__":
    asyncio.run(seed_demo())
