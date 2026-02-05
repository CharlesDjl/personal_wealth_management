import React, { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { DailyReport } from '../types';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

export const Reports = () => {
  const [report, setReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await apiClient.get<DailyReport>('/reports/daily');
        setReport(response.data);
      } catch (error) {
        console.error('Error fetching report:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, []);

  if (loading) return <div>加载中...</div>;
  if (!report) return <div>暂无报告数据</div>;

  const data = {
    labels: ['现金', '股票/基金', '债券', '黄金'],
    datasets: [
      {
        data: [
          report.asset_allocation.cash,
          report.asset_allocation.stock,
          report.asset_allocation.bond,
          report.asset_allocation.gold,
        ],
        backgroundColor: [
          'rgba(75, 192, 192, 0.2)', // Cash
          'rgba(54, 162, 235, 0.2)', // Stock
          'rgba(153, 102, 255, 0.2)', // Bond
          'rgba(255, 206, 86, 0.2)', // Gold
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 206, 86, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">每日资产健康报告</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">资产分布</h3>
          <div className="w-full max-w-xs mx-auto">
            <Pie data={data} />
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">健康度评估</h3>
            <div className="flex items-center space-x-4">
              <div className="text-4xl font-bold text-blue-600">{report.health_score}</div>
              <div className="text-sm text-gray-500">
                / 100 分<br />
                风险等级: {report.risk_assessment}
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">建议与提醒</h3>
            <ul className="list-disc pl-5 space-y-2 text-gray-600">
              {report.recommendations.map((rec, index) => (
                <li key={index}>{rec}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
