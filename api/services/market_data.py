import tushare as ts
import pandas as pd
import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class MarketDataService:
    def __init__(self):
        self.tushare_token = os.environ.get("TUSHARE_TOKEN")
        self.pro = None
        if self.tushare_token:
            try:
                ts.set_token(self.tushare_token)
                self.pro = ts.pro_api()
                print("Tushare initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Tushare: {e}")

    def _get_gold_price(self) -> Optional[float]:
        """
        爬取伦敦金价 (XAU/USD)
        备用源: 金投网或其他开放数据源
        """
        try:
            # 尝试从极简汇率或类似的免费开放 API 获取
            # 这里使用一个公开的汇率 API 示例 (exchangerate-api 或类似)
            # 或者直接爬取金投网页面 (解析 HTML 较脆弱，优先 API)
            
            # 方案 A: 使用 Metal Price API 的免费层 (如果有 Key)
            # 方案 B: 简单的 HTML 爬取 (以金投网为例，仅作演示)
            # 方案 C: 模拟 Yahoo Finance 的替代品，例如 Sina Finance 接口
            
            # 使用新浪财经接口获取国际金价 (hf_XAU)
            url = "http://hq.sinajs.cn/list=hf_XAU"
            headers = {"Referer": "http://finance.sina.com.cn/"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                # 响应格式: var hq_str_hf_XAU="1834.50,1834.60,1834.50,1834.60,1834.50,08:59:59";
                # 价格通常在第 0 位
                content = resp.text
                if '"' in content:
                    data = content.split('"')[1]
                    price = float(data.split(',')[0])
                    if price > 0:
                        return price
        except Exception as e:
            print(f"Gold price fetch failed: {e}")
        return None

    def _get_fund_nav_from_web(self, fund_code: str) -> Optional[float]:
        """
        爬取场外基金净值 (天天基金网)
        无需鉴权，适合获取实时性要求不高的日更净值
        """
        try:
            # 天天基金网接口
            # http://fundgz.1234567.com.cn/js/001186.js
            # 返回 jsonp: jsonpgz({"fundcode":"001186","name":"富国文体健康股票A","jzrq":"2023-05-12","dwjz":"2.3450",...});
            
            # 使用时间戳防止缓存
            import time
            timestamp = int(time.time() * 1000)
            url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js?rt={timestamp}"
            resp = requests.get(url, timeout=5)
            
            if resp.status_code == 200:
                content = resp.text
                # 提取 jsonpgz(...) 中的内容
                start = content.find('(')
                end = content.rfind(')')
                if start != -1 and end != -1:
                    import json
                    json_str = content[start+1:end]
                    data = json.loads(json_str)
                    # dwjz: 单位净值 (昨日收盘), gsz: 估算值 (今日实时)
                    # 只有在交易时间(9:30-15:00)且 gsz 存在时，才优先用 gsz
                    # 否则使用 dwjz (更准确)
                    # 但用户反馈 gsz (1.0668) 准确，dwjz (1.05) 偏离，说明 dwjz 滞后。
                    # 策略：如果有 gsz，优先用 gsz，因为它代表最新估值
                    if 'gsz' in data and data['gsz']:
                         return float(data['gsz'])
                    if 'dwjz' in data and data['dwjz']:
                        return float(data['dwjz'])
                         
        except Exception as e:
            print(f"Fund web crawl failed for {fund_code}: {e}")
            
            # 备用方案：新浪财经基金接口
            try:
                 # http://hq.sinajs.cn/list=f_013810
                 url_sina = f"http://hq.sinajs.cn/list=f_{fund_code}"
                 resp_sina = requests.get(url_sina, timeout=5)
                 if resp_sina.status_code == 200:
                     # var hq_str_f_013810="景顺长城中证500指数增强A,1.2345,..."
                     # 第 1 位是净值 (索引 1)
                     content = resp_sina.text
                     if '"' in content:
                         data = content.split('"')[1].split(',')
                         if len(data) > 1:
                             return float(data[1])
            except Exception as e2:
                 print(f"Sina fund fallback failed for {fund_code}: {e2}")

        return None

    def _get_tushare_price(self, symbol: str) -> Optional[float]:
        """
        使用 Tushare 获取 A 股价格 (股票和 ETF)
        """
        if not self.pro:
            return None
            
        # 转换代码格式: 
        # Yahoo (600519.SS) -> Tushare (600519.SH)
        # Yahoo (000001.SZ) -> Tushare (000001.SZ)
        # 场外基金 (013810.OF) -> Tushare (013810.OF)
        ts_code = symbol
        if symbol.endswith('.SS'):
            ts_code = symbol.replace('.SS', '.SH')
        
        try:
            # 0. 如果是场外基金 (.OF)，使用 fund_nav 接口
            if ts_code.endswith('.OF'):
                try:
                    # 场外基金净值
                    df_nav = self.pro.fund_nav(ts_code=ts_code.split('.')[0], limit=1) # 尝试不带后缀或者带后缀
                    if df_nav.empty:
                         df_nav = self.pro.fund_nav(ts_code=ts_code, limit=1)
                    
                    if not df_nav.empty:
                        # 场外基金通常看 'unit_nav' (单位净值)
                        return float(df_nav.iloc[0]['unit_nav'])
                except Exception as e:
                    print(f"Tushare fund_nav failed for {ts_code}: {e}")

            # 1. 尝试作为普通股票获取
            df = self.pro.daily(ts_code=ts_code, limit=1)
            if not df.empty:
                return float(df.iloc[0]['close'])
            
            # 2. 如果是基金 (ETF/LOF)，尝试 fund_daily 接口
            # Tushare 的基金接口通常不需要后缀，或者后缀规则不同，这里尝试直接带后缀查询
            try:
                df_fund = self.pro.fund_daily(ts_code=ts_code, limit=1)
                if not df_fund.empty:
                    return float(df_fund.iloc[0]['close'])
            except:
                pass

            # 3. 备选：尝试获取实时行情 (旧版接口)
            try:
                # get_realtime_quotes 需要纯数字代码，不需要后缀
                code_only = ts_code.split('.')[0]
                df_rt = ts.get_realtime_quotes(code_only)
                if df_rt is not None and not df_rt.empty:
                    price = float(df_rt.iloc[0]['price'])
                    if price > 0:
                        return price
            except:
                pass
            
            # 4. 针对 ETF 的特别处理 (如果上述都失败)
            # 159852 是深交所 ETF，Tushare 代码应该是 159852.SZ
            # 有时候 fund_daily 需要更早的数据，或者代码后缀不匹配
            if '159852' in ts_code:
                try:
                    # 尝试直接用新浪接口兜底 ETF
                    sina_code = f"sz{ts_code.split('.')[0]}"
                    url = f"http://hq.sinajs.cn/list={sina_code}"
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        content = resp.text
                        if '"' in content:
                            data = content.split('"')[1]
                            # 新浪 A 股/ETF 格式: name, open, pre_close, current, high, low, ...
                            # current 是第 3 位 (索引 3)
                            price = float(data.split(',')[3])
                            if price > 0:
                                return price
                except Exception as e:
                    print(f"Sina fallback for ETF {ts_code} failed: {e}")

        except Exception as e:
            print(f"Tushare failed for {ts_code}: {e}")
        
        return None

    def get_current_price(self, symbol: str, asset_type: str) -> Optional[float]:
        """
        获取资产当前价格
        :param symbol: 资产代码
        :param asset_type: 资产类型 (stock, fund, bond, gold, cash)
        :return: 当前价格, 失败返回 None
        """
        if asset_type == 'cash':
            return 1.0  # 现金单位价值为 1 (假设基础货币为人民币)
        
        # 黄金特别处理
        if asset_type == 'gold' or symbol.upper() == 'GOLD' or symbol == 'GC=F':
            # 优先尝试获取国内人民币金价 (g)
            try:
                # 上海黄金交易所 Au99.99
                # 新浪接口: hf_XAU 是国际金价(美元/盎司), g_Au99_99 是国内金价(人民币/克)
                # 使用新浪财经行情接口获取国内金价
                url = "http://hq.sinajs.cn/list=g_Au99_99"
                headers = {"Referer": "http://finance.sina.com.cn/"}
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    content = resp.text
                    if '"' in content:
                        # 格式: var hq_str_g_Au99_99="黄金9999,580.00,580.00,582.50,578.00,581.30,...";
                        # 最新价在第 5 位 (索引 5) - 注意不同接口字段位置可能不同，通常是 最新价
                        # 另一种格式: 名字,开盘,昨收,最新,最高,最低...
                        data = content.split('"')[1].split(',')
                        if len(data) > 5:
                            price = float(data[3]) # 通常第 4 个是当前价格 (index 3)
                            if price > 0:
                                return price
            except Exception as e:
                print(f"CNY Gold price fetch failed: {e}")

            # 如果国内金价获取失败，尝试获取国际金价并折算
            gold_price = self._get_gold_price()
            if gold_price:
                # 国际金价是 美元/盎司
                # 1 盎司 = 31.1035 克
                # 汇率假设 7.0
                price_cny_g = (gold_price / 31.1035) * 7.0
                return price_cny_g
        
        # 处理特殊后缀，如 A 股代码
        ticker_symbol = symbol
        is_cn_stock = False
        
        if asset_type == 'stock':
            if symbol.isdigit():
                if symbol.startswith('60') or symbol.startswith('68'):
                    ticker_symbol = f"{symbol}.SS"
                    is_cn_stock = True
                elif symbol.startswith('00') or symbol.startswith('30'):
                    ticker_symbol = f"{symbol}.SZ"
                    is_cn_stock = True
        
        elif asset_type == 'fund':
            # 区分场内基金(ETF/LOF) 和 场外基金
            # 场内基金: 15开头(深交所), 51开头(上交所)
            if symbol.startswith('15') or symbol.startswith('51'):
                ticker_symbol = f"{symbol}.SZ" if symbol.startswith('15') else f"{symbol}.SS"
                is_cn_stock = True
            else:
                # 场外基金 (00xxxx, 01xxxx 等)
                # 不作为股票处理，直接走 fund_nav 爬虫
                is_cn_stock = False
        
        # 优先尝试 Tushare (仅针对 A 股和场内 ETF)
        if is_cn_stock and self.pro:
            price = self._get_tushare_price(ticker_symbol)
            if price is not None:
                return price
        
        # 尝试场外基金爬虫 (针对所有非场内的基金，包括 005875 等)
        if asset_type == 'fund' and not is_cn_stock:
             # 确保是数字代码 (甚至支持非6位，只要接口支持)
             fund_price = self._get_fund_nav_from_web(symbol)
             if fund_price:
                 return fund_price
        
        try:
            # 简单的 Mock 机制：如果网络不通或获取失败，返回模拟数据
            # 仅用于开发演示，生产环境应移除
            if asset_type == 'stock' and not symbol:
                return None
            
            return None
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None

    def search_fund_code(self, fund_name: str) -> Optional[str]:
        """
        根据基金名称搜索基金代码
        优先尝试天天基金网接口
        """
        if not fund_name:
            return None
            
        try:
            # 策略1: 直接搜索全名
            # 天天基金搜索接口
            # http://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?m=1&key=广发科创50
            
            search_keys = [fund_name]
            
            # 策略2: 去掉最后两个字符 (通常是 A/B/C/联接A 等)
            if len(fund_name) > 4:
                search_keys.append(fund_name[:-2])
                
            # 策略3: 只取前 6 个字符 (针对超长名字)
            if len(fund_name) > 6:
                search_keys.append(fund_name[:6])
                
            for key in search_keys:
                if not key.strip(): continue
                
                url = f"http://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?m=1&key={key}"
                resp = requests.get(url, timeout=3)
                
                if resp.status_code == 200:
                    data = resp.json()
                    # 响应格式: {"Datas": [{"CODE": "012345", "NAME": "...", ...}]}
                    if "Datas" in data and len(data["Datas"]) > 0:
                        # 尝试过滤掉高端理财 (CATEGORY=750)，只保留基金 (CATEGORY=700)
                        # 同时优先选择 6 位数字代码
                        for item in data["Datas"]:
                            code = item["CODE"]
                            if str(item.get("CATEGORY")) == "700" and len(code) == 6 and code.isdigit():
                                return code
            
            # 如果所有 key 都没找到完美匹配，返回 None
            return None
                        
        except Exception as e:
            print(f"Fund search failed for {fund_name}: {e}")
            
        return None

    def get_asset_name(self, symbol: str, asset_type: str) -> Optional[str]:
        """
        根据代码获取资产名称
        """
        if not symbol:
            return None
            
        try:
            # 1. A 股 / ETF
            if asset_type == 'stock' or (asset_type == 'fund' and len(symbol) == 6 and (symbol.startswith('15') or symbol.startswith('51'))):
                # 构造新浪代码
                sina_code = symbol
                if symbol.startswith('6'):
                    sina_code = f"sh{symbol}"
                elif symbol.startswith('0') or symbol.startswith('3') or symbol.startswith('1'):
                    sina_code = f"sz{symbol}"
                elif symbol.startswith('5'):
                    sina_code = f"sh{symbol}"
                
                url = f"http://hq.sinajs.cn/list={sina_code}"
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    # var hq_str_sh600519="贵州茅台,..."
                    content = resp.text
                    if '"' in content:
                        data = content.split('"')[1]
                        name = data.split(',')[0]
                        if name:
                            return name
            
            # 2. 场外基金
            if asset_type == 'fund':
                # 尝试新浪基金接口
                url = f"http://hq.sinajs.cn/list=f_{symbol}"
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    # var hq_str_f_013810="景顺长城中证500指数增强A,..."
                    content = resp.text
                    if '"' in content:
                        data = content.split('"')[1]
                        name = data.split(',')[0]
                        if name:
                            return name
                            
        except Exception as e:
            print(f"Failed to fetch name for {symbol}: {e}")
            
        return None

    def get_asset_values(self, assets: list) -> Dict[str, float]:
        """
        批量获取资产价值
        """
        results = {}
        for asset in assets:
            price = self.get_current_price(asset['symbol'], asset['asset_type'])
            # 如果获取失败，使用 0 或其他默认值
            final_price = price if price is not None else 0.0
            results[asset['id']] = {
                'current_price': final_price,
                'total_value': final_price * float(asset['quantity'])
            }
        return results

market_data_service = MarketDataService()
