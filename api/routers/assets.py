from fastapi import APIRouter, HTTPException, Depends, Header, UploadFile, File
from typing import List, Optional
from api.database import get_supabase_client
from api.models.schemas import AssetCreate, AssetUpdate, AssetResponse, AssetOverview, AssetType
from api.services.market_data import market_data_service
from api.services.asset_parser import asset_parser_service
from datetime import datetime

router = APIRouter(prefix="/api/assets", tags=["assets"])

# 依赖注入：获取当前用户 ID
async def get_current_user_id(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = authorization.replace("Bearer ", "")
    supabase = get_supabase_client()
    try:
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user.user.id
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/import-screenshot", response_model=List[AssetResponse])
async def import_screenshot(file: UploadFile = File(...), user_id: str = Depends(get_current_user_id)):
    """
    上传资产截图，使用 LLM 解析并导入/更新资产
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # 读取图片内容
    image_bytes = await file.read()
    
    # 调用 LLM 解析
    parsed_assets = await asset_parser_service.parse_asset_screenshot(image_bytes)
    
    # 打印日志调试
    print(f"DEBUG: Parsed assets from LLM: {parsed_assets}")
    
    if not parsed_assets:
        raise HTTPException(status_code=422, detail="Failed to parse assets from image")
    
    supabase = get_supabase_client()
    imported_assets = []
    
    for item in parsed_assets:
        symbol = item['symbol']
        name = item.get('name', '')
        asset_type = item.get('asset_type', 'fund')
        
        # 特别处理：如果是基金且没有代码但有名称（如支付宝截图）
        if not symbol and name and asset_type == 'fund':
            # 1. 尝试搜索代码
            print(f"Searching code for fund: {name}")
            searched_code = market_data_service.search_fund_code(name)
            if searched_code:
                symbol = searched_code
                item['symbol'] = symbol # 更新 item
                print(f"Found code for {name}: {symbol}")
                
                # 2. 获取最新净值
                current_price = market_data_service.get_current_price(symbol, 'fund')
                if current_price and current_price > 0:
                    item['current_price'] = current_price
                    
                    # 3. 反推份额和成本
                    # total_value (amount) = quantity * current_price  => quantity = amount / current_price
                    amount = item.get('amount', 0)
                    profit = item.get('profit', 0)
                    
                    if amount > 0:
                        qty = amount / current_price
                        item['quantity'] = qty
                        
                        # cost_value = amount - profit
                        # purchase_price = cost_value / qty
                        cost_value = amount - profit
                        if qty > 0:
                            purchase_price = cost_value / qty
                            item['purchase_price'] = purchase_price
                            print(f"Calculated for {name}: qty={qty:.4f}, cost={purchase_price:.4f}, nav={current_price}")

        # 补全名称逻辑：如果 OCR 未识别出名称，或名称无效，尝试从公开渠道获取
        current_ocr_name = item.get('name', '')
        if not current_ocr_name or current_ocr_name.isdigit() or current_ocr_name == symbol:
            fetched_name = market_data_service.get_asset_name(symbol, item['asset_type'])
            if fetched_name:
                item['name'] = fetched_name
                print(f"Fetched name for {symbol}: {fetched_name}")
        
        # 尝试查找现有资产 (按 Symbol 和 UserID)
        # 如果是现金，symbol 可能是 CASH，或者没有 symbol。
        # 简单起见，如果有 symbol 且不为空，则匹配 symbol。
        # 否则按 name 匹配。
        
        query = supabase.table("assets").select("*").eq("user_id", user_id)
        if symbol and symbol.upper() != "CASH":
            query = query.eq("symbol", symbol)
        else:
            query = query.eq("name", item['name'])
            
        existing = query.execute()
        
        if existing.data:
            # 更新逻辑：覆盖数量，重新计算总值
            # 注意：LLM 返回的 amount 可能是市值，quantity 可能是份额
            # 我们优先信赖 quantity。如果 quantity 为 0 但有 amount，且我们能获取价格，则反推 quantity。
            # 如果是 Cash，quantity = amount。
            
            asset_id = existing.data[0]['id']
            qty = item['quantity']
            
            # 优先使用 OCR 识别出的当前价格，如果为 0 则尝试从市场数据获取
            current_price = item.get('current_price', 0)
            if current_price <= 0:
                current_price = market_data_service.get_current_price(symbol, item['asset_type'])
                if current_price is None:
                    # 如果获取不到市场价格，尝试用截图里的 amount / quantity
                    if qty > 0 and item['amount'] > 0:
                        current_price = item['amount'] / qty
                    else:
                        current_price = existing.data[0]['current_price'] # 保持旧价格
            
            # 修正 Quantity 逻辑：如果 LLM 返回 0，或根据 A 股规则校验异常
            # 如果 qty 为 0 但有 amount 和 current_price，计算 qty
            if qty == 0 and item['amount'] > 0 and current_price > 0:
                 qty = item['amount'] / current_price
                 # 对于股票，尝试四舍五入到最近的整数（A股通常是100的倍数，但也可能有零股）
                 # 但 OCR 计算可能有微小误差 (e.g. 299.999 -> 300)
                 if item['asset_type'] == 'stock':
                     qty = round(qty)
            
            total_value = current_price * qty
            
            update_data = {
                "quantity": qty,
                "current_price": current_price,
                "total_value": total_value,
                "last_updated": datetime.now().isoformat()
            }
            # 如果 OCR 识别出了名称，尝试更新名称
            new_name = item.get('name')
            current_name = existing.data[0].get('name')
            # 只要新名称存在且不为空，且与旧名称不同，就更新
            if new_name and new_name != current_name:
                update_data['name'] = new_name
            
            # 如果 OCR 识别出了购买价格，则更新购买价格
            if item.get('purchase_price') and item['purchase_price'] > 0:
                update_data['purchase_price'] = item['purchase_price']
                
            resp = supabase.table("assets").update(update_data).eq("id", asset_id).execute()
            if resp.data:
                imported_assets.append(resp.data[0])
                
        else:
            # 创建新资产
            qty = item['quantity']
            
            # 优先使用 OCR 识别出的当前价格
            current_price = item.get('current_price', 0)
            if current_price <= 0:
                current_price = market_data_service.get_current_price(symbol, item['asset_type'])
                if current_price is None:
                     if qty > 0 and item['amount'] > 0:
                        current_price = item['amount'] / qty
                     else:
                        current_price = 0.0
                        
            # 同样处理 quantity = 0 的情况
            if qty == 0 and item['amount'] > 0 and current_price > 0:
                 qty = item['amount'] / current_price
                 if item['asset_type'] == 'stock':
                     qty = round(qty)
            
            total_value = current_price * qty
            
            # 优先使用 OCR 识别出的购买价格，如果没有则假设当前价格为成本价
            purchase_price = item.get('purchase_price', 0)
            if purchase_price <= 0:
                purchase_price = current_price
            
            new_asset = {
                "user_id": user_id,
                "symbol": symbol,
                "name": item.get('name', ''), # 确保 name 被写入
                "asset_type": item['asset_type'],
                "quantity": qty,
                "purchase_price": purchase_price,
                "purchase_date": datetime.now().isoformat(),
                "current_price": current_price,
                "total_value": total_value
            }
            resp = supabase.table("assets").insert(new_asset).execute()
            if resp.data:
                imported_assets.append(resp.data[0])
                
    return imported_assets

@router.get("/overview", response_model=AssetOverview)
async def get_asset_overview(user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    response = supabase.table("assets").select("*").eq("user_id", user_id).execute()
    assets = response.data
    
    if not assets:
        return AssetOverview(
            total_value=0, cash_value=0, stock_value=0, 
            fund_value=0, bond_value=0, gold_value=0
        )

    # 获取实时价格并计算总值
    # 注意：实际生产中应该有缓存机制，避免每次请求都去爬取价格
    # 这里简化处理，每次都更新
    
    overview = {
        "total_value": 0.0,
        "cash_value": 0.0,
        "stock_value": 0.0,
        "fund_value": 0.0,
        "bond_value": 0.0,
        "gold_value": 0.0
    }
    
    for asset in assets:
        # 更新价格
        current_price = market_data_service.get_current_price(asset['symbol'], asset['asset_type'])
        
        # 如果获取失败（None），则使用数据库中存储的旧价格
        if current_price is None:
            current_price = float(asset['current_price']) if asset['current_price'] else 0.0
            print(f"Warning: Using cached price for {asset['symbol']}: {current_price}")
        
        total_val = current_price * float(asset['quantity'])
        
        # 累加到概览
        overview["total_value"] += total_val
        key = f"{asset['asset_type']}_value"
        if key in overview:
            overview[key] += total_val
            
        # 异步更新数据库中的价格（可选，或者定期任务更新）
        # supabase.table("assets").update({
        #     "current_price": current_price,
        #     "total_value": total_val,
        #     "last_updated": datetime.now().isoformat()
        # }).eq("id", asset['id']).execute()

    return AssetOverview(**overview)

@router.get("/", response_model=List[AssetResponse])
async def get_assets(user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    response = supabase.table("assets").select("*").eq("user_id", user_id).execute()
    return response.data

@router.post("/", response_model=AssetResponse)
async def create_asset(asset: AssetCreate, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    
    # 获取初始价格
    fetched_price = market_data_service.get_current_price(asset.symbol, asset.asset_type)
    
    # 如果获取失败，默认为 0，或者尝试使用用户输入的买入价格作为参考
    current_price = fetched_price if fetched_price is not None else 0.0
    
    # 如果获取价格失败但用户提供了买入价格，可以用买入价格作为初始当前价格（可选策略）
    if current_price == 0.0 and asset.purchase_price and asset.purchase_price > 0:
        current_price = asset.purchase_price

    total_value = current_price * asset.quantity
    
    data = asset.model_dump()
    data["user_id"] = user_id
    data["current_price"] = current_price
    data["total_value"] = total_value
    data["purchase_date"] = data["purchase_date"].isoformat() if data["purchase_date"] else None
    
    response = supabase.table("assets").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create asset")
    
    return response.data[0]

@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: str, asset: AssetUpdate, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    
    # 检查权限
    existing = supabase.table("assets").select("*").eq("id", asset_id).eq("user_id", user_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    data = asset.model_dump(exclude_unset=True)
    if data.get("purchase_date"):
        data["purchase_date"] = data["purchase_date"].isoformat()
        
    # 如果 symbol 变更，需要重新获取价格和名称(如果未提供)
    if "symbol" in data:
        new_symbol = data["symbol"]
        asset_type = data.get("asset_type", existing.data[0]['asset_type']) # 暂时不支持改类型，或者从 existing 获取
        
        # 获取新价格
        new_price = market_data_service.get_current_price(new_symbol, asset_type)
        if new_price is not None:
            data["current_price"] = new_price
            # 如果没有提供 name，尝试自动获取
            if "name" not in data:
                new_name = market_data_service.get_asset_name(new_symbol, asset_type)
                if new_name:
                    data["name"] = new_name
    
    # 如果数量或价格变更，重新计算总值
    if "quantity" in data or "current_price" in data or "symbol" in data:
        qty = data.get("quantity", existing.data[0]['quantity'])
        price = data.get("current_price", existing.data[0]['current_price'])
        data["total_value"] = price * qty
        data["last_updated"] = datetime.now().isoformat()
        
    response = supabase.table("assets").update(data).eq("id", asset_id).execute()
    return response.data[0]

@router.post("/refresh-all", response_model=List[AssetResponse])
async def refresh_all_assets(user_id: str = Depends(get_current_user_id)):
    """
    刷新用户所有资产的价格
    """
    supabase = get_supabase_client()
    
    # 1. 获取所有资产
    response = supabase.table("assets").select("*").eq("user_id", user_id).execute()
    assets = response.data
    
    if not assets:
        return []

    updated_assets = []
    
    # 2. 逐个更新 (后续可优化为并发更新)
    for asset in assets:
        new_price = market_data_service.get_current_price(asset['symbol'], asset['asset_type'])
        
        if new_price is not None:
            total_value = new_price * float(asset['quantity'])
            update_data = {
                "current_price": new_price,
                "total_value": total_value,
                "last_updated": datetime.now().isoformat()
            }
            # 更新数据库
            upd_resp = supabase.table("assets").update(update_data).eq("id", asset['id']).execute()
            if upd_resp.data:
                updated_assets.append(upd_resp.data[0])
        else:
            # 如果更新失败，保留原数据
            updated_assets.append(asset)
            
    return updated_assets

@router.post("/{asset_id}/refresh", response_model=AssetResponse)
async def refresh_asset_price(asset_id: str, user_id: str = Depends(get_current_user_id)):
    """
    手动刷新单个资产的价格
    """
    supabase = get_supabase_client()
    
    # 1. 检查资产是否存在且属于当前用户
    existing = supabase.table("assets").select("*").eq("id", asset_id).eq("user_id", user_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset = existing.data[0]
    
    # 2. 强制尝试获取最新价格
    new_price = market_data_service.get_current_price(asset['symbol'], asset['asset_type'])
    
    if new_price is None:
        raise HTTPException(status_code=503, detail="Failed to fetch latest price from external source")
        
    # 3. 更新数据库
    total_value = new_price * float(asset['quantity'])
    update_data = {
        "current_price": new_price,
        "total_value": total_value,
        "last_updated": datetime.now().isoformat()
    }
    
    response = supabase.table("assets").update(update_data).eq("id", asset_id).execute()
    return response.data[0]

from pydantic import BaseModel

class BatchDeleteRequest(BaseModel):
    asset_ids: List[str]

@router.post("/batch-delete")
async def batch_delete_assets(request: BatchDeleteRequest, user_id: str = Depends(get_current_user_id)):
    """
    批量删除资产
    """
    supabase = get_supabase_client()
    
    # 只能删除属于该用户的资产
    response = supabase.table("assets").delete().in_("id", request.asset_ids).eq("user_id", user_id).execute()
    
    if not response.data:
        # 注意：如果 ID 不存在或不属于该用户，Supabase 可能返回空列表但不报错
        # 这里为了用户体验，即使没有删除任何数据也返回成功，或者检查删除数量
        pass
        
    return {"message": f"Successfully deleted {len(response.data)} assets"}

@router.delete("/{asset_id}")
async def delete_asset(asset_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    response = supabase.table("assets").delete().eq("id", asset_id).eq("user_id", user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"message": "Asset deleted successfully"}
