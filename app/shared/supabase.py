"""
Supabase Connection and Configuration
Shared database connection for all modules
"""

import os
from typing import Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance
    """
    global supabase
    
    if supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Supabase credentials not found. "
                "Please set SUPABASE_URL and SUPABASE_KEY in your .env file"
            )
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase")
    
    return supabase


def test_connection() -> bool:
    """
    Test the Supabase connection
    """
    try:
        client = get_supabase_client()
        # Try a simple query to test connection
        response = client.table('events').select("count", count='exact').limit(0).execute()
        print("✅ Supabase connection test successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection test failed: {e}")
        return False


# Helper function to handle Supabase responses
def handle_supabase_response(response) -> Dict[str, Any]:
    """
    Process Supabase response and handle errors
    """
    if hasattr(response, 'data') and response.data is not None:
        return {
            "success": True,
            "data": response.data,
            "count": len(response.data) if isinstance(response.data, list) else 1
        }
    else:
        return {
            "success": False,
            "data": None,
            "error": "No data returned"
        }

