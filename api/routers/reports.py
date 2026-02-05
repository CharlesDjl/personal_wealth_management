from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from api.database import get_supabase_client
from api.routers.assets import get_current_user_id, get_asset_overview
from datetime import date

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/daily")
async def get_daily_report(user_id: str = Depends(get_current_user_id)):
    overview = await get_asset_overview(user_id)
    
    # 简单的健康评分逻辑
    health_score = 80
    risk_level = "moderate"
    
    # 如果现金比例过低，风险增加
    total_val = overview.total_value
    if total_val > 0:
        cash_ratio = overview.cash_value / total_val
        if cash_ratio < 0.1:
            health_score -= 10
            risk_level = "high"
        elif cash_ratio > 0.5:
            health_score -= 5
            risk_level = "low" # 过于保守
            
    return {
        "report_date": date.today().isoformat(),
        "total_assets": overview.total_value,
        "asset_allocation": {
            "cash": overview.cash_value,
            "stock": overview.stock_value + overview.fund_value,
            "bond": overview.bond_value,
            "gold": overview.gold_value
        },
        "health_score": health_score,
        "risk_assessment": risk_level,
        "recommendations": ["定期检查资产配置", "关注市场动态"]
    }
