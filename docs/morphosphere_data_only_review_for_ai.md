# Morphosphere 数据审视版（给其他 AI）

> 目的：只列数据、表、计数、关系、边界。尽量不做定义解释。

- generated_at: `2026-05-06T13:35:08.389401Z`
- analyzed_package: `Morphosphere_v36_6_complete_deploy_pass14.tar.zst`
- run_type_observed: `materialized_integration_run + native-shaped_replay_samples`
- 不等同于：`online native runtime`、`true PDE/continuous field`、`fully direct FK graph`

## 1. DB 清单

| DB path | MB | tables | nonempty_tables | estimated_rows | role/purpose |
| --- | --- | --- | --- | --- | --- |
| outputs/m25.db | 26.32 | 346 | 321 | 65068 | v25 Evidence Reconstruction / information point, coordinate transform, trajectory window, P/R/Xin measures |
| outputs/m34.db | 88.71 | 444 | 419 | 204933 | v34 Full base governance / proxy + external entropy control plane on cumulative base |
| outputs/m35.db | 0.25 | 14 | 14 | 1087 | v35 Attention proposal + path-integral audit overlay |
| outputs/m35H.db | 0.26 | 8 | 8 | 1879 | v35H Hyperedge incidence sidecar |
| outputs/m36.db | 0.16 | 11 | 11 | 650 | v36 Dissipative source / information-energy metric proxy |
| outputs/m361.db | 0.18 | 11 | 11 | 865 | v36.1 Variational external ledger bridge |
| outputs/m362.db | 0.18 | 11 | 11 | 759 | v36.2 Variational action revision / Xin_var bridge |
| outputs/m363.db | 0.21 | 11 | 11 | 1010 | v36.3 R spacetime band / Xin continuity bridge |
| outputs/m364.db | 0.25 | 12 | 12 | 1457 | v36.4 Constrained coupler / R-band / Xin triage bridge |
| outputs/m365.db | 0.21 | 12 | 12 | 269 | v36.5 Semantic stripping + Xin carrier + external readout overlay |
| outputs/m365_full_rebase.db | 0.04 | 5 | 5 | 89 | v36.5 full-lineage rebase manifest / coverage / boundary proof |
| outputs/v366/m365_full_chain_materialized.db | 11.87 | 24 | 24 | 32224 | Full-chain materialized integration index |
| outputs/v366/m366_process_window_pass3.db | 11.09 | 28 | 28 | 37905 | v36.6 process_window + hypernode spacetime backprojection |
| outputs/v366/m366_implementation_coverage_audit.db | 0.08 | 6 | 6 | 169 | Implementation coverage / maturity audit |
| outputs/v366/m366_upper_layer_empirical.db | 0.62 | 22 | 22 | 1318 | Upper-layer empirical analysis |
| outputs/v366/m366_build_pass12_execution.db | 1.8 | 7 | 7 | 6967 | Native-shaped skeleton + offline stress projection |
| outputs/v366/m366_build_pass13_native_replay.db | 3.36 | 14 | 14 | 8951 | Sample native-shaped replay / perturbation comparison |

## 2. 核心对象计数

### v25_core
| object | count |
| --- | --- |
| information_point_v25 | 4575 |
| coordinate_transform_trace_v25 | 4575 |
| trajectory_window_trace_v25 | 532 |
| p_spacetime_measure_v25 | 532 |
| r_counter_measure_v25 | 532 |
| xi_residual_surface_v25 | 532 |
| decision_evidence_bundle_v25 | 532 |
| attention_yield_event_v25 | 262 |

### v35_attention_verdicts
| verdict | count |
| --- | --- |
| NEUTRAL | 79 |
| EFFECTIVE | 26 |
| INEFFECTIVE | 10 |
| NOVELTY_DISCOVERED | 5 |

### v35h_hyperedge_arity
| hyperedges | avg_arity | min_arity | max_arity |
| --- | --- | --- | --- |
| 120 | 7.125 | 7 | 8 |

