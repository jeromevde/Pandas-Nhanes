#!/usr/bin/env python3
"""
Local development server for Pandas-NHANES variable explorer.
This script automatically generates the site and serves it locally.
"""

import os
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import subprocess
import time
import socket

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def is_port_in_use(port):
    """Check if a port is already in use."""
    try:
        # Create a socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Try to bind to the port
            s.bind(('localhost', port))
            # If we get here, the port is free
            return False
    except OSError:
        # If we can't bind, the port is in use
        return True

def find_available_port(start_port=8000, max_attempts=20):
    """Find an available port starting from start_port."""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

def generate_site():
    """Generate the site content."""
    print("Generating site content...")
    try:
        # Get the path to the current directory (scripts)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Get the path to generate_site.py
        generate_site_path = os.path.join(script_dir, "generate_site.py")
        # Run the script
        subprocess.run([sys.executable, generate_site_path], check=True)
        print("Site generated successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating site: {e}")
        return False

def serve_site(port=8000):
    """Serve the site directory on the specified port."""
    # Get the path to the root directory
    root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    # Get the path to the site directory
    site_dir = os.path.join(root_dir, "site")
    
    # Change to the site directory
    os.chdir(site_dir)
    
    # Find an available port
    try:
        port = find_available_port(port)
        
        # Create and start the server
        server_address = ('', port)
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        
        url = f"http://localhost:{port}"
        print(f"Starting server at {url}")
        print("Press Ctrl+C to stop the server")
        
        # Open the browser automatically
        webbrowser.open(url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.server_close()
    except OSError as e:
        print(f"Error starting server: {e}")
        print("Try manually starting a server using 'python -m http.server' in the site directory")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    """Main function to generate and serve the site."""
    # Store the original working directory
    original_dir = os.getcwd()
    
    try:
        if generate_site():
            # Add a small delay to ensure files are written
            time.sleep(0.5)
            serve_site()
    finally:
        # Restore the original working directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main()
