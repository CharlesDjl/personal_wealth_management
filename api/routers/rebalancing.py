from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from api.database import get_supabase_client
from api.models.schemas import RebalancingResponse, RebalancingSuggestion
from api.routers.assets import get_current_user_id, get_asset_overview

router = APIRouter(prefix="/api/rebalancing", tags=["rebalancing"])

@router.get("/suggestions", response_model=RebalancingResponse)
async def get_rebalancing_suggestions(user_id: str = Depends(get_current_user_id)):
    # 1. 获取当前资产概览
    overview = await get_asset_overview(user_id)
    total_value = overview.total_value
    
    if total_value == 0:
        return RebalancingResponse(
            current_allocation={"cash": 0, "stock": 0, "bond": 0, "gold": 0, "fund": 0},
            target_allocation={"cash": 25, "stock": 25, "bond": 25, "gold": 25},
            suggestions=[],
            expected_return=0
        )
        
    # 2. 获取用户目标配置 (目前硬编码为永久投资组合，后续可从数据库读取)
    # 永久投资组合: 25% 现金, 25% 股票, 25% 债券, 25% 黄金
    # 注意：我们将 fund 归类到 stock 或者单独处理，这里为了简化，假设 fund 也是权益类，并入 stock 计算，或者根据需求分开
    # 这里简单地将 fund 并入 stock 计算
    
    current_allocation = {
        "cash": (overview.cash_value / total_value) * 100,
        "stock": ((overview.stock_value + overview.fund_value) / total_value) * 100,
        "bond": (overview.bond_value / total_value) * 100,
        "gold": (overview.gold_value / total_value) * 100
    }
    
    target_allocation = {
        "cash": 25.0,
        "stock": 25.0,
        "bond": 25.0,
        "gold": 25.0
    }
    
    suggestions = []
    
    # 3. 计算偏差并生成建议
    # 阈值：偏差超过 5% 才建议调仓
    threshold = 5.0
    
    for asset_type, target_pct in target_allocation.items():
        current_pct = current_allocation.get(asset_type, 0)
        diff = target_pct - current_pct
        
        if abs(diff) > threshold:
            action = "buy" if diff > 0 else "sell"
            # 计算需要买入/卖出的金额
            amount = abs(diff / 100) * total_value
            
            suggestions.append(RebalancingSuggestion(
                action=action,
                asset_type=asset_type,
                amount=round(amount, 2),
                reason=f"{asset_type} allocation is {current_pct:.1f}%, target is {target_pct}%. Deviation: {diff:.1f}%"
            ))
            
    return RebalancingResponse(
        current_allocation=current_allocation,
        target_allocation=target_allocation,
        suggestions=suggestions,
        expected_return=0.06 # 假设年化收益率
    )
