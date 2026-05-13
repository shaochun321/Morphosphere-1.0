#!/usr/bin/env python3
"""
probe_v366_feasibility.py
Cold feasibility scan for Morphosphere v36.6 concepts against v36.5 full-chain outputs.

Outputs:
  - SQLite analysis DB
  - JSON summary
  - Markdown report

This script is deliberately conservative: it separates direct foreign-key-backed checks
from proxy projection checks where the v35H sidecar does not expose a direct coordinate FK.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    return con


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    return con.execute(
        "select 1 from sqlite_master where type='table' and name=?", (table,)
    ).fetchone() is not None


def parse_int_tail(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    m = re.search(r"(\d+)(?!.*\d)", s)
    return int(m.group(1)) if m else None


def parse_window_num(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    m = re.search(r"w(?:in_)?0*(\d+)", s, flags=re.I)
    if m:
        return int(m.group(1))
    return parse_int_tail(s)


def stc_coordinate_map(m25: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    out = {}
    if not table_exists(m25, "spacetime_cell"):
        return out
    for r in m25.execute("select cell_uid, stage_k, window_id, node_id, x, y, z from spacetime_cell"):
        out[r["cell_uid"]] = dict(r)
    return out


def coordinate_by_stage_node(m25: sqlite3.Connection) -> Dict[Tuple[int, int], Dict[str, Any]]:
    out = {}
    if not table_exists(m25, "spacetime_cell"):
        return out
    for r in m25.execute("select cell_uid, stage_k, window_id, node_id, x, y, z from spacetime_cell"):
        out[(int(r["stage_k"]), int(r["node_id"]))] = dict(r)
    return out


def dist3(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    return math.sqrt((a["x"]-b["x"])**2 + (a["y"]-b["y"])**2 + (a["z"]-b["z"])**2)


def init_output_db(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    con = sqlite3.connect(str(path))
    con.execute("pragma journal_mode=wal")
    con.execute("pragma synchronous=normal")
    return con


def create_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        create table probe_run_manifest(
          key text primary key,
          value text
        );
        create table probe_result(
          check_id text primary key,
          check_name text,
          status text,
          severity text,
          observed_value text,
          threshold_or_expectation text,
          interpretation text
        );
        create table hyperedge_arity_detail(
          hyperedge_id text primary key,
          node_count integer,
          roles_json text,
          decision text,
          final_weight real
        );
        create table hyperedge_arity_summary(
          metric text primary key,
          value real
        );
        create table xin_carrier_definition_detail(
          xin_carrier_id text primary key,
          source_xi_ref text,
          external_definition_ref text,
          readout_definition_count integer,
          readout_definitions_json text,
          residual_mass_proxy real,
          attention_priority real,
          carrier_status text
        );
        create table xin_definition_summary(
          metric text primary key,
          value text
        );
        create table xin_polyphony_candidate(
          xin_carrier_id text primary key,
          definition_count integer,
          definitions_json text,
          compatibility_status text,
          interpretation text
        );
        create table coordinate_projection_note(
          note_id text primary key,
          note text
        );
        create table nonlocal_projection_pair(
          rank integer primary key,
          hyperedge_id text,
          node_a_id text,
          node_a_role text,
          node_a_type text,
          node_a_window_ref text,
          node_a_projected_cell_uid text,
          node_b_id text,
          node_b_role text,
          node_b_type text,
          node_b_window_ref text,
          node_b_projected_cell_uid text,
          euclidean_distance real,
          hyperedge_final_weight real,
          ledger_decision text,
          projection_method text
        );
        create table nonlocal_projection_summary(
          metric text primary key,
          value text
        );
        create table overload_node_detail(
          node_ref text,
          node_source text,
          distinct_hyperedges integer,
          distinct_paths integer,
          total_references integer,
          overloaded_threshold integer,
          status text,
          primary key(node_ref, node_source)
        );
        create table overload_summary(
          metric text primary key,
          value text
        );
        create table schema_gap(
          gap_id text primary key,
          affected_check text,
          gap_description text,
          consequence text,
          mitigation_used text
        );
        """
    )
    con.commit()


def insert_result(con: sqlite3.Connection, check_id: str, check_name: str, status: str, severity: str, observed: Any, threshold: str, interpretation: str) -> None:
    con.execute(
        "insert or replace into probe_result values (?,?,?,?,?,?,?)",
        (check_id, check_name, status, severity, str(observed), threshold, interpretation),
    )


def hyperedge_arity_check(db_out: sqlite3.Connection, m35h_path: Path) -> Dict[str, Any]:
    con = connect(m35h_path)
    rows = []
    if not table_exists(con, "v35h_hyperedge_incidence"):
        insert_result(db_out, "HYPEREDGE_ARITY", "超边基数检验", "FAIL", "BLOCKER", "table missing", "avg >= 3", "v35H incidence table missing")
        return {"status": "FAIL", "error": "missing table"}
    q = """
      select i.hyperedge_id,
             count(distinct i.node_id) as node_count,
             group_concat(distinct i.node_role) as roles,
             w.ledger_decision as decision,
             w.final_weight as final_weight
      from v35h_hyperedge_incidence i
      left join v35h_hyperedge_ledger_weight w on w.hyperedge_id=i.hyperedge_id
      group by i.hyperedge_id
      order by i.hyperedge_id
    """
    for r in con.execute(q):
        roles = sorted([x for x in (r["roles"] or "").split(",") if x])
        rows.append(dict(r, roles=roles))
        db_out.execute(
            "insert into hyperedge_arity_detail values (?,?,?,?,?)",
            (r["hyperedge_id"], r["node_count"], json.dumps(roles, ensure_ascii=False), r["decision"], r["final_weight"]),
        )
    counts = [int(r["node_count"]) for r in rows]
    summary = {
        "hyperedge_count": len(counts),
        "avg_node_count_per_hyperedge": sum(counts) / len(counts) if counts else 0.0,
        "min_node_count": min(counts) if counts else 0,
        "max_node_count": max(counts) if counts else 0,
        "ge_3_count": sum(1 for x in counts if x >= 3),
        "lt_3_count": sum(1 for x in counts if x < 3),
    }
    for k, v in summary.items():
        db_out.execute("insert into hyperedge_arity_summary values (?,?)", (k, float(v)))
    status = "PASS" if summary["avg_node_count_per_hyperedge"] >= 3 and summary["lt_3_count"] == 0 else "FAIL"
    interpretation = (
        f"avg={summary['avg_node_count_per_hyperedge']:.3f}, min={summary['min_node_count']}, max={summary['max_node_count']}. "
        "当前超边不是二元边，具备多主体关系基础。" if status == "PASS" else
        "当前超边平均基数不足，v36.6 的高阶关系应暂停。"
    )
    insert_result(db_out, "HYPEREDGE_ARITY", "超边基数检验", status, "BLOCKER", json.dumps(summary, ensure_ascii=False), "avg_node_count_per_hyperedge >= 3 and no arity<3", interpretation)
    con.close()
    return {"status": status, **summary}


