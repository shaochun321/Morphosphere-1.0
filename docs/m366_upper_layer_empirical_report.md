# Morphosphere v36.6 Upper-Layer Empirical Analysis

**Purpose:** answer what the information spacetime trajectories and the upper T/O/P/R/Xin architecture actually recognize, separate, and transform. This is not a deployment PASS report.

**Input:** `Morphosphere_v36_6_full_materialized_deploy_pass9` DB outputs.  
**Output DB:** `m366_upper_layer_empirical.db`  
**Integrity:** `ok`

## 1. Direct answer

The current upper layer recognizes **windowed information processes**, not semantic objects. It separates each trajectory window into:

- **T:** trace/trajectory/window continuity material;
- **O:** support/object candidate carrier;
- **P:** stable or positive support proxy;
- **R:** structured counter-evidence pressure;
- **Xin/Xi:** unclosed residual retained by ledger and re-entry policy.

This run contains **532 T/O/P/R/Xin windows** built from **4,575 information points**. It is empirically conservative: P is mostly candidate-level support, R is mostly low but measurable counter-pressure, and Xin is low/decaying/ledger-retained rather than a strong novelty outbreak.

## 2. What the upper layer recognized and separated

|role_proxy|window_count|percentage|empirical_mean_p|empirical_mean_r|empirical_mean_xin|meaning|
|---|---|---|---|---|---|---|
|XIN_RESIDUAL_PRESSURE|201|0.3778|0.5478|0.3006|0.3179|windows with high residual/phase conflict retained as Xin pressure|
|LOW_OR_MIXED_SIGNAL|137|0.2575|0.5593|0.2823|0.2631|windows without one dominant upper-layer role proxy|
|R_COUNTER_PRESSURE|92|0.1729|0.5375|0.3356|0.2614|windows where counter-evidence pressure is in the upper empirical quartile|
|P_STABLE_SUPPORT|65|0.1222|0.6108|0.2765|0.2224|high-confidence stable support windows relative to this dataset|
|P_R_MIXED_COMPETITION|37|0.06955|0.5825|0.3054|0.2718|windows where stable support and counter pressure both remain visible|


Interpretation: these are empirical proxy roles, not semantic labels and not truth classes.

## 3. T/O/P/R/Xin metric distributions

|metric_group|metric_name|n|min|q25|median|q75|max|mean|interpretation|
|---|---|---|---|---|---|---|---|---|---|
|P|attention_yield_ratio|532|0|0|0|0.01875|0.1029|0.01296|stable P budget release toward R/masking/Xin|
|P|p_measure_value|532|0.3157|0.5482|0.5659|0.5839|0.6589|0.5591|positive/stable support measure|
|P|prediction_mass|532|0|0.1778|0.3324|0.4831|1|0.3473|predictive support contribution inside P|
|R|masking_exposure_gain|532|0|0.1143|0.1374|0.1674|0.4865|0.144|how much R exposes masking need|
|R|r_measure_value|532|0.1104|0.2832|0.3001|0.3153|0.5138|0.2993|counter-evidence / refutational pressure measure|
|R|recursive_reentry_priority|532|0.2331|0.3286|0.3378|0.3461|0.4542|0.3373|priority for recursive re-entry / inspection|
|T|direction_coherence|532|0|0.1778|0.3324|0.4831|1|0.3473|process direction coherence; higher means less direction switching|
|T|mean_speed|532|0|2.211|2.935|3.834|25.58|3.165|motion/transport speed proxy inside trajectory window|
|T|path_length|532|0|54.64|76.01|99.05|170.8|76.35|information trajectory geometric/transport path length proxy|
|Xin|phase_conflict_mass|532|0|0.3601|0.4407|0.4978|0.9051|0.42|phase conflict component of Xin residual|
|Xin|unbound_duration|532|0|6.018|7.173|8.419|11.23|7.016|duration not tightly bound to P/R|
|Xin|xi_residual_mass|532|0.1746|0.2322|0.2777|0.3183|0.416|0.2792|unclosed residual mass retained after P/R/masking|


## 4. Information state transitions across tracks

The table below summarizes role transitions between consecutive trajectory windows in the same track.

|from_role|to_role|transition_count|representative_track|representative_from_window|representative_to_window|
|---|---|---|---|---|---|
|XIN_RESIDUAL_PRESSURE|XIN_RESIDUAL_PRESSURE|137|01_10|tw25_01-10_000_f000_027|tw25_01-10_001_f007_034|
|LOW_OR_MIXED_SIGNAL|LOW_OR_MIXED_SIGNAL|85|01_29|tw25_01-29_000_f000_027|tw25_01-29_001_f007_034|
|R_COUNTER_PRESSURE|R_COUNTER_PRESSURE|58|01_15|tw25_01-15_001_f007_034|tw25_01-15_002_f014_041|
|P_STABLE_SUPPORT|P_STABLE_SUPPORT|49|01_1|tw25_01-1_000_f000_027|tw25_01-1_001_f007_034|
|P_R_MIXED_COMPETITION|P_R_MIXED_COMPETITION|18|01_23|tw25_01-23_001_f007_034|tw25_01-23_002_f014_041|
|XIN_RESIDUAL_PRESSURE|LOW_OR_MIXED_SIGNAL|14|01_24|tw25_01-24_009_f063_090|tw25_01-24_010_f070_091|
|LOW_OR_MIXED_SIGNAL|XIN_RESIDUAL_PRESSURE|11|01_29|tw25_01-29_003_f021_048|tw25_01-29_004_f028_055|
|XIN_RESIDUAL_PRESSURE|R_COUNTER_PRESSURE|8|01_15|tw25_01-15_000_f000_027|tw25_01-15_001_f007_034|
|R_COUNTER_PRESSURE|LOW_OR_MIXED_SIGNAL|7|01_15|tw25_01-15_009_f063_090|tw25_01-15_010_f070_091|
|P_R_MIXED_COMPETITION|LOW_OR_MIXED_SIGNAL|7|01_28|tw25_01-28_007_f049_076|tw25_01-28_008_f056_083|
|P_STABLE_SUPPORT|LOW_OR_MIXED_SIGNAL|6|01_1|tw25_01-1_003_f021_048|tw25_01-1_004_f028_055|
|P_R_MIXED_COMPETITION|R_COUNTER_PRESSURE|6|01_23|tw25_01-23_006_f042_069|tw25_01-23_007_f049_076|


These transitions show how information changes role across windows: it can remain stable support, become mixed P/R competition, or enter higher residual pressure.

## 5. Attention layer empirical results

|label|count|share|interpretation|
|---|---|---|---|
|NEUTRAL|79|0.6583|attention path did not justify immediate escalation|
|EFFECTIVE|26|0.2167|attention path improved or stabilized target|
|INEFFECTIVE|10|0.08333|attention did not produce useful result|
|NOVELTY_DISCOVERED|5|0.04167|candidate novelty surfaced by path audit|


Attention is mostly neutral in this dataset, with a smaller number of effective and novelty-discovered cases. This supports the interpretation that v35 is a **resource allocation / audit layer**, not an action layer.

## 6. Hyperedge / high-order relation results

- Hyperedges: **120**
- Incidence rows: **855**
- Average arity: **7.125**
- Arity range: **7–8**

This means the upper layer does contain high-order relation events rather than just binary edges. The important limitation is that many high-order links still use materialized or inferred backprojection rather than raw direct bottom FK.

## 7. Variational path / Xin_var results

|metric_group|metric_name|n|min|q25|median|q75|max|mean|interpretation|
|---|---|---|---|---|---|---|---|---|---|
|action|total_action_proxy|120|0.35|0.6482|0.704|0.7913|0.95|0.708|path-level ledger/action cost proxy|
|components|constraint_violation|120|0|0|0|0|0.15|0.0075|constraint component of Xin_var|
|components|ledger_balance_residual|120|0|0.024|0.054|0.084|0.108|0.054|ledger component of Xin_var|
|delta_xin|cleaned_delta_xin|120|-0.057|-0.018|0.002|0.022|0.057|0.001|fallback local Delta-Xin, not main definition|
|stationarity|finite_variation_residual|120|0.000677|0.002756|0.005404|0.009978|0.01838|0.006793|discrete stationarity defect / finite variation residual|
|xin_var|xin_var_total|120|0.0649|0.1623|0.1988|0.2376|0.4277|0.2027|variational Xin closure defect|


Key point: **Delta-Xin remains a fallback local reading.** The upper layer's stronger object is `Xin_var`, which combines stationarity, ledger, constraint, and anomaly components.

