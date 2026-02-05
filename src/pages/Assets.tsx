import React, { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { Asset, AssetType } from '../types';
import { Plus, Trash2, Edit2, RefreshCw, Upload } from 'lucide-react';
import { cn } from '../lib/utils';

export const Assets = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshingId, setRefreshingId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [formData, setFormData] = useState({
    asset_type: 'stock' as AssetType,
    symbol: '',
    name: '', // 新增 name 字段
    quantity: 0,
    purchase_price: 0,
    purchase_date: new Date().toISOString().split('T')[0]
  });
  
  // 新增：编辑状态
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);

  const fetchAssets = async () => {
    try {
      setLoading(true); // 显示加载状态
      const response = await apiClient.get<Asset[]>('/assets/');
      setAssets(response.data);
    } catch (error) {
      console.error('Error fetching assets:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('请上传图片文件');
      return;
    }

    setUploading(true);
    const uploadFormData = new FormData();
    uploadFormData.append('file', file);

    try {
      const response = await apiClient.post<Asset[]>('/assets/import-screenshot', uploadFormData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      const imported = response.data;
      if (imported.length > 0) {
        alert(`成功识别并导入 ${imported.length} 项资产`);
        fetchAssets(); // 刷新列表
      } else {
        alert('未能从图片中识别出有效资产，请确保截图清晰包含资产名称和数量');
      }
    } catch (error) {
      console.error('Error uploading screenshot:', error);
      alert('上传分析失败，请稍后重试');
    } finally {
      setUploading(false);
      // 清空 input value 以允许重复上传同一文件
      e.target.value = '';
    }
  };

  // 全局刷新所有资产
  const handleRefreshAll = async () => {
    if (loading) return;
    try {
      setLoading(true);
      // 先重新获取列表，后端会自动尝试更新价格（如果未命中缓存或有新逻辑）
      // 或者如果后端实现了批量刷新接口，这里调用批量刷新
      // 目前后端 GET /assets/overview 会触发更新逻辑，或者我们可以逐个刷新
      // 为了简单有效，这里我们重新调用 fetchAssets，因为它会从后端获取最新数据
      // 注意：如果后端 GET /assets/ 只是读库，那我们需要一个批量刷新接口
      // 暂时用逐个刷新的方式模拟批量刷新（或者让用户手动点）
      // 更好的方式是调用 fetchAssets，并假设后端在 GET 时会检查时效性
      // 但根据当前后端逻辑，GET /assets/ 只是读库。
      // 我们改进一下：重新加载页面数据
      await fetchAssets();
      alert('数据已重新加载');
    } catch (error) {
      console.error('Error refreshing all:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async (id: string) => {
    setRefreshingId(id);
    try {
      const response = await apiClient.post<Asset>(`/assets/${id}/refresh`);
      // 局部更新：只更新这一行的数据，避免全量刷新带来的闪烁
      setAssets(prev => prev.map(a => a.id === id ? response.data : a));
    } catch (error) {
      console.error('Error refreshing asset:', error);
      alert('更新失败，请稍后重试或检查网络');
    } finally {
      setRefreshingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这项资产吗？')) return;
    try {
      await apiClient.delete(`/assets/${id}`);
      setAssets(assets.filter(a => a.id !== id));
    } catch (error) {
      console.error('Error deleting asset:', error);
    }
  };

  const handleEdit = (asset: Asset) => {
    setEditingAsset(asset);
    setFormData({
      asset_type: asset.asset_type,
      symbol: asset.symbol,
      name: asset.name || '',
      quantity: asset.quantity,
      purchase_price: asset.purchase_price || 0,
      purchase_date: asset.purchase_date ? asset.purchase_date.toString().split('T')[0] : new Date().toISOString().split('T')[0]
    });
    setShowAddModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingAsset) {
        // 更新逻辑
        await apiClient.put(`/assets/${editingAsset.id}`, formData);
      } else {
        // 创建逻辑
        await apiClient.post('/assets/', formData);
      }
      setShowAddModal(false);
      setEditingAsset(null); // 清除编辑状态
      fetchAssets();
      // 重置表单
      setFormData({
        asset_type: 'stock',
        symbol: '',
        name: '',
        quantity: 0,
        purchase_price: 0,
        purchase_date: new Date().toISOString().split('T')[0]
      });
    } catch (error) {
      console.error('Error saving asset:', error);
      alert('保存失败，请检查输入或重试');
    }
  };

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isBatchMode, setIsBatchMode] = useState(false);

  // ... (其他状态保持不变)

  const toggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleBatchDelete = async () => {
    if (!isBatchMode) {
        setIsBatchMode(true);
        return;
    }
    
    if (selectedIds.size === 0) {
        setIsBatchMode(false); // 退出批量模式
        return;
    }

    if (!confirm(`确定要删除选中的 ${selectedIds.size} 项资产吗？`)) return;

    try {
      await apiClient.post('/assets/batch-delete', { asset_ids: Array.from(selectedIds) });
      setAssets(assets.filter(a => !selectedIds.has(a.id)));
      setSelectedIds(new Set());
      setIsBatchMode(false);
      alert('批量删除成功');
    } catch (error) {
      console.error('Error batch deleting assets:', error);
      alert('批量删除失败，请重试');
    }
  };

  // 跨组全选逻辑
  const handleSelectAll = (checked: boolean) => {
      if (checked) {
          setSelectedIds(new Set(assets.map(a => a.id)));
      } else {
          setSelectedIds(new Set());
      }
  };

  // ... (表格渲染部分需要大改)

  // 按类型分组
  const groupedAssets = assets.reduce((acc, asset) => {
    const type = asset.asset_type;
    if (!acc[type]) acc[type] = [];
    acc[type].push(asset);
    return acc;
  }, {} as Record<AssetType, Asset[]>);

  const assetTypeLabels: Record<AssetType, string> = {
    cash: '现金',
    stock: '股票',
    fund: '基金',
    bond: '债券',
    gold: '黄金'
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">资产管理</h1>
        <div className="flex space-x-2">
            {isBatchMode && (
                <div className="flex items-center mr-4">
                    <input 
                        type="checkbox"
                        id="selectAll"
                        className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        checked={assets.length > 0 && selectedIds.size === assets.length}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                    />
                    <label htmlFor="selectAll" className="text-sm text-gray-700">全选所有 ({assets.length})</label>
                </div>
            )}
          {/* 上传按钮 */}
          <div className="relative">
             <input
                type="file"
                accept="image/*"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                onChange={handleFileUpload}
                disabled={uploading}
             />
             <button
                disabled={uploading}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
             >
                <Upload className={cn("h-4 w-4 mr-2", uploading && "animate-spin")} />
                {uploading ? '分析中...' : '截图导入'}
             </button>
          </div>

          <button
            onClick={handleBatchDelete} 
            className={cn(
                "inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md bg-white hover:bg-gray-50",
                isBatchMode && selectedIds.size > 0 ? "text-red-700 border-red-300 hover:bg-red-50" : "text-gray-700"
            )}
          >
            <Trash2 className={cn("h-4 w-4 mr-2", isBatchMode && selectedIds.size > 0 ? "text-red-500" : "text-gray-500")} />
            {isBatchMode ? (selectedIds.size > 0 ? `删除 (${selectedIds.size})` : '取消批量') : '批量管理'}
          </button>
          <button
            onClick={handleRefreshAll}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
            更新最新价格
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            添加资产
          </button>
        </div>
      </div>
      
      {/* ... (后续表格内容保持不变) */}

      <div className="space-y-6">
        {loading && assets.length === 0 ? (
          <div className="text-center py-10">加载中...</div>
        ) : assets.length === 0 ? (
          <div className="text-center py-10 text-gray-500">暂无资产，请添加</div>
        ) : (
          (Object.entries(groupedAssets) as [AssetType, Asset[]][]).map(([type, typeAssets]) => (
            <div key={type} className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center">
                  <span className={cn(
                    "w-3 h-3 rounded-full mr-2",
                    type === 'cash' ? "bg-gray-400" :
                    type === 'stock' ? "bg-blue-500" :
                    type === 'bond' ? "bg-green-500" :
                    type === 'gold' ? "bg-yellow-500" :
                    "bg-purple-500"
                  )}></span>
                  {assetTypeLabels[type]}
                  <span className="ml-2 text-sm text-gray-500 font-normal">({typeAssets.length})</span>
                </h3>
                <span className="text-sm font-medium text-gray-900">
                  总值: ¥{typeAssets.reduce((sum, a) => sum + a.total_value, 0).toFixed(2)}
                </span>
              </div>
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {isBatchMode && (
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-10">
                            <input 
                                type="checkbox" 
                                onChange={(e) => {
                                    if (e.target.checked) {
                                        setSelectedIds(new Set(typeAssets.map(a => a.id)));
                                    } else {
                                        setSelectedIds(new Set());
                                    }
                                }}
                                checked={typeAssets.length > 0 && typeAssets.every(a => selectedIds.has(a.id))}
                            />
                        </th>
                    )}
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/5">代码/名称</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-1/6">持有数量</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-1/6">买入/现价</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-1/6">盈亏</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-1/6">总价值</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {typeAssets.map((asset) => {
                    const cost = (asset.purchase_price || 0) * asset.quantity;
                    const profit = asset.total_value - cost;
                    const profitPercent = cost > 0 ? (profit / cost) * 100 : 0;
                    const isProfit = profit >= 0;
                    
                    return (
                    <tr key={asset.id}>
                      {isBatchMode && (
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              <input 
                                  type="checkbox" 
                                  checked={selectedIds.has(asset.id)}
                                  onChange={() => toggleSelect(asset.id)}
                              />
                          </td>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        <div className="flex flex-col">
                          <span className="font-bold">{asset.name && asset.name.trim() !== '' ? asset.name : asset.symbol}</span>
                          <span className="text-xs text-gray-500">{asset.name && asset.name.trim() !== '' && asset.name !== asset.symbol ? asset.symbol : ''}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                        {asset.quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                        <div className="flex flex-col">
                          <span className="text-gray-900">¥{asset.current_price.toFixed(4)}</span>
                          <span className="text-xs text-gray-400">买: ¥{(asset.purchase_price || 0).toFixed(4)}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                        <div className={cn("flex flex-col", isProfit ? "text-red-600" : "text-green-600")}>
                          <span>{isProfit ? '+' : ''}{profit.toFixed(2)}</span>
                          <span className="text-xs">{isProfit ? '+' : ''}{profitPercent.toFixed(2)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-medium">
                        ¥{asset.total_value.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                        <button
                          onClick={() => handleRefresh(asset.id)}
                          disabled={refreshingId === asset.id}
                          className={cn(
                            "text-blue-600 hover:text-blue-900 disabled:opacity-50",
                            refreshingId === asset.id && "animate-spin"
                          )}
                          title="刷新价格"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(asset)}
                          className="text-indigo-600 hover:text-indigo-900"
                          title="编辑"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(asset.id)}
                          className="text-red-600 hover:text-red-900"
                          title="删除"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );})}
                </tbody>
              </table>
            </div>
          ))
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <form onSubmit={handleSubmit}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">添加新资产</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">类型</label>
                      <select
                        value={formData.asset_type}
                        onChange={(e) => setFormData({ ...formData, asset_type: e.target.value as AssetType })}
                        className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      >
                        <option value="cash">现金</option>
                        <option value="stock">股票</option>
                        <option value="fund">基金</option>
                        <option value="bond">债券</option>
                        <option value="gold">黄金</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">名称 (可选)</label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="例如: 贵州茅台"
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">代码/符号</label>
                      <input
                        type="text"
                        required
                        value={formData.symbol}
                        onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                        placeholder="例如: 600519 (茅台) 或 CNY"
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">数量</label>
                      <input
                        type="number"
                        required
                        step="0.0001"
                        value={formData.quantity}
                        onChange={(e) => setFormData({ ...formData, quantity: parseFloat(e.target.value) })}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">买入价格 (可选)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.purchase_price}
                        onChange={(e) => setFormData({ ...formData, purchase_price: parseFloat(e.target.value) })}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    保存
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    取消
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
