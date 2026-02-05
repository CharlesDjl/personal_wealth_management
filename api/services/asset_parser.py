import os
import json
import base64
from typing import List, Dict, Optional, Any
from http import HTTPStatus
import dashscope
from dashscope.api_entities.dashscope_response import Role

# 配置 API Key
dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY")

class AssetParserService:
    def __init__(self):
        self.api_key = os.environ.get("DASHSCOPE_API_KEY")
        
    async def parse_asset_screenshot(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        使用 Qwen-VL-Max 多模态模型解析资产截图
        """
        if not self.api_key:
            raise Exception("DASHSCOPE_API_KEY not set")

        # 将图片转换为 base64
        # Dashscope SDK 支持本地文件路径或 URL，也支持 base64 (data URI schema)
        # 格式: data:image/png;base64,.....
        img_b64 = base64.b64encode(image_bytes).decode('utf-8')
        img_data_uri = f"data:image/jpeg;base64,{img_b64}"

        # 构造 Prompt
        prompt = """
        请仔细分析这张图片，它可能是一张证券资产持仓表，或者支付宝/基金APP的持仓截图。
        请提取表格中的每一行资产信息，并以 JSON 数组格式返回。
        
        **重点注意**：
        1. 如果是证券持仓表，通常包含“证券代码”、“证券名称”、“市值”、“实际数量”、“成本价”、“市价”。
        2. 如果是支付宝/基金APP截图，通常包含“基金名称”（如“广发科创50联接A”）、“持有金额/金额”（如“16,002.00”）、“持有收益/收益”（如“+5,448.06”）。这种情况下通常没有代码。
        
        请提取以下字段：
        - symbol: 证券代码 (如 "600171")。如果截图中没有代码，请留空字符串 ""。
        - name: 证券/基金名称。**必须提取中文名称**。
        - asset_type: 根据代码或名称判断类型。stock (股票/ETF), fund (基金), bond (债券), gold (黄金), cash (现金/存款)。如果不确定，默认为 fund。
        - quantity: 图片中显示的“实际数量”或“持有数量”。如果图片未显示数量列，返回 0。
        - amount: 图片显示的市值/总金额/持有金额。
        - profit: 图片显示的持有收益/收益 (可选，仅用于支付宝截图场景)。
        - purchase_price: 图片显示的成本价。
        - current_price: 图片显示的市价/最新价。
        
        请严格只返回 JSON 数组字符串，不要包含 Markdown 格式标记（如 ```json ... ```），不要包含其他解释文字。
        示例格式：
        [
            {"symbol": "600519", "name": "贵州茅台", "asset_type": "stock", "quantity": 100, "amount": 180000.0, "purchase_price": 1700.0, "current_price": 1800.0},
            {"symbol": "", "name": "广发科创50联接A", "asset_type": "fund", "quantity": 0, "amount": 16002.00, "profit": 5448.06}
        ]
        """

        try:
            # 调用 DashScope MultiModal API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": img_data_uri},
                        {"text": prompt}
                    ]
                }
            ]

            response = dashscope.MultiModalConversation.call(
                model='qwen-vl-max',
                messages=messages
            )

            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0].message.content[0]['text']
                # 清理可能的 markdown 标记
                content = content.replace("```json", "").replace("```", "").strip()
                try:
                    assets = json.loads(content)
                    # 数据清洗与标准化
                    cleaned_assets = []
                    for asset in assets:
                        # 确保必要字段存在
                        if 'name' not in asset: continue
                        
                        # 标准化类型
                        atype = asset.get('asset_type', 'stock').lower()
                        if atype not in ['stock', 'fund', 'bond', 'gold', 'cash']:
                            atype = 'stock' # 默认
                        
                        # 处理数值
                        qty = float(asset.get('quantity', 0))
                        amt = float(asset.get('amount', 0))
                        
                        # 新增字段处理
                        purchase_price = float(asset.get('purchase_price', 0))
                        current_price = float(asset.get('current_price', 0))
                        profit = float(asset.get('profit', 0))
                        
                        # 如果是 Cash，quantity 通常等于 amount
                        if atype == 'cash' and qty == 0 and amt > 0:
                            qty = amt
                            
                        # 如果有金额但没数量，且是股票/基金，后续逻辑可能需要处理（或者前端让用户填）
                        # 这里原样返回，由 Router 处理入库逻辑
                        
                        cleaned_assets.append({
                            "symbol": asset.get('symbol', ''),
                            "name": asset.get('name', 'Unknown'),
                            "asset_type": atype,
                            "quantity": qty,
                            "amount": amt,
                            "purchase_price": purchase_price,
                            "current_price": current_price,
                            "profit": profit # 传递收益信息
                        })
                    return cleaned_assets
                except json.JSONDecodeError:
                    print(f"Failed to decode JSON from LLM: {content}")
                    return []
            else:
                print(f"DashScope API failed: {response.code} - {response.message}")
                return []

        except Exception as e:
            print(f"Asset parsing failed: {e}")
            return []

asset_parser_service = AssetParserService()