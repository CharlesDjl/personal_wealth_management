import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件 (兼容从 api 目录或根目录运行的情况)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

url: str = os.environ.get("VITE_SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    # 尝试从 VITE_SUPABASE_ANON_KEY 获取 (作为后备)
    key = os.environ.get("VITE_SUPABASE_ANON_KEY")

if not url or not key:
    print("Warning: Supabase credentials not found in environment variables.")
    # 不抛出异常，以免导致整个应用崩溃，但数据库功能将不可用
    # raise ValueError("Supabase URL and Key must be set in environment variables")

try:
    supabase: Client = create_client(url, key)
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    supabase = None

def get_supabase_client() -> Client:
    if supabase is None:
        raise ValueError("Supabase client is not initialized")
    return supabase
