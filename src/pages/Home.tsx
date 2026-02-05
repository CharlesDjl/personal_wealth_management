import React, { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { AssetOverview } from '../types';
import { ArrowUpRight, ArrowDownRight, DollarSign, TrendingUp } from 'lucide-react';

export const Home = () => {
  const [overview, setOverview] = useState<AssetOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const response = await apiClient.get<AssetOverview>('/assets/overview');
        setOverview(response.data);
      } catch (error) {
        console.error('Error fetching overview:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOverview();
  }, []);

  if (loading) return <div className="p-6 text-center">加载中...</div>;
  if (!overview) {
    // 即使加载失败，也显示空状态，而不是报错
    return (
        <div className="space-y-6">
          <h1 className="text-2xl font-semibold text-gray-900">资产总览</h1>
          <div className="p-6 text-center text-gray-500 bg-white shadow rounded-lg">
            暂无资产数据，请先前往“资产管理”页面添加资产。
          </div>
        </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">资产总览</h1>
      
      {/* 核心指标卡片 */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DollarSign className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">总资产</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    ¥{overview.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">现金储备</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    ¥{overview.cash_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 资产分布 */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">资产分布详情</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="border rounded p-4">
            <div className="text-sm text-gray-500">股票/基金</div>
            <div className="text-xl font-bold text-blue-600">
              ¥{((overview.stock_value || 0) + (overview.fund_value || 0)).toLocaleString()}
            </div>
          </div>
          <div className="border rounded p-4">
            <div className="text-sm text-gray-500">债券</div>
            <div className="text-xl font-bold text-green-600">
              ¥{overview.bond_value.toLocaleString()}
            </div>
          </div>
          <div className="border rounded p-4">
            <div className="text-sm text-gray-500">黄金</div>
            <div className="text-xl font-bold text-yellow-600">
              ¥{overview.gold_value.toLocaleString()}
            </div>
          </div>
          <div className="border rounded p-4">
            <div className="text-sm text-gray-500">现金</div>
            <div className="text-xl font-bold text-gray-600">
              ¥{overview.cash_value.toLocaleString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