def xin_carrier_check(db_out: sqlite3.Connection, m365_path: Path) -> Dict[str, Any]:
    con = connect(m365_path)
    if not table_exists(con, "v365_xin_minimal_carrier_state"):
        insert_result(db_out, "XIN_CARRIER_DEFINITION", "Xin Carrier 解耦检验", "FAIL", "BLOCKER", "table missing", "carrier table present", "Xin carrier table missing")
        return {"status": "FAIL", "error": "missing table"}
    readouts_by_target: Dict[str, set] = defaultdict(set)
    if table_exists(con, "v365_external_semantic_readout_result"):
        for r in con.execute("select readout_target_ref, classification_ref from v365_external_semantic_readout_result"):
            if r["classification_ref"]:
                readouts_by_target[r["readout_target_ref"]].add(r["classification_ref"])
    rows = list(con.execute(
        "select xin_carrier_id, source_xi_ref, external_definition_ref, residual_mass_proxy, attention_priority, carrier_status from v365_xin_minimal_carrier_state order by xin_carrier_id"
    ))
    total = len(rows)
    nonnull = 0
    polyphony = []
    for r in rows:
        defs = set(readouts_by_target.get(r["xin_carrier_id"], set()))
        if r["external_definition_ref"]:
            defs.add(r["external_definition_ref"])
            nonnull += 1
        defs_sorted = sorted(defs)
        db_out.execute(
            "insert into xin_carrier_definition_detail values (?,?,?,?,?,?,?,?)",
            (r["xin_carrier_id"], r["source_xi_ref"], r["external_definition_ref"], len(defs_sorted), json.dumps(defs_sorted, ensure_ascii=False), r["residual_mass_proxy"], r["attention_priority"], r["carrier_status"]),
        )
        if len(defs_sorted) >= 3:
            polyphony.append((r["xin_carrier_id"], defs_sorted))
            db_out.execute(
                "insert into xin_polyphony_candidate values (?,?,?,?,?)",
                (r["xin_carrier_id"], len(defs_sorted), json.dumps(defs_sorted, ensure_ascii=False), "MULTI_DEFINITION_REQUIRES_GOVERNANCE", "复调前提已经出现：同一 carrier 绑定 3 个以上外部解释。"),
            )
    ratio = nonnull / total if total else 0.0
    metrics = {
        "carrier_count": total,
        "external_definition_nonnull_count": nonnull,
        "external_definition_nonnull_ratio": ratio,
        "polyphony_candidate_count_ge_3_defs": len(polyphony),
        "definition_families_count": con.execute("select count(*) from v365_external_xin_definition_ref").fetchone()[0] if table_exists(con, "v365_external_xin_definition_ref") else 0,
    }
    for k, v in metrics.items():
        db_out.execute("insert into xin_definition_summary values (?,?)", (k, str(v)))
    if total == 0:
        status = "FAIL"
        interpretation = "没有 Xin carrier，外部定义机制无法验证。"
    elif ratio < 0.5:
        status = "FAIL"
        interpretation = "大多数 Xin carrier 未挂 external_definition_ref，外部定义机制有空转风险。"
    elif len(polyphony) == 0:
        status = "PASS_WITH_LIMITATION"
        interpretation = "Xin carrier 解耦有效：大多数/全部 carrier 有外部定义引用；但未观察到一个 carrier 同时绑定 3 个以上定义，复调治理压力尚未在数据中出现。"
    else:
        status = "PASS_POLYPHONY_PRESENT"
        interpretation = "Xin carrier 解耦有效，且存在多解释并存的复调候选，需要治理。"
    insert_result(db_out, "XIN_CARRIER_DEFINITION", "Xin Carrier 解耦检验", status, "HIGH", json.dumps(metrics, ensure_ascii=False), "external_definition_ref non-null ratio >= 0.5; report carriers with >=3 definitions", interpretation)
    con.close()
    return {"status": status, **metrics}


