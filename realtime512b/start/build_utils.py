"""Build utilities for UI components."""

import os
import subprocess
import sys
from pathlib import Path


class BuildError(Exception):
    """Exception raised when UI build fails."""
    pass


def verify_node_and_npm():
    """
    Verify that Node.js >= 18 and npm are installed.
    
    Raises:
        BuildError: If Node.js or npm are not found, or if Node.js version < 18
    """
    # Check Node.js
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            raise BuildError(
                "Node.js is required but not found.\n"
                "Please install Node.js >= 18 from https://nodejs.org"
            )
        
        # Parse version (format: v18.x.x or v20.x.x)
        version_str = result.stdout.strip()
        if not version_str.startswith('v'):
            raise BuildError(f"Could not parse Node.js version: {version_str}")
        
        major_version = int(version_str[1:].split('.')[0])
        if major_version < 18:
            raise BuildError(
                f"Node.js version {version_str} found, but version >= 18 is required.\n"
                f"Please upgrade Node.js from https://nodejs.org"
            )
        
        print(f"✓ Node.js {version_str} found")
        
    except FileNotFoundError:
        raise BuildError(
            "Node.js is required but not found.\n"
            "Please install Node.js >= 18 from https://nodejs.org"
        )
    
    # Check npm
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            raise BuildError(
                "npm is required but not found.\n"
                "Please install npm (usually included with Node.js)"
            )
        
        npm_version = result.stdout.strip()
        print(f"✓ npm v{npm_version} found")
        
    except FileNotFoundError:
        raise BuildError(
            "npm is required but not found.\n"
            "Please install npm (usually included with Node.js)"
        )


def run_npm_install(ui_dir: Path):
    """
    Run npm install in the UI directory.
    
    Args:
        ui_dir: Path to the figpack-realtime512b-ui directory
        
    Returns:
        bool: True if successful, False if failed (with warning)
    """
    print("Installing npm dependencies...")
    
    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=ui_dir,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            # Check if it's a network error
            error_output = result.stderr.lower()
            if "getaddrinfo" in error_output or "network" in error_output or "enotfound" in error_output:
                print("⚠ Warning: npm install failed (possible network issue)")
                print("  Continuing with existing dependencies...")
                return False
            else:
                # Other error - still show warning but continue
                print("⚠ Warning: npm install failed")
                print(f"  Error: {result.stderr}")
                print("  Continuing with existing dependencies...")
                return False
        
        print("✓ npm dependencies installed")
        return True
        
    except Exception as e:
        print(f"⚠ Warning: npm install failed: {e}")
        print("  Continuing with existing dependencies...")
        return False


def build_ui_components():
    """
    Build the UI components by running npm build in figpack-realtime512b-ui.
    
    Raises:
        BuildError: If the build fails or output file is not created
    """
    # Get the project root directory (parent of realtime512b/)
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    ui_dir = project_root / "figpack-realtime512b-ui"
    output_file = project_root / "realtime512b" / "figpack_realtime512b.js"

    # Verify UI directory exists
    if not ui_dir.exists():
        raise BuildError(
            f"UI directory not found: {ui_dir}\n"
            "The figpack-realtime512b-ui directory is required for building UI components."
        )
    
    print("Building UI components...")
    print(f"UI directory: {ui_dir}")
    
    # Verify Node.js and npm
    verify_node_and_npm()
    
    # Run npm install
    run_npm_install(ui_dir)
    
    # Run npm build
    print("Running npm build...")
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=ui_dir,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Show output for debugging
        if result.stdout:
            print(result.stdout)
        
        if result.returncode != 0:
            error_msg = "npm build failed:\n"
            if result.stderr:
                error_msg += result.stderr
            else:
                error_msg += "Unknown error"
            
            # Add helpful suggestions
            error_msg += "\n\nTroubleshooting steps:"
            error_msg += f"\n1. Check that package.json exists in {ui_dir}"
            error_msg += f"\n2. Try manually running: cd {ui_dir} && npm install && npm run build"
            error_msg += "\n3. Check for any missing dependencies or build errors above"
            
            raise BuildError(error_msg)
        
        # Verify output file was created
        if not output_file.exists():
            raise BuildError(
                f"Build completed but output file not found: {output_file}\n"
                "Please check the build configuration in vite.config.ts"
            )
        
        print(f"✓ UI components built successfully")
        print(f"  Output: {output_file}")
        
    except FileNotFoundError:
        raise BuildError(
            "npm command not found. Please ensure npm is installed and in your PATH."
        )