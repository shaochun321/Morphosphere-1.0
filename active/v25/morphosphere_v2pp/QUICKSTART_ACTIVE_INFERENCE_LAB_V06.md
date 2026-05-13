# Quickstart: Active-Inference / System-Identification External Lab v0.6

## 一键验证

```bash
cd morphosphere_active_inference_lab_v06_package
./run_local_active_inference_lab.sh
```

## 单独重建 v0.6 外部实验室

```bash
python -S morphosphere_v2pp/scripts/run_active_inference_lab_v06.py \
  --db outputs/morphosphere_active_inference_lab_v06_output_database.db \
  --report-dir morphosphere_v2pp/reports

python -S morphosphere_v2pp/scripts/run_active_inference_acceptance_v06.py \
  outputs/morphosphere_active_inference_lab_v06_output_database.db
```

## 重要边界

`v0.6` 只生成候选权重和 decision note。它不自动写入主线，不修改源事实，不允许 Xi 顶替 P/R。
