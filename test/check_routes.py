"""
Check if routes are properly registered
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("Checking Route Registration")
print("="*70)

# Test 1: Check if module imports
print("\n1. Testing module imports...")
try:
    from app.orchestrator.routes import router
    print("   [OK] Router imported successfully")
except Exception as e:
    print(f"   [X] Import failed: {e}")
    sys.exit(1)

# Test 2: Check routes in router
print("\n2. Checking routes in router...")
try:
    routes = [r.path for r in router.routes if hasattr(r, 'path')]
    print(f"   Found {len(routes)} routes:")
    for route in routes:
        print(f"     - {route}")
    
    if "/process-singlish" in routes:
        print("   [OK] /process-singlish route found in router")
    else:
        print("   [X] /process-singlish route NOT found in router!")
        print("   Available routes:", routes)
except Exception as e:
    print(f"   [X] Error checking routes: {e}")

# Test 3: Check if app includes router
print("\n3. Testing app import and route registration...")
try:
    from app.main import app
    print("   [OK] App imported successfully")
    
    # Get all routes from app
    app_routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            app_routes.append(route.path)
        elif hasattr(route, 'path_regex'):
            # For mounted routers
            if hasattr(route, 'routes'):
                for sub_route in route.routes:
                    if hasattr(sub_route, 'path'):
                        full_path = route.path_regex.pattern.replace('^', '').replace('$', '') + sub_route.path
                        app_routes.append(full_path)
    
    print(f"   Found {len(app_routes)} routes in app")
    
    # Check for orchestrator routes
    orchestrator_routes = [r for r in app_routes if 'orchestrator' in r]
    print(f"   Orchestrator routes: {orchestrator_routes}")
    
    if any('process-singlish' in r for r in app_routes):
        print("   [OK] /process-singlish found in app routes")
    else:
        print("   [X] /process-singlish NOT found in app routes")
        print("   This means the route isn't being registered!")
        
except Exception as e:
    print(f"   [X] Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check for syntax errors
print("\n4. Checking for syntax errors...")
try:
    import ast
    with open('app/orchestrator/routes.py', 'r', encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)
    print("   [OK] No syntax errors in routes.py")
except SyntaxError as e:
    print(f"   [X] Syntax error: {e}")
    print(f"   Line {e.lineno}: {e.text}")

print("\n" + "="*70)
print("Summary")
print("="*70)
print("\nIf /process-singlish is not found:")
print("  1. Check Render logs for import errors")
print("  2. Verify the code was actually deployed")
print("  3. Check if there's an error during route registration")

