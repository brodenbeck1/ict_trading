import os
from dotenv import find_dotenv, load_dotenv

# find environment variables from a .env file
dotenv = find_dotenv()
print(f"Loading environment variables from {dotenv}")

# load the environment variables
load_dotenv(dotenv) 

#store environment variables in constants
API_KEY = os.getenv("DATABENTO_API_KEY")
DATA_BENTO_USER_ID = os.getenv("DATABENTO_USER_ID")
print(f"DATABENTO_API_KEY: {API_KEY}")
print(f"DATABENTO_USER_ID: {DATA_BENTO_USER_ID}")