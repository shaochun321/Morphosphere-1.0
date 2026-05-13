-- ═══════════════════════════════════════════════════════════════
-- v37.4.50: Hebbian A/B Test — 拓扑惯性 vs 机械分层
-- ═══════════════════════════════════════════════════════════════

-- A/B 引擎权重镜像表
CREATE TABLE IF NOT EXISTS v37450_ab_weight_mirror (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    engine TEXT,               -- 'A_strata' or 'B_inertia'
    from_entity_id TEXT,
    to_entity_id TEXT,
    weight_value REAL,
    inertia_mass REAL,         -- M(Φ) for engine B, 1.0 for engine A
    cumulative_potential REAL,  -- Φ: accumulated xin impacts
    layer TEXT,                -- 'fast' or 'slow' (for engine A)
    tick INTEGER,
    created_at TEXT
);

-- A/B 指标日志表（每轮评估写一行）
CREATE TABLE IF NOT EXISTS v37450_ab_metric_log (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    engine TEXT,
    tick INTEGER,
    phase TEXT,                -- 'warmup', 'noise_storm', 'regime_shift', 'normal'
    p_core_survival_rate REAL, -- 指标1: 噪音风暴下P-Core存活率
    adaptation_latency REAL,   -- 指标2: 新规律响应延迟(Tick数)
    compute_overhead_ms REAL,  -- 指标3: 计算开销
    weight_entropy REAL,       -- Shannon entropy of weight distribution
    dead_node_count INTEGER,   -- M(Φ) > 0.9 * M_max 的节点数
    exploded_count INTEGER,    -- ΔW > 1.0 的更新截断次数
    avg_weight REAL,
    max_weight REAL,
    min_weight REAL,
    total_weights INTEGER,
    created_at TEXT
);

-- A/B 最终判决表
CREATE TABLE IF NOT EXISTS v37450_ab_verdict (
    verdict_id TEXT PRIMARY KEY,
    run_id TEXT,
    winner TEXT,               -- 'A_strata', 'B_inertia', or 'DRAW'
    -- 指标1: P-Core 存活率
    survival_a REAL,
    survival_b REAL,
    survival_winner TEXT,
    -- 指标2: 概念响应延迟
    latency_a REAL,
    latency_b REAL,
    latency_winner TEXT,
    -- 指标3: 计算开销
    overhead_a_ms REAL,
    overhead_b_ms REAL,
    overhead_winner TEXT,
    -- 综合
    wins_a INTEGER,
    wins_b INTEGER,
    rationale TEXT,
    created_at TEXT
);

-- A/B 测试配置快照
CREATE TABLE IF NOT EXISTS v37450_ab_config (
    config_id TEXT PRIMARY KEY,
    run_id TEXT,
    m_max REAL,                -- 惯性质量上限
    alpha REAL,                -- 惯性系数
    decay_epsilon REAL,        -- 全局衰减率
    oja_lambda REAL,           -- Oja 衰减系数
    eta REAL,                  -- 学习率
    strata_absorb_interval INTEGER, -- 机械分层吸收周期
    noise_storm_ticks INTEGER,
    regime_shift_ticks INTEGER,
    warmup_ticks INTEGER,
    created_at TEXT
);