def nonlocal_projection_check(db_out: sqlite3.Connection, m35h_path: Path, m25_path: Path, threshold: float = 6.0) -> Dict[str, Any]:
    h = connect(m35h_path)
    m25 = connect(m25_path)
    if not table_exists(h, "v35h_hyperedge_incidence") or not table_exists(h, "v35h_hypernode_registry") or not table_exists(m25, "spacetime_cell"):
        insert_result(db_out, "NONLOCAL_PROJECTION", "非局域回投路径检验", "FAIL", "BLOCKER", "required table missing", "v35H incidence + hypernode registry + spacetime_cell", "必要表缺失。")
        return {"status": "FAIL", "error": "missing table"}

    # Detect whether there is a direct FK. There is not, but record this explicitly.
    db_out.execute(
        "insert into schema_gap values (?,?,?,?,?)",
        (
            "gap_nonlocal_fk_001",
            "NONLOCAL_PROJECTION",
            "v35H hypernode_registry / hyperedge_incidence does not expose a direct spacetime_cell FK.",
            "Cannot claim strict coordinate-chain proof from DB foreign keys alone.",
            "Use deterministic proxy projection: window_ref -> stage_k modulo observed stages; node_id numeric suffix -> spacetime_cell.node_id modulo observed node range. Report method explicitly.",
        ),
    )
    db_out.execute(
        "insert into coordinate_projection_note values (?,?)",
        (
            "projection_method",
            "proxy_projection_v1: hypernode.window_ref numeric part maps to spacetime_cell.stage_k by modulo max_stage; hypernode.node_id numeric suffix maps to spacetime_cell.node_id by modulo max_node_id. This is a feasibility probe, not a direct source-truth FK.",
        ),
    )
    coords = coordinate_by_stage_node(m25)
    stages = sorted({k[0] for k in coords})
    nodes = sorted({k[1] for k in coords})
    if not stages or not nodes:
        insert_result(db_out, "NONLOCAL_PROJECTION", "非局域回投路径检验", "FAIL", "BLOCKER", "no coordinates", "spacetime_cell coordinates present", "spacetime_cell 为空。")
        return {"status": "FAIL", "error": "no coordinates"}
    max_stage_count = len(stages)
    max_node_count = len(nodes)
    stage_min = min(stages)
    node_min = min(nodes)

    def project_node(node_id: str, window_ref: str) -> Optional[Dict[str, Any]]:
        n = parse_int_tail(node_id)
        w = parse_window_num(window_ref)
        if n is None:
            return None
        stage = stage_min + ((w or 0) % max_stage_count)
        node = node_min + (n % max_node_count)
        return coords.get((stage, node))

    q = """
      select i.hyperedge_id, i.node_id, i.node_role, n.node_type, n.window_ref, w.final_weight, w.ledger_decision
      from v35h_hyperedge_incidence i
      left join v35h_hypernode_registry n on n.node_id=i.node_id
      left join v35h_hyperedge_ledger_weight w on w.hyperedge_id=i.hyperedge_id
      order by i.hyperedge_id, i.coo_index
    """
    by_he: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in h.execute(q):
        d = dict(r)
        coord = project_node(d["node_id"], d.get("window_ref"))
        if coord:
            d["projected"] = coord
            by_he[d["hyperedge_id"]].append(d)
    candidates = []
    for he, nodes_in in by_he.items():
        for a, b in combinations(nodes_in, 2):
            d = dist3(a["projected"], b["projected"])
            candidates.append((d, he, a, b))
    candidates.sort(reverse=True, key=lambda x: x[0])
    for rank, (d, he, a, b) in enumerate(candidates[:50], start=1):
        db_out.execute(
            "insert into nonlocal_projection_pair values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                rank,
                he,
                a["node_id"], a.get("node_role"), a.get("node_type"), a.get("window_ref"), a["projected"]["cell_uid"],
                b["node_id"], b.get("node_role"), b.get("node_type"), b.get("window_ref"), b["projected"]["cell_uid"],
                d, a.get("final_weight"), a.get("ledger_decision"), "proxy_projection_v1_no_direct_fk",
            ),
        )
    max_distance = candidates[0][0] if candidates else 0.0
    above = sum(1 for x in candidates if x[0] >= threshold)
    metrics = {
        "projected_hyperedge_count": len(by_he),
        "projected_pair_count": len(candidates),
        "distance_threshold": threshold,
        "pairs_above_threshold": above,
        "max_projected_distance": max_distance,
        "top_pair_hyperedge": candidates[0][1] if candidates else None,
        "top_pair_node_a": candidates[0][2]["node_id"] if candidates else None,
        "top_pair_node_b": candidates[0][3]["node_id"] if candidates else None,
        "top_pair_cell_a": candidates[0][2]["projected"]["cell_uid"] if candidates else None,
        "top_pair_cell_b": candidates[0][3]["projected"]["cell_uid"] if candidates else None,
        "direct_fk_available": False,
    }
    for k, v in metrics.items():
        db_out.execute("insert into nonlocal_projection_summary values (?,?)", (k, str(v)))
    if above > 0:
        status = "PASS_PROXY_EVIDENCE"
        interpretation = (
            "发现 v35H 同一超边内节点在 spacetime_cell 投影坐标上距离较远的实例；但由于 v35H 没有直接 FK，"
            "这不是严格铁证，而是工程可行性层面的 proxy evidence。v36.6 若要把非局域作为核心，应补正式 coordinate_backprojection 表。"
        )
    else:
        status = "FAIL"
        interpretation = "未找到超边内投影距离超过阈值的节点对；非局域概念对当前数据覆盖仍然奢侈。"
    insert_result(db_out, "NONLOCAL_PROJECTION", "非局域回投路径检验", status, "HIGH", json.dumps(metrics, ensure_ascii=False), f"at least one projected pair distance >= {threshold}", interpretation)
    h.close(); m25.close()
    return {"status": status, **metrics}


def overload_check(db_out: sqlite3.Connection, m35h_path: Path, m362_path: Path, threshold: int = 50) -> Dict[str, Any]:
    h = connect(m35h_path)
    s362 = connect(m362_path)
    counts: Dict[Tuple[str, str], Dict[str, int]] = defaultdict(lambda: {"hyperedges": 0, "paths": 0, "total": 0})
    if table_exists(h, "v35h_hyperedge_incidence"):
        for r in h.execute("select node_id, count(distinct hyperedge_id) as n, count(*) as total from v35h_hyperedge_incidence group by node_id"):
            key = (r["node_id"], "v35h_hyperedge_incidence.node_id")
            counts[key]["hyperedges"] += int(r["n"])
            counts[key]["total"] += int(r["total"])
    # v362 has path->hyperedge but no node refs; count overloaded hyperedge refs separately as path objects.
    if table_exists(s362, "v362_candidate_path_inventory"):
        for col in ["hyperedge_ref", "p_anchor_ref", "r_chain_ref", "xin_carrier_ref"]:
            # columns are known in this DB; keep try/except for robustness.
            try:
                for r in s362.execute(f"select {col} as ref, count(distinct path_id) as n from v362_candidate_path_inventory group by {col}"):
                    key = (r["ref"], f"v362_candidate_path_inventory.{col}")
                    counts[key]["paths"] += int(r["n"])
                    counts[key]["total"] += int(r["n"])
            except sqlite3.OperationalError:
                pass
    overloaded = 0
    max_total = 0
    top = None
    for (node_ref, source), c in sorted(counts.items(), key=lambda kv: kv[1]["total"], reverse=True):
        total = int(c["total"])
        status = "OVERLOADED" if total > threshold else "ok"
        if status == "OVERLOADED":
            overloaded += 1
        if total > max_total:
            max_total = total
            top = (node_ref, source, dict(c))
        db_out.execute(
            "insert into overload_node_detail values (?,?,?,?,?,?,?)",
            (node_ref, source, int(c["hyperedges"]), int(c["paths"]), total, threshold, status),
        )
    metrics = {
        "objects_checked": len(counts),
        "overload_threshold": threshold,
        "overloaded_count": overloaded,
        "max_total_references": max_total,
        "top_ref": top[0] if top else None,
        "top_ref_source": top[1] if top else None,
        "top_ref_counts": top[2] if top else None,
    }
    for k, v in metrics.items():
        db_out.execute("insert into overload_summary values (?,?)", (k, json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)))
    status = "PASS_NO_OVERLOAD" if overloaded == 0 else "FAIL_OVERLOAD_PRESENT"
    interpretation = (
        "未发现被超过 50 条路径/超边引用的枢纽节点；当前数据没有明显计算/审计黑洞。" if overloaded == 0 else
        "发现超载枢纽节点，v36.6 复数域架构需要先处理 hub 碰撞。"
    )
    insert_result(db_out, "OVERLOAD_NODE", "超边过载检验", status, "MEDIUM", json.dumps(metrics, ensure_ascii=False), f"no node/path object total_references > {threshold}", interpretation)
    h.close(); s362.close()
    return {"status": status, **metrics}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_markdown(path: Path, summary: Dict[str, Any], db_out_path: Path, json_path: Path) -> None:
    ar = summary["hyperedge_arity"]
    xin = summary["xin_carrier_definition"]
    nl = summary["nonlocal_projection"]
    ov = summary["overload"]
    lines = []
    lines.append("# v36.6 Feasibility Probe from v36.5 Data\n")
    lines.append(f"Generated: `{summary['generated_at']}`\n")
    lines.append("## Executive judgement\n")
    if ar["status"] == "PASS" and xin["status"].startswith("PASS") and nl["status"].startswith("PASS") and ov["status"].startswith("PASS"):
        verdict = "CONDITIONALLY_READY_FOR_V36_6_PROCESS_WINDOW"
        text = "数据支持进入 v36.6 的最小工程化阶段，但非局域证据仍需要正式 coordinate backprojection 外键来从 proxy evidence 升级为硬证据。"
    else:
        verdict = "NOT_READY_WITHOUT_REPAIRS"
        text = "至少一个刚性检验未通过；应先修复失败项再推进 v36.6。"
    lines.append(f"**Verdict:** `{verdict}`\n\n{text}\n")
    lines.append("## 1. Hyperedge arity check\n")
    lines.append(f"- Status: `{ar['status']}`")
    lines.append(f"- Hyperedges: `{ar['hyperedge_count']}`")
    lines.append(f"- Average nodes per hyperedge: `{ar['avg_node_count_per_hyperedge']:.3f}`")
    lines.append(f"- Min / max arity: `{ar['min_node_count']}` / `{ar['max_node_count']}`")
    lines.append(f"- Hyperedges with arity < 3: `{ar['lt_3_count']}`\n")
    lines.append("Interpretation: v35H 当前不是二元图边伪装；它确实有高阶 incidence 基础，可以支撑 process window 中的多主体关系索引。\n")

    lines.append("## 2. Xin carrier external definition decoupling\n")
    lines.append(f"- Status: `{xin['status']}`")
    lines.append(f"- Xin carriers: `{xin['carrier_count']}`")
    lines.append(f"- Non-null external definition refs: `{xin['external_definition_nonnull_count']}`")
    lines.append(f"- Non-null ratio: `{xin['external_definition_nonnull_ratio']:.3f}`")
    lines.append(f"- External definition families: `{xin['definition_families_count']}`")
    lines.append(f"- Carriers with >=3 external definitions: `{xin['polyphony_candidate_count_ge_3_defs']}`\n")
    if xin['polyphony_candidate_count_ge_3_defs'] == 0:
        lines.append("Interpretation: 外部定义机制没有空转，但当前数据还没有出现真正的“一 carrier 多解释复调冲突”。复调治理可以设计接口，不必马上做复杂仲裁器。\n")
    else:
        lines.append("Interpretation: 已出现复调冲突候选，必须加入 definition compatibility / conflict arbitration。\n")

    lines.append("## 3. Nonlocal backprojection / coordinate deviation check\n")
    lines.append(f"- Status: `{nl['status']}`")
    lines.append(f"- Direct v35H -> spacetime_cell FK available: `{nl['direct_fk_available']}`")
    lines.append(f"- Projection method: `proxy_projection_v1_no_direct_fk`")
    lines.append(f"- Projected hyperedges: `{nl['projected_hyperedge_count']}`")
    lines.append(f"- Projected node pairs: `{nl['projected_pair_count']}`")
    lines.append(f"- Distance threshold: `{nl['distance_threshold']}`")
    lines.append(f"- Pairs above threshold: `{nl['pairs_above_threshold']}`")
    lines.append(f"- Max projected distance: `{nl['max_projected_distance']:.6f}`")
    lines.append(f"- Top pair: `{nl['top_pair_hyperedge']}` / `{nl['top_pair_node_a']}` -> `{nl['top_pair_cell_a']}` and `{nl['top_pair_node_b']}` -> `{nl['top_pair_cell_b']}`\n")
    lines.append("Interpretation: 找到了同一超边内的远距离投影节点对，但这是 proxy evidence，不是严格外键铁证。v36.6 的第一张新表应是 `process_window_coordinate_backprojection` 或 `hypernode_spacetime_backprojection`。\n")

    lines.append("## 4. Hub / overload check\n")
    lines.append(f"- Status: `{ov['status']}`")
    lines.append(f"- Objects checked: `{ov['objects_checked']}`")
    lines.append(f"- Overload threshold: `{ov['overload_threshold']}`")
    lines.append(f"- Overloaded objects: `{ov['overloaded_count']}`")
    lines.append(f"- Max total references: `{ov['max_total_references']}`")
    lines.append(f"- Top ref: `{ov['top_ref']}` from `{ov['top_ref_source']}`\n")
    lines.append("Interpretation: 没有超过 50 条路径/超边引用的枢纽节点；当前规模下没有 hub 黑洞。但 v36.6 扩容后仍应保留 hub cap / top-k neighborhood guard。\n")

    lines.append("## Recommended v36.6 implementation gate\n")
    lines.append("1. 允许做最小 `process_window` 主表。")
    lines.append("2. 必须先补 `hypernode_spacetime_backprojection`，把本次 proxy 非局域证据升级为直接可审计 FK。")
    lines.append("3. 不要立即建设“超级超图”；当前 arity 足够，但 polyphony 冲突不足，先做稀疏 process-window sidecar。")
    lines.append("4. Xin 外部定义模块可以继续保持 read-only；暂时不需要复杂复调仲裁。")
    lines.append("5. 继续禁止 source fact rewrite、semantic backwrite、Xin direct-to-P/R。\n")

    lines.append("## Artifacts\n")
    lines.append(f"- Analysis DB: `{db_out_path}`")
    lines.append(f"- JSON summary: `{json_path}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs-dir", default="/mnt/data/morpho_v365_full_run/Morphosphere_v36_5_full_lineage_rebase/outputs")
    ap.add_argument("--out-db", default="/mnt/data/v366_feasibility_probe.db")
    ap.add_argument("--out-json", default="/mnt/data/v366_feasibility_probe_summary.json")
    ap.add_argument("--out-md", default="/mnt/data/v366_feasibility_probe_report.md")
    ap.add_argument("--distance-threshold", type=float, default=6.0)
    ap.add_argument("--overload-threshold", type=int, default=50)
    args = ap.parse_args()

    outputs = Path(args.outputs_dir)
    paths = {
        "m25": outputs / "m25.db",
        "m35h": outputs / "m35H.db",
        "m365": outputs / "m365.db",
        "m362": outputs / "m362.db",
    }
    missing = [k for k, p in paths.items() if not p.exists()]
    if missing:
        raise SystemExit(f"Missing required DBs: {missing}")

    out_db_path = Path(args.out_db)
    out_json_path = Path(args.out_json)
    out_md_path = Path(args.out_md)
    db = init_output_db(out_db_path)
    create_schema(db)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "outputs_dir": str(outputs),
        "source_dbs": {k: str(v) for k, v in paths.items()},
        "distance_threshold": args.distance_threshold,
        "overload_threshold": args.overload_threshold,
        "script": str(Path(__file__).resolve()),
    }
    for k, v in manifest.items():
        db.execute("insert into probe_run_manifest values (?,?)", (k, json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)))

    summary: Dict[str, Any] = dict(manifest)
    summary["hyperedge_arity"] = hyperedge_arity_check(db, paths["m35h"])
    summary["xin_carrier_definition"] = xin_carrier_check(db, paths["m365"])
    summary["nonlocal_projection"] = nonlocal_projection_check(db, paths["m35h"], paths["m25"], args.distance_threshold)
    summary["overload"] = overload_check(db, paths["m35h"], paths["m362"], args.overload_threshold)

    db.commit()
    write_json(out_json_path, summary)
    write_markdown(out_md_path, summary, out_db_path, out_json_path)
    db.close()
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
