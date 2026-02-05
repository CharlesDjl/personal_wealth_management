import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件 (兼容从 api 目录或根目录运行的情况)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 后端优先使用 SUPABASE_URL 和 SUPABASE_KEY
url: str = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")

if not url or not key:
    print("Warning: Supabase credentials not found in environment variables.")
    print("Please create a .env file with SUPABASE_URL and SUPABASE_KEY")
    supabase = None
else:
    try:
        supabase: Client = create_client(url, key)
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        supabase = None

def get_supabase_client() -> Client:
    if supabase is None:
        raise ValueError("Supabase client is not initialized")
    return supabase