### v36_proxy_counts
| object | count |
| --- | --- |
| dissipative_source_registry | 80 |
| delta_xin_field | 64 |
| information_energy_metric_proxy | 160 |
| metric_anchor_audit | 160 |
| curvature_proxy | 120 |

### v362_action_counts
| object | count |
| --- | --- |
| functional_candidates | 5 |
| candidate_paths | 120 |
| discrete_action_scores | 120 |
| stationarity_defect_proxy | 120 |
| xin_var_closure_defect | 120 |
| delta_xin_fallback | 120 |

### v365_readout_counts
| object | count |
| --- | --- |
| xin_minimal_carriers | 31 |
| external_xin_definitions | 6 |
| external_semantic_readouts | 31 |
| readout_backwrite_blocks | 4 |
| xin_reentry_policies | 2 |

### process_window_counts
| object | count |
| --- | --- |
| process_windows | 1633 |
| process_window_members | 22128 |
| hypernode_spacetime_backprojection | 855 |
| hyperedge_spacetime_relations | 2625 |
| coordinate_nonlocal_proxy_audit_examples | 50 |

### process_window_confidence
| materialization_confidence_class | count |
| --- | --- |
| low_materialization_confidence | 842 |
| medium_materialization_confidence | 671 |
| high_materialization_confidence | 120 |

### implementation_maturity
| maturity_level | concept_count | evidence_rows |
| --- | --- | --- |
| BLUEPRINT_ONLY | 5 | 0 |
| DATA_POPULATED | 8 | 3691 |
| MATERIALIZED_INDEX | 13 | 30049 |
| NATIVE_RUN_GENERATED | 29 | 24131 |
| SCHEMA_ONLY | 1 | 6 |

### empirical_roles
| role_proxy | window_count | percentage | mean_p | mean_r | mean_xin |
| --- | --- | --- | --- | --- | --- |
| XIN_RESIDUAL_PRESSURE | 201 | 0.3778 | 0.5478 | 0.3006 | 0.3179 |
| LOW_OR_MIXED_SIGNAL | 137 | 0.2575 | 0.5593 | 0.2823 | 0.2631 |
| R_COUNTER_PRESSURE | 92 | 0.1729 | 0.5375 | 0.3356 | 0.2614 |
| P_STABLE_SUPPORT | 65 | 0.1222 | 0.6108 | 0.2765 | 0.2224 |
| P_R_MIXED_COMPETITION | 37 | 0.0695 | 0.5825 | 0.3054 | 0.2718 |

### empirical_findings
| finding_kind | statement | evidence_count |
| --- | --- | --- |
| recognition | The current bottom-to-middle layer recognizes 532 trajectory windows from 4,575 information points and splits each into P/R/Xin measures. | 532 |
| separation | P is mostly candidate-level stable support, R is mostly low but measurable counter-pressure, and Xin is low/decaying but ledger-retained. | P:532 R:532 Xin:532 |
| attention | v35 attention mostly returns NEUTRAL, with 26 EFFECTIVE and 5 NOVELTY_DISCOVERED cases. | 120 |
| hyperedge | v35H hyperedges average >7 nodes and therefore express multi-subject binding rather than binary edges. | 120 hyperedges / 855 incidence |
| variational | v36.2 computes action proxies, stationarity defects, and Xin_var for 120 candidate paths; delta-Xin is only fallback. | 120 |
| rband | R-band/coupler layers build pseudo-continuity candidates and triage Xin into foreground/background/deferred/thermalized/external leakage classes. | 90 bands / 85 triage |
| readout | v36.5 preserves Xin as minimal carriers and external readout remains read-only with blocked backwrite attempts. | 31 carriers / 31 readouts |

### pass12_stress_projection
| stress_name | trajectory_windows | p_to_r_projected | r_or_p_to_xin_projected | stable_retained | boundary_blocked |
| --- | --- | --- | --- | --- | --- |
| coordinate jitter | 532 | 1 | 0 | 531 | 0 |
| support dropout | 532 | 23 | 0 | 509 | 0 |
| counter-evidence boost | 532 | 513 | 0 | 19 | 0 |
| Xin residual spike | 532 | 1 | 462 | 69 | 0 |
| masking failure | 532 | 450 | 67 | 15 | 0 |
| semantic backwrite attack | 532 | 0 | 0 | 0 | 532 |

### pass13_state_transitions
| scenario_id | transition_class | count | pct |
| --- | --- | --- | --- |
| baseline | stable_retained | 70 | 1.0 |
| coordinate_jitter | observe_retain_shift | 7 | 0.1 |
| coordinate_jitter | stable_retained | 63 | 0.9 |
| counter_boost | P_or_stable_to_R_focus | 66 | 0.942857 |
| counter_boost | stable_retained | 4 | 0.057143 |
| masking_failure | P_or_stable_to_R_focus | 24 | 0.342857 |
| masking_failure | observe_retain_shift | 13 | 0.185714 |
| masking_failure | stable_retained | 33 | 0.471429 |
| semantic_attack | semantic_backwrite_blocked | 70 | 1.0 |
| support_dropout | P_or_stable_to_R_focus | 1 | 0.014286 |
| support_dropout | observe_retain_shift | 13 | 0.185714 |
| support_dropout | stable_retained | 56 | 0.8 |
| xin_spike | R_or_P_to_Xin_escalation | 69 | 0.985714 |
| xin_spike | stable_retained | 1 | 0.014286 |

## 3. 数据关系边（source → upper layer）

| from | to | relation/data edge |
| --- | --- | --- |
| source/envelope | information_point_v25 | source data is converted into information points |
| information_point_v25 | coordinate_transform_trace_v25 | each information point receives coordinate/backprojection traces |
| information_point_v25 | trajectory_window_trace_v25 | information points are grouped/stiched into trajectory windows |
| trajectory_window_trace_v25 | p_spacetime_measure_v25 | trajectory window yields P stable-support measure |
| trajectory_window_trace_v25 | r_counter_measure_v25 | trajectory window yields R counter-evidence measure |
| trajectory_window_trace_v25 | xi_residual_surface_v25 | trajectory window yields Xi/Xin residual surface |
| P/R/Xin measures | decision_evidence_bundle_v25 | evidence bundles preserve the decision trace |
| P/R/Xin measures | v35_attention_region_index | regions are indexed as attention candidates |
| v35_attention_region_index | v35_attention_proposal | attention sandbox proposes where to focus |
| v35_attention_proposal | v35_attentional_path_integral_audit | external ledger path audit scores attention path |
| v35_attention_proposal | v35h_hyperedge_proposal | attention events become high-order hyperedge proposals |
| v35h_hyperedge_proposal | v35h_hyperedge_incidence | hyperedge incidence binds multiple P/R/Xi/mask/ledger/proxy nodes |
| hyperedge/path | v362_candidate_path_inventory | candidate information-spacetime paths are assembled |
| v362_candidate_path_inventory | v362_discrete_action_score | paths are scored via S_IE_proxy |
| v362_discrete_action_score | v362_xin_var_closure_defect | unclosed variational residual becomes Xin_var proxy |
| R/Xin paths | v363_r_spacetime_band_candidate | R continuity is approximated as spacetime bands |
| R-band/Xin | v364 coupling/triage tables | coupler triages paths and Xin residual classes |
| Xin residual | v365_xin_minimal_carrier_state | semanticless mainline stores minimal Xin carriers |
| v365_xin_minimal_carrier_state | v365_external_semantic_readout_result | external readout interprets carriers read-only |
| all layers | v366_process_window_registry | process_window is the materialized index joining information/time/support/process/envelope/ledger |
| v35H hypernodes | v366_hypernode_spacetime_backprojection | hypernodes are backprojected to spacetime as direct/proxy/inferred audit |
| materialized data | pass12/pass13 replay DBs | stress and native-shaped replay evaluate P/R/Xin behavior under scenarios |

## 4. 分组统计查询（来自关键 DB）

### m366_process_window_pass3.db / process_window_materialization_confidence_pass3
| materialization_confidence_class | count |
| --- | --- |
| low_materialization_confidence | 842 |
| medium_materialization_confidence | 671 |
| high_materialization_confidence | 120 |

### m366_process_window_pass3.db / stage2_bypass_and_route_legitimacy_pass3
| stage2_route_status | count |
| --- | --- |
| intentional_bypass_to_toprxin | 532 |
| stage1_preneural_interface_direct | 500 |
| hybrid_route | 330 |
| overlay_governance_route | 271 |

### m366_process_window_pass3.db / v366_hypernode_spacetime_backprojection
| direct_fk_available | count |
| --- | --- |
| 0 | 855 |

### m366_build_pass13_native_replay.db / pass13_state_transition_summary
| scenario_id | transition_class | count |
| --- | --- | --- |
| baseline | stable_retained | 1 |
| coordinate_jitter | observe_retain_shift | 1 |
| coordinate_jitter | stable_retained | 1 |
| counter_boost | P_or_stable_to_R_focus | 1 |
| counter_boost | stable_retained | 1 |
| masking_failure | P_or_stable_to_R_focus | 1 |
| masking_failure | observe_retain_shift | 1 |
| masking_failure | stable_retained | 1 |
| semantic_attack | semantic_backwrite_blocked | 1 |
| support_dropout | P_or_stable_to_R_focus | 1 |
| support_dropout | observe_retain_shift | 1 |
| support_dropout | stable_retained | 1 |
| xin_spike | R_or_P_to_Xin_escalation | 1 |
| xin_spike | stable_retained | 1 |

### m366_build_pass13_native_replay.db / pass13_acceptance_report
| status | count |
| --- | --- |
| PASS | 7 |

### m366_build_pass12_execution.db / pass12_execution_result_matrix
| stress_name | count |
| --- | --- |
| support dropout | 1 |
| semantic backwrite attack | 1 |
| masking failure | 1 |
| counter-evidence boost | 1 |
| coordinate jitter | 1 |
| Xin residual spike | 1 |

### m366_implementation_coverage_audit.db / implementation_coverage
| maturity_level | count |
| --- | --- |
| NATIVE_RUN_GENERATED | 29 |
| MATERIALIZED_INDEX | 13 |
| DATA_POPULATED | 8 |
| BLUEPRINT_ONLY | 5 |
| SCHEMA_ONLY | 1 |

### m366_implementation_coverage_audit.db / implementation_gap_index
| maturity_level | count |
| --- | --- |
| MATERIALIZED_INDEX | 13 |
| NATIVE_RUN_GENERATED | 12 |
| DATA_POPULATED | 8 |
| BLUEPRINT_ONLY | 5 |
| SCHEMA_ONLY | 1 |

## 5. 重点 DB 的最大非空表

## 6. 数据审视重点

### 6.1 已落盘的主要链路计数
| object | count | source DB | note |
| --- | --- | --- | --- |
| information_point_v25 | 4575 | m25/m34 | source-level point data |
| coordinate_transform_trace_v25 | 4575 | m25/m34 | 3D/4D/backprojection trace fields exist |
| trajectory_window_trace_v25 | 532 | m25/m34 | trajectory/T windows |
| p_spacetime_measure_v25 | 532 | m25/m34 | P measure rows |
| r_counter_measure_v25 | 532 | m25/m34 | R measure rows |
| xi_residual_surface_v25 | 532 | m25/m34 | Xin/Xi residual rows |
| decision_evidence_bundle_v25 | 532 | m25/m34 | bundle traceability |
| v35 attention audit/report | 120 | m35 | attention proposals/audits |
| v35H hyperedges | 120 | m35H | hyperedge events |
| v35H incidence | 855 | m35H | hyperedge-node incidence |
| v36.2 candidate paths | 120 | m362 | variational path scoring |
| v36.3 R bands | 90 | m363 | R pseudo-continuity candidates |
| v36.5 Xin carriers/readouts | 31/31 | m365 | carrier/readout pair |
| process_windows | 1633 | m366 process_window pass3 | materialized integration windows |
| process_window_members | 22128 | m366 process_window pass3 | window-member links |
| Pass12 stress rows | 3192 | m366_build_pass12_execution | offline stress projections |
| Pass13 replay stage rows | 5880 | m366_build_pass13_native_replay | native-shaped replay stage outputs |

### 6.2 Direct / inferred / proxy 边界
| edge/boundary | data | interpretation |
| --- | --- | --- |
| hypernode → spacetime backprojection | 855 rows | mostly materialized/proxy; raw full direct FK not universal |
| Pass7 normalized direct candidates | 390 / 855 | candidate upgrade, not raw direct fact |
| Pass6 conservative raw direct coverage | 0 / 855 | query surface kept conservative |
| Stage2 route | 532 intentional_bypass_to_toprxin | legitimate route in current architecture |
| external semantic readout | 31 readouts; 4 backwrite blocks | read-only; writes_mainline=0 |
| semantic attack stress | 532 / 532 boundary blocked in Pass12; 70 / 70 in Pass13 | boundary holds |

## 7. 压力与重放结果

### 7.1 Pass12 offline projection
| stress_name | trajectory_windows | P_to_R_projected | R/P_to_Xin_projected | stable_retained | boundary_blocked |
| --- | --- | --- | --- | --- | --- |
| coordinate jitter | 532 | 1 | 0 | 531 | 0 |
| support dropout | 532 | 23 | 0 | 509 | 0 |
| counter-evidence boost | 532 | 513 | 0 | 19 | 0 |
| Xin residual spike | 532 | 1 | 462 | 69 | 0 |
| masking failure | 532 | 450 | 67 | 15 | 0 |
| semantic backwrite attack | 532 | 0 | 0 | 0 | 532 |

### 7.2 Pass13 sample replay transitions
| scenario | transition_class | count | pct |
| --- | --- | --- | --- |
| baseline | stable_retained | 70 | 1.0 |
| coordinate_jitter | observe_retain_shift | 7 | 0.1 |
| coordinate_jitter | stable_retained | 63 | 0.9 |
| counter_boost | P_or_stable_to_R_focus | 66 | 0.942857 |
| counter_boost | stable_retained | 4 | 0.057143 |
| masking_failure | P_or_stable_to_R_focus | 24 | 0.342857 |
| masking_failure | observe_retain_shift | 13 | 0.185714 |
| masking_failure | stable_retained | 33 | 0.471429 |
| semantic_attack | semantic_backwrite_blocked | 70 | 1.0 |
| support_dropout | P_or_stable_to_R_focus | 1 | 0.014286 |
| support_dropout | observe_retain_shift | 13 | 0.185714 |
| support_dropout | stable_retained | 56 | 0.8 |
| xin_spike | R_or_P_to_Xin_escalation | 69 | 0.985714 |
| xin_spike | stable_retained | 1 | 0.014286 |

## 8. 缺口索引（数据视角）
| concept_id | version | concept | maturity | current_limit | next_action |
| --- | --- | --- | --- | --- | --- |
| empirical_stress_suite | future | perturbation/control stress suite for strong R/Xin/novelty | BLUEPRINT_ONLY | current dataset is stable/low-R/low-Xin |  |
| native_full_chain_runtime | future | native full-chain runtime skeleton | BLUEPRINT_ONLY | current run is materialized integration, not native synchronous runtime | design separate skeleton if required |
| native_hypergraph_db | future | native hypergraph database | BLUEPRINT_ONLY | v35H requires logical hypergraph index, not DB migration |  |
| online_life_runtime | future | online life-like runtime / synchronous external modules | BLUEPRINT_ONLY | not implemented and not required for current full-chain full-data materialization |  |
| true_pde_continuous_field | future | true continuous field / PDE solver / real nonlocal spacetime | BLUEPRINT_ONLY | blueprints require proxy/downgrade, not real PDE/nonlocal physics |  |
| full_external_xin_taxonomy | future | full external Xin taxonomy/capacity/PDE-ghost/leakage module | SCHEMA_ONLY | only 6 definitions and 31 readouts in current package | expand only as external readout module |
| full_chain_toprxin_profile | v36.6 materialized | T/O/P/R/Xin empirical profile | MATERIALIZED_INDEX |  |  |
| native_writer_contract | pass7 advisory | native writer contract / direct FK upgrade plan | MATERIALIZED_INDEX | should not be presented as v36.6 blueprint requirement |  |
| v34_1_meta_proxy | v34.1 | meta-proxy governance / runtime guard hardening | MATERIALIZED_INDEX | v34.1 appears as blueprint/partial hardening rather than separate full DB | do not overclaim as complete runtime hardening |
| v366_coordinate_nonlocal_audit | v36.6 | coordinate-nonlocal proxy audit | MATERIALIZED_INDEX |  |  |
| v366_external_module_sync | v36.6 pass9 | external module offline sync index | MATERIALIZED_INDEX |  |  |
| v366_hypernode_backprojection | v36.6 | hypernode spacetime backprojection | MATERIALIZED_INDEX | not full direct evidence linkage | keep directness label explicit |
| v366_ledger_binding | v36.6 | process_window ledger binding | MATERIALIZED_INDEX |  |  |
| v366_measure_binding | v36.6 | coordinate-hidden measure binding | MATERIALIZED_INDEX |  |  |
| v366_process_hyperedge_relation | v36.6 | process/hyperedge spacetime relation | MATERIALIZED_INDEX |  |  |
| v366_process_members | v36.6 | process_window members | MATERIALIZED_INDEX |  |  |
| v366_process_window | v36.6 | process_window registry | MATERIALIZED_INDEX | not yet native writer output for all modules | future native full-chain skeleton |
| v366_run_plan | v36.6 pass9 | full-chain execution plan | MATERIALIZED_INDEX |  |  |
| v366_upper_empirical | v36.6 empirical | upper-layer empirical analysis | MATERIALIZED_INDEX |  |  |
| information_fiber | legacy-v25 | information fiber | DATA_POPULATED |  |  |
| masking_layer | v25/v35/pass2 | masking / counter-evidence shielding layer | DATA_POPULATED | coverage is not one concrete mask object per R-chain | add concrete mask object when needed |
| physical_stage1 | legacy-v25 | Stage 1 physical/source substrate | DATA_POPULATED | not full 3D electromechanical live sphere in current run | separate external 2D source route from full electromechanical route |
| preneural_interface | v0.2-v25/pass3 | preneural interface bundle | DATA_POPULATED | not every current process_window is originally written by preneural writer | keep as optional interface trace, not external module |
| src_envelope | v25/v36.5 | external/source input envelope | DATA_POPULATED | offline source/envelope, not live runtime sensorium | add native run_id for future full-chain skeleton |
| stage2_object_surface | legacy-v25/pass8 | Stage 2 object surface / early-neural simulation layer | DATA_POPULATED | legitimate bypass in current architecture; not mandatory route | report route status rather than treating bypass as failure |
| storage_ledger_split | v1.0-v36.6 | SQLite ledger/index + runtime_store payload split | DATA_POPULATED |  |  |
| v35h_appeal_gc | v35H | hyperedge appeal and GC governance | DATA_POPULATED |  |  |
| external_entropy_ledger | v34 | external entropy / equivalent energy ledger | NATIVE_RUN_GENERATED | ledger energy is proxy, not joule/physical energy |  |
| noether_audit | v34 | Noether-style balance audit | NATIVE_RUN_GENERATED | not proof of physical law |  |
| o_candidate | v25 | O candidate support | NATIVE_RUN_GENERATED | small legacy O surface count; current O refs often v25-derived |  |
| v35_attention | v35 | attention proposal/path integral governance | NATIVE_RUN_GENERATED | attention is not action authorization |  |
| v35h_hyperedge | v35H | hyperedge incidence sidecar | NATIVE_RUN_GENERATED | logical hypergraph sidecar, not primary hypergraph DB |  |
| v361_variational_measure | v36.1 | variational external ledger measure | NATIVE_RUN_GENERATED | not real physical action |  |
| v362_action_revision | v36.2 | S_IE_proxy action revision and Xin_var | NATIVE_RUN_GENERATED | minimum action score != truth |  |
| v363_r_band | v36.3 | R spacetime band / pseudo-continuity | NATIVE_RUN_GENERATED | pseudo-continuity only, not true continuous manifold |  |
| v365_external_readout | v36.5 | external Xin definition and readout-only module | NATIVE_RUN_GENERATED | minimal external module, not full taxonomy |  |
| v36_curvature_proxy | v36 | curvature / singularity / heat-bath proxy | NATIVE_RUN_GENERATED | not Ricci curvature |  |
| v36_dissipative_source | v36 | steady dissipative source registry | NATIVE_RUN_GENERATED | not physical heat source |  |
| v36_metric_proxy | v36 | information-energy metric proxy | NATIVE_RUN_GENERATED | not physical metric |  |

## 9. 建议给其他 AI 的检查顺序（数据优先）

1. 先读 `morphosphere_data_only_review_for_ai.md` 的第 1–4 节。
2. 再查 `m25.db` / `m34.db` 的 `information_point_v25`, `coordinate_transform_trace_v25`, `trajectory_window_trace_v25`, `p_spacetime_measure_v25`, `r_counter_measure_v25`, `xi_residual_surface_v25`, `decision_evidence_bundle_v25`。
3. 查 `m35.db` 的 `v35_attention_performance_report`, `v35_r_counter_chain`, `v35_masking_proposal`。
4. 查 `m35H.db` 的 hyperedge/incidence 表，确认平均 arity 与 node roles。
5. 查 `m362.db` 的 action score / stationarity defect / Xin_var 表。
6. 查 `m366_upper_layer_empirical.db` 的 `empirical_full_chain_backtrace_sample`, `empirical_role_transition_counts`, `empirical_metric_distribution`。
7. 查 `m366_build_pass12_execution.db` 与 `m366_build_pass13_native_replay.db` 的 stress/replay 输出。

## 10. 最少可复核 SQL

```sql
-- v25 source-to-trajectory core counts
SELECT COUNT(*) FROM information_point_v25;
SELECT COUNT(*) FROM coordinate_transform_trace_v25;
SELECT COUNT(*) FROM trajectory_window_trace_v25;
SELECT COUNT(*) FROM p_spacetime_measure_v25;
SELECT COUNT(*) FROM r_counter_measure_v25;
SELECT COUNT(*) FROM xi_residual_surface_v25;

-- v35 attention verdicts
SELECT verdict, COUNT(*) FROM v35_attention_performance_report GROUP BY verdict;

-- v35H hyperedge arity
SELECT hyperedge_id, COUNT(*) AS arity FROM v35h_hyperedge_incidence GROUP BY hyperedge_id ORDER BY arity DESC LIMIT 10;

-- v36.6 process windows
SELECT COUNT(*) FROM v366_process_window_registry;
SELECT COUNT(*) FROM v366_process_window_member;

-- Pass13 transitions
SELECT scenario_id, transition_class, count, pct FROM pass13_state_transition_summary;
```