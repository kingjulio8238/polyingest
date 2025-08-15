#!/usr/bin/env python3
"""
Structure verification script for PolyIngest Phase 1.

Verifies that all directories and Python packages are correctly initialized.
"""

import os
import sys
from pathlib import Path

def main():
    """Verify project structure matches Phase 1 requirements."""
    print("🚀 PolyIngest Phase 1 Structure Verification")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Add project root to Python path for imports
    sys.path.insert(0, str(project_root))
    
    # Define expected structure
    expected_dirs = [
        "app",
        "app/api",
        "app/api/models", 
        "app/data",
        "app/agents",
        "app/intelligence",
        "app/alpha",
        "app/storage",
        "app/monitoring",
        "scripts",
        "tests",
        "tests/unit",
        "tests/integration", 
        "tests/load",
        "migrations"
    ]
    
    expected_init_files = [
        "app/__init__.py",
        "app/api/__init__.py",
        "app/api/models/__init__.py",
        "app/data/__init__.py",
        "app/agents/__init__.py",
        "app/intelligence/__init__.py",
        "app/alpha/__init__.py",
        "app/storage/__init__.py",
        "app/monitoring/__init__.py"
    ]
    
    # Check directories
    print("📁 Checking directories...")
    missing_dirs = []
    for dir_path in expected_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} - MISSING")
            missing_dirs.append(dir_path)
    
    print()
    
    # Check __init__.py files
    print("🐍 Checking Python package initialization...")
    missing_init_files = []
    for init_file in expected_init_files:
        if os.path.exists(init_file) and os.path.isfile(init_file):
            print(f"  ✅ {init_file}")
        else:
            print(f"  ❌ {init_file} - MISSING")
            missing_init_files.append(init_file)
    
    print()
    
    # Test imports
    print("🔍 Testing Python imports...")
    try:
        import app
        print("  ✅ import app")
        
        import app.api
        print("  ✅ import app.api")
        
        import app.api.models
        print("  ✅ import app.api.models")
        
        import app.data
        print("  ✅ import app.data")
        
        import app.agents
        print("  ✅ import app.agents")
        
        import app.intelligence
        print("  ✅ import app.intelligence")
        
        import app.alpha
        print("  ✅ import app.alpha")
        
        import app.storage
        print("  ✅ import app.storage")
        
        import app.monitoring
        print("  ✅ import app.monitoring")
        
        print("  ✅ All imports successful")
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    
    print()
    
    # Summary
    if missing_dirs or missing_init_files:
        print("❌ VERIFICATION FAILED")
        if missing_dirs:
            print(f"   Missing directories: {', '.join(missing_dirs)}")
        if missing_init_files:
            print(f"   Missing __init__.py files: {', '.join(missing_init_files)}")
        return False
    else:
        print("🎉 VERIFICATION SUCCESSFUL")
        print("   All directories and Python packages are correctly initialized!")
        print("   Phase 1 project structure is ready for development.")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)