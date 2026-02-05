import React, { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { RebalancingResponse } from '../types';
import { ArrowRight, TrendingUp } from 'lucide-react';

export const Rebalancing = () => {
  const [data, setData] = useState<RebalancingResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get<RebalancingResponse>('/rebalancing/suggestions');
        setData(response.data);
      } catch (error) {
        console.error('Error fetching suggestions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>加载中...</div>;
  if (!data) return <div>暂无建议</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">调仓建议</h1>
        <div className="text-sm text-gray-500">
          基于永久投资组合策略 (25/25/25/25)
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">当前配置 vs 目标配置</h3>
          <div className="space-y-4">
            {Object.entries(data.current_allocation).map(([key, val]) => (
              <div key={key}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="capitalize">{key}</span>
                  <span className="text-gray-500">
                    {val.toFixed(1)}% / {data.target_allocation[key]}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full"
                    style={{ width: `${Math.min(val, 100)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">操作建议</h3>
          {data.suggestions.length === 0 ? (
            <div className="text-green-600 flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              当前配置平衡，无需调仓
            </div>
          ) : (
            <div className="space-y-4">
              {data.suggestions.map((suggestion, index) => (
                <div key={index} className="flex items-start p-3 bg-gray-50 rounded-md">
                  <div className={`flex-shrink-0 w-2 h-2 mt-2 rounded-full ${
                    suggestion.action === 'buy' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <div className="ml-4 flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {suggestion.action === 'buy' ? '买入' : '卖出'} {suggestion.asset_type}
                    </p>
                    <p className="text-sm text-gray-500">
                      金额: ¥{(suggestion.amount || 0).toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {suggestion.reason}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