## 8. R-band / coupler / Xin triage results

|source_table|status_or_class|count|interpretation|
|---|---|---|---|
|v363_r_spacetime_band_candidate|accepted_candidate|87|R-band candidate outcome; pseudo-continuity proposal, not physical continuity|
|v363_r_spacetime_band_candidate|needs_review|3|R-band candidate outcome; pseudo-continuity proposal, not physical continuity|
|v364_coupler_decision_report|selected_under_constraints|22|constrained coupler decision under ledger/Xin/P-anchor costs|
|v364_coupler_decision_report|selected_as_least_bad_with_deferred_xin|18|constrained coupler decision under ledger/Xin/P-anchor costs|
|v364_xin_triage_policy|background|17|Xin triage class after R-band/coupler processing|
|v364_xin_triage_policy|deferred|17|Xin triage class after R-band/coupler processing|
|v364_xin_triage_policy|external_leakage_candidate|17|Xin triage class after R-band/coupler processing|
|v364_xin_triage_policy|foreground|17|Xin triage class after R-band/coupler processing|
|v364_xin_triage_policy|thermalized|17|Xin triage class after R-band/coupler processing|


This shows R is not only negative evidence: it is routed into pseudo-continuity construction and then Xin triage.

## 9. Xin carrier / external readout

|definition_family|carrier_count|mean_attention_priority|meaning|
|---|---|---|---|
|external_leakage_hypothesis_proxy|9|0.5895|external definition family attached to minimal Xin carrier, readout only|
|continuity_defect_proxy|5|0.5058|external definition family attached to minimal Xin carrier, readout only|
|model_capacity_gap_proxy|5|0.5168|external definition family attached to minimal Xin carrier, readout only|
|pde_like_solver_gap_proxy|4|0.4648|external definition family attached to minimal Xin carrier, readout only|
|noether_style_closure_defect_proxy|4|0.4708|external definition family attached to minimal Xin carrier, readout only|
|deferred_cognitive_boundary_proxy|4|0.4755|external definition family attached to minimal Xin carrier, readout only|


External readout remains read-only. It explains or classifies carriers but does not rewrite source facts or P/R/Xin truth.

## 10. Sample-level full-chain traces

|sample_id|source_point_id|trajectory_trace_id|point_frame|p_value|r_value|xin_mass|hyperedge_id|variational_path_id|xin_carrier_id|readout_id|
|---|---|---|---|---|---|---|---|---|---|---|
|trace_sample_0000|ip25_01_t000_trk01-10|tw25_01-10_000_f000_027|0|0.5665|0.3095|0.2323|he35h_0001|path362_0000|xinc365_f2ec5945886df76a|read365_5290da127f61b0d7|
|trace_sample_0001|ip25_01_t007_trk01-10|tw25_01-10_001_f007_034|7|0.5749|0.3021|0.2316|he35h_0002|path362_0001|xinc365_f9b0c529446d6860|read365_bb5cdaa77daadeb0|
|trace_sample_0002|ip25_01_t014_trk01-10|tw25_01-10_002_f014_041|14|0.5884|0.2903|0.2304|he35h_0003|path362_0002|xinc365_509738458bc0cae7|read365_f927b47a541c913d|
|trace_sample_0003|ip25_01_t021_trk01-10|tw25_01-10_003_f021_046|21|0.5764|0.2912|0.2292|he35h_0004|path362_0003|xinc365_anom_44704c22a9ac4457|read365_99e62ae4576c72e7|
|trace_sample_0004|ip25_01_t047_trk01-12|tw25_01-12_000_f047_047|47|0.3162|0.1461|0.2682|he35h_0005|path362_0004|xinc365_anom_55d6152e8b76297e|read365_afe59e6e0ab5fd60|
|trace_sample_0005|ip25_01_t047_trk01-14|tw25_01-14_000_f047_049|47|0.4197|0.3078|0.2148|he35h_0006|path362_0005|xinc365_anom_1e0995fda31b74c0|read365_71f32874641b0aab|
|trace_sample_0006|ip25_01_t000_trk01-15|tw25_01-15_000_f000_027|0|0.5832|0.3126|0.2207|he35h_0007|path362_0006|xinc365_anom_5bf21122c41ed037|read365_30d0eea1c644225a|
|trace_sample_0007|ip25_01_t007_trk01-15|tw25_01-15_001_f007_034|7|0.5807|0.322|0.2229|he35h_0008|path362_0007|xinc365_anom_d1daa018a74ad2c8|read365_a0bc823456309464|


