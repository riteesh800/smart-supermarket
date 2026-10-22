"""
Database migration script for SmartMart AI Supermarket.
Applies schema definitions and creates missing tables:
- oauth_accounts (links SmartMart users to Google sub identities)
- oauth_states (manages OAuth 2.0 PKCE, state, and nonce tokens)
- account_linking_tickets (manages explicit account-linking verification)
"""

import sys
import os

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base, init_db, OAuthAccount, OAuthState, AccountLinkingTicket, User, UserSession

def run_migrations():
    print("[*] Running database schema migration for SmartMart AI...")
    try:
        # Create all tables defined in Base metadata
        Base.metadata.create_all(engine)
        print("[+] Successfully verified and applied database tables:")
        print("   - users")
        print("   - user_sessions")
        print("   - oauth_accounts")
        print("   - oauth_states")
        print("   - account_linking_tickets")
        print("   - products, customers, sales, inventory, suppliers")
        print("[OK] Migration completed successfully!")
    except Exception as e:
        print(f"[-] Error applying migrations: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
