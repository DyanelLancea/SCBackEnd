import os
import warnings

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Supabase URL from environment
url = os.getenv("SUPABASE_URL")

# Service Role Key from environment
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    if not url:
        warnings.warn(
            "SUPABASE_URL not found in environment. "
            "Set SUPABASE_URL in your .env file to enable Supabase.",
            UserWarning,
        )
    if not key:
        warnings.warn(
            "SUPABASE_SERVICE_ROLE_KEY not found in environment. "
            "Supabase features will be unavailable. "
            "Set SUPABASE_SERVICE_ROLE_KEY in your .env file to enable Supabase.",
            UserWarning,
        )
    supabase = None
else:
    supabase = create_client(url, key)