These are materialized examples showing how one source information point can be followed to trajectory, P/R/Xin, ledger, hyperedge, variational path, Xin carrier, and readout. They are excellent for inspection, but upper overlay links should still be treated as materialized samples unless raw direct FK is explicit.

## 11. What information becomes after upper-layer processing

| Step | Transformation | Output |
|---|---|---|
| 1 | source event → information point | observable time/coordinate/provenance event |
| 2 | information point → coordinate transform | 3D/4D backprojection and evidence anchor |
| 3 | coordinate trace → trajectory window | process continuity material `T` |
| 4 | trajectory → O/P/R/Xin | support, counter-evidence, residual roles |
| 5 | P/R/Xin → attention/masking | resource request and audit focus |
| 6 | attention/R/Xin/ledger → hyperedge | high-order multi-subject event |
| 7 | candidate path → S_IE_proxy / Xin_var | path-level ledger-scored candidate |
| 8 | R → R-band/coupler | pseudo-continuity and residual triage |
| 9 | unresolved Xin → carrier/readout | minimal mainline carrier + external read-only interpretation |

## 12. Findings

|finding_id|finding_kind|statement|evidence_count|consequence|
|---|---|---|---|---|
|F001|recognition|The current bottom-to-middle layer recognizes 532 trajectory windows from 4,575 information points and splits each into P/R/Xin measures.|532|The upper layer is not empty; it is a windowed recognition/separation system.|
|F002|separation|P is mostly candidate-level stable support, R is mostly low but measurable counter-pressure, and Xin is low/decaying but ledger-retained.|P:532 R:532 Xin:532|Current run shows conservative residual retention rather than strong novelty outbreak.|
|F003|attention|v35 attention mostly returns NEUTRAL, with 26 EFFECTIVE and 5 NOVELTY_DISCOVERED cases.|120|Attention layer is a resource-allocation/audit layer, not an action layer.|
|F004|hyperedge|v35H hyperedges average >7 nodes and therefore express multi-subject binding rather than binary edges.|120 hyperedges / 855 incidence|High-order relation indexing exists, but bottom FK remains partially inferred.|
|F005|variational|v36.2 computes action proxies, stationarity defects, and Xin_var for 120 candidate paths; delta-Xin is only fallback.|120|The upper layer changes information from local window readings into path-level ledger-scored candidates.|
|F006|rband|R-band/coupler layers build pseudo-continuity candidates and triage Xin into foreground/background/deferred/thermalized/external leakage classes.|90 bands / 85 triage|R is not merely negative evidence; it becomes continuity-seeking structure.|
|F007|readout|v36.5 preserves Xin as minimal carriers and external readout remains read-only with blocked backwrite attempts.|31 carriers / 31 readouts|Semantic interpretation is externalized and cannot rewrite mainline.|


## 13. Limitations

|limitation_id|limitation|impact|next_analysis_needed|
|---|---|---|---|
|L001|This is an empirical materialized integration analysis, not a native end-to-end runtime recomputation.|It demonstrates upper-layer behavior in current stored outputs but not single-run live causality.|Create native full-chain run skeleton with single run_id if needed.|
|L002|Many upper-layer hyperedge/backprojection links remain proxy/inferred rather than raw direct FK.|High-order relation claims must remain auditable proxy, not hard bottom facts.|Upgrade upstream writers or add direct source refs in future.|
|L003|Current T/O/P/R/Xin run is conservative: R is mostly low and Xin is low/decaying/ledger-retained.|Good for boundary stability; limited evidence of strong novelty/emergence in this dataset.|Run on stronger perturbation/novelty data or targeted examples.|
|L004|External modules are readout-only; they do not co-run as live external processes.|Readout results explain carriers but do not alter mainline computation.|If desired, add offline batch external-module scheduler with read-only contract.|


## 14. Files

- `m366_upper_layer_empirical.db`: full empirical analysis DB.
- `m366_upper_layer_empirical_summary.json`: compact summary.
- CSV extracts for distributions, roles, transitions, attention, variational paths, R-band, Xin definitions, findings and limitations.
