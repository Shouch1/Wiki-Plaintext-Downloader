import os
import sys
import webbrowser
from threading import Timer

# Ensure the 'api' directory is in the path so we can import index.py
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

try:
    from index import app
except ImportError:
    print("Error: Could not find 'api/index.py'. Make sure you are running this from the project root.")
    sys.exit(1)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    print("--- W.P.D. Local Runner ---")
    print("Starting local development server...")
    
    # Wait 1.5 seconds then open the browser automatically
    Timer(1.5, open_browser).start()
    
    # Run the Flask app
    app.run(debug=True, port=5000)
