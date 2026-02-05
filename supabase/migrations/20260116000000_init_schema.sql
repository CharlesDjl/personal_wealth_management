-- 创建用户表 (作为 public profile，关联 auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255),
    name VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users(created_at);

-- 创建资产表
CREATE TABLE IF NOT EXISTS public.assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('cash', 'stock', 'fund', 'bond', 'gold')),
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(15,4) NOT NULL DEFAULT 0,
    current_price DECIMAL(12,4) NOT NULL DEFAULT 0,
    total_value DECIMAL(15,2) NOT NULL DEFAULT 0,
    purchase_price DECIMAL(12,4),
    purchase_date DATE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_assets_user_id ON public.assets(user_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON public.assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON public.assets(symbol);

-- 创建投资组合目标表
CREATE TABLE IF NOT EXISTS public.portfolio_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    target_cash_pct DECIMAL(5,2) DEFAULT 25.00,
    target_stock_pct DECIMAL(5,2) DEFAULT 25.00,
    target_bond_pct DECIMAL(5,2) DEFAULT 25.00,
    target_gold_pct DECIMAL(5,2) DEFAULT 25.00,
    strategy_name VARCHAR(50) DEFAULT 'permanent_portfolio',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_portfolio_targets_user_id ON public.portfolio_targets(user_id);

-- 创建报告表
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    total_assets DECIMAL(15,2) NOT NULL,
    cash_value DECIMAL(15,2) NOT NULL DEFAULT 0,
    stock_value DECIMAL(15,2) NOT NULL DEFAULT 0,
    bond_value DECIMAL(15,2) NOT NULL DEFAULT 0,
    gold_value DECIMAL(15,2) NOT NULL DEFAULT 0,
    asset_allocation JSONB NOT NULL,
    health_score INTEGER CHECK (health_score >= 0 AND health_score <= 100),
    risk_level VARCHAR(20),
    recommendations JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_date ON public.reports(report_date);
CREATE INDEX IF NOT EXISTS idx_reports_health_score ON public.reports(health_score);

-- 启用 RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

-- 权限设置
-- 允许 Auth 角色操作
GRANT ALL PRIVILEGES ON public.users TO service_role;
GRANT ALL PRIVILEGES ON public.assets TO service_role;
GRANT ALL PRIVILEGES ON public.portfolio_targets TO service_role;
GRANT ALL PRIVILEGES ON public.reports TO service_role;

-- 允许 Authenticated 用户操作
GRANT SELECT, UPDATE, INSERT ON public.users TO authenticated;
GRANT ALL PRIVILEGES ON public.assets TO authenticated;
GRANT ALL PRIVILEGES ON public.portfolio_targets TO authenticated;
GRANT ALL PRIVILEGES ON public.reports TO authenticated;

-- 允许 Anon 用户读取(如果有公共数据需求，目前主要是用户私有数据，暂不开放 Anon 读权限，除了特定公开接口)
-- 暂时只给 Anon 角色最基础的权限，防止报错，实际数据访问受 RLS 控制
GRANT SELECT ON public.users TO anon;

-- RLS 策略

-- Users 表策略
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Assets 表策略
CREATE POLICY "Users can view own assets" ON public.assets
    FOR ALL USING (auth.uid() = user_id);

-- Portfolio Targets 表策略
CREATE POLICY "Users can manage own portfolio targets" ON public.portfolio_targets
    FOR ALL USING (auth.uid() = user_id);

-- Reports 表策略
CREATE POLICY "Users can view own reports" ON public.reports
    FOR ALL USING (auth.uid() = user_id);

-- 创建 Trigger 处理新用户注册
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, name)
  VALUES (new.id, new.email, split_part(new.email, '@', 1));
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 触发器
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
