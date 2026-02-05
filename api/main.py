from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import traceback
from api.routers import assets, reports, rebalancing
from api.database import get_supabase_client

load_dotenv()

app = FastAPI(title="Personal Wealth Management API")

# 全局异常处理，返回详细错误信息以便调试
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = f"{str(exc)}\n{traceback.format_exc()}"
    print(f"Global Exception: {error_msg}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "trace": traceback.format_exc()},
    )

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置为前端的具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(assets.router)
app.include_router(reports.router)
app.include_router(rebalancing.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Personal Wealth Management API"}

@app.get("/health")
async def health_check():
    # 检查数据库连接
    db_status = "unknown"
    try:
        supabase = get_supabase_client()
        # 尝试做一个简单的查询
        supabase.table("assets").select("id").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        
    # 检查 DashScope Key
    has_dashscope = bool(os.environ.get("DASHSCOPE_API_KEY"))
    
    return {
        "status": "healthy", 
        "database": db_status,
        "env_vars": {
            "DASHSCOPE_API_KEY": "set" if has_dashscope else "missing",
            "SUPABASE_URL": "set" if os.environ.get("VITE_SUPABASE_URL") else "missing"
        }
    }
