import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set the Python path to include the project directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Get the port from environment variables
port = int(os.getenv("PORT", 5001))

if __name__ == "__main__":
    print(f"Starting FastAPI server on port {port}...")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)