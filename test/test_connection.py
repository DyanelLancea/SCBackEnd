"""
Test Supabase Connection
Run this to verify your database connection is working
"""

from app.shared.supabase import get_supabase_client, test_connection

def main():
    print("=" * 50)
    print("Testing Supabase Connection...")
    print("=" * 50)
    print()
    
    # Test 1: Get client
    print("Test 1: Getting Supabase client...")
    try:
        client = get_supabase_client()
        print("✅ Client created successfully!")
        print(f"   Connected to: {client.supabase_url}")
        print()
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        print()
        return
    
    # Test 2: Test connection
    print("Test 2: Testing connection to database...")
    if test_connection():
        print("✅ Connection test passed!")
        print()
    else:
        print("❌ Connection test failed!")
        print()
        return
    
    # Test 3: Query events table
    print("Test 3: Querying events table...")
    try:
        response = client.table('events').select('*').limit(5).execute()
        print(f"✅ Successfully queried events table!")
        print(f"   Found {len(response.data)} events")
        
        if response.data:
            print("\n   Sample event:")
            event = response.data[0]
            print(f"   - Title: {event.get('title')}")
            print(f"   - Date: {event.get('date')}")
            print(f"   - Location: {event.get('location')}")
        print()
    except Exception as e:
        print(f"❌ Failed to query events: {e}")
        print()
        return
    
    # Test 4: Check event_registrations table
    print("Test 4: Checking event_registrations table...")
    try:
        response = client.table('event_registrations').select('*').limit(1).execute()
        print(f"✅ event_registrations table is accessible!")
        print()
    except Exception as e:
        print(f"❌ Failed to access event_registrations: {e}")
        print()
        return
    
    print("=" * 50)
    print("🎉 All tests passed! Your Supabase connection is working!")
    print("=" * 50)

if __name__ == "__main__":
    main()

