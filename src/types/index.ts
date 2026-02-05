export type AssetType = 'cash' | 'stock' | 'fund' | 'bond' | 'gold';

export interface Asset {
  id: string;
  user_id: string;
  asset_type: AssetType;
  symbol: string;
  name?: string; // 新增
  quantity: number;
  current_price: number;
  total_value: number;
  purchase_price?: number;
  purchase_date?: string;
  last_updated: string;
  created_at: string;
}

export interface AssetOverview {
  total_value: number;
  cash_value: number;
  stock_value: number;
  fund_value: number;
  bond_value: number;
  gold_value: number;
  daily_change: number;
}

export interface DailyReport {
  report_date: string;
  total_assets: number;
  asset_allocation: {
    cash: number;
    stock: number;
    bond: number;
    gold: number;
  };
  health_score: number;
  risk_assessment: string;
  recommendations: string[];
}

export interface RebalancingSuggestion {
  action: 'buy' | 'sell';
  asset_type: string;
  amount: number;
  reason: string;
}

export interface RebalancingResponse {
  current_allocation: { [key: string]: number };
  target_allocation: { [key: string]: number };
  suggestions: RebalancingSuggestion[];
  expected_return: number;
}
