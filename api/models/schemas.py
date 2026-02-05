from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum

class AssetType(str, Enum):
    cash = "cash"
    stock = "stock"
    fund = "fund"
    bond = "bond"
    gold = "gold"

class AssetBase(BaseModel):
    asset_type: AssetType
    symbol: str
    name: Optional[str] = None # 新增 name 字段
    quantity: float
    purchase_price: Optional[float] = None
    purchase_date: Optional[date] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    symbol: Optional[str] = None # 允许更新 symbol
    name: Optional[str] = None # 允许更新 name
    quantity: Optional[float] = None
    purchase_price: Optional[float] = None
    purchase_date: Optional[date] = None

class AssetResponse(AssetBase):
    id: str
    user_id: str
    current_price: float
    total_value: float
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class AssetOverview(BaseModel):
    total_value: float
    cash_value: float
    stock_value: float
    fund_value: float
    bond_value: float
    gold_value: float
    daily_change: Optional[float] = 0.0

class PortfolioTarget(BaseModel):
    target_cash_pct: float = 25.0
    target_stock_pct: float = 25.0
    target_bond_pct: float = 25.0
    target_gold_pct: float = 25.0
    strategy_name: str = "permanent_portfolio"

class RebalancingSuggestion(BaseModel):
    action: str  # buy or sell
    asset_type: str
    amount: float
    reason: str

class RebalancingResponse(BaseModel):
    current_allocation: Dict[str, float]
    target_allocation: Dict[str, float]
    suggestions: List[RebalancingSuggestion]
    expected_return: Optional[float] = None
