# Morphosphere v37.4.91 — HG-FHPMS Native Runtime

## Status

**v37.4.90 — Blueprint MORPHOSPHERE.2026.5.10.1 Full Engineering Compliance**

| Metric | Result |
|--------|:------:|
| A/B/C Stress Benchmark | **40/40 ALL PASS** ✅ |
| Integrated Pipeline | **8/8 ALL PASS** ✅ |
| §16 Database Tables | 7/7 ✅ |
| §10.3 Data Streams | 6/6 ✅ |
| §13.3 Self-Reference Audit | 7/7 fields ✅ |
| §附录B 10-Question Checklist | 10/10 ✅ |

**v37.5: BLOCKED** — requires external data expansion (class_diversity ≥3, motion_regimes ≥5)

## Architecture

```
External Streams → Source Adapter → ProcessWindow → z_t (7D measure)
  → HG-FHPMS Memory Layer
    → Engine A: Manual Fast/Slow/Prior Strata (baseline)
    → Engine B: Topological Inertia M_eff (candidate)
    → Engine C: Guarded Hybrid (compromise)
  → P/R/Xin/U Transition Boundary
  → RLIS Ledger / Xin Conservation
  → A/B Stress Benchmark → Promotion Decision
```

## Quick Start

```bash
# Run full verification suite (48 checks)
python scripts/run_all_checks.py

# Run A/B stress benchmark only (40 checks)
python runners/run_v37450_ab_test.py

# Run integrated pipeline only (8 checks)
python runners/run_v37460_integrated.py

# Generate DB lock file for provenance
python scripts/gen_db_lock.py db/v37490_ab_test.db

# View database table stats
python scripts/db_info.py
```

## Directory Structure

```
morphosphere_v2pp/
├── runners/           # Active test runners
│   ├── run_v37450_ab_test.py      # A/B/C stress benchmark (40 checks)
│   ├── run_v37460_integrated.py   # Integrated pipeline (8 checks)
│   └── archive/                   # Historical runners
├── db/                # SQLite databases
│   ├── v37490_ab_test.db          # A/B stress benchmark DB
│   ├── v37460_integrated.db       # Integrated pipeline DB
│   └── scratch/                   # Archived old databases
├── engines/           # Engine module copies
├── docs/              # §17 documentation
│   ├── V37490_AB_STRESS_PROTOCOL.md
│   └── V37490_PROMOTION_DECISION_RULES.md
├── reports/           # Generated CSV/MD outputs
│   └── archive/                   # Historical report directories
├── migrations/        # SQL table definitions
├── scripts/           # Utility scripts
│   ├── run_all_checks.py          # One-shot full verification
│   ├── gen_db_lock.py             # DB provenance lock generator
│   ├── db_info.py                 # Database inspector
│   └── archive/                   # Old temp scripts
├── configs/           # Configuration files
├── src/               # Core morphosphere package
├── hebbian_ab_engine.py           # Three-engine A/B/C harness
├── pipeline_engine.py             # Core pipeline engine
├── ctc_source_adapter.py          # CTC real data adapter
├── formula_candidate_registry.py  # Formula competition engine
├── motion_recognition_engine.py   # Bayesian motion recognizer
├── variational_em_engine.py       # Variational EM engine
└── variational_gmm_engine.py      # Variational GMM engine
```

## Three Engines

| Engine | Strategy | Key Parameters |
|--------|----------|----------------|
| **A — Manual Strata** | Fast/slow/prior 3-layer Oja | α_fast=0.18, α_slow=0.05 |
| **B — Topological Inertia** | M_eff-gated 7-input Hebbian | M_max=8.0, η=0.18, κ=0.15 |
| **C — Guarded Hybrid** | A's structure + B's alpha modulation | mod=[0.5, 1.5] |

## Current Verdict

**KEEP_AS_CANDIDATE** — B wins 2/3 dimensions (survival + adaptation) but not all 3.
Occam's razor keeps A as default. B retained for further testing.

## Blueprint Reference

MORPHOSPHERE.2026.5.10.1 (2026-05-10)
