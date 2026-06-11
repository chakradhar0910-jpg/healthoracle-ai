import os

# Set mock API key before any modules are loaded in the test suite
os.environ["HEALTHORACLE_GEMINI_API_KEY"] = "mock-api-key"
