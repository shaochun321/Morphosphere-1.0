"""V8.5 diagnostic table to mainline concept crosswalk.

The crosswalk prevents diagnostic SPMS rows from being silently interpreted as
mainline source-of-truth objects.  It is deliberately descriptive and
side-effect free so it can be imported by runners, migrations, reports, and
acceptance tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MainlineCrosswalkEntry:
    """Interpretation row for one V8.5 diagnostic table."""

    diagnostic_table: str
    prior_mainline_concept: str
    semantic_role: str
    allowed_use: str
    forbidden_use: str
    source_of_truth: str
    intentionally_empty_when: str = ""

    def to_row(self) -> dict[str, str]:
        return {
            "diagnostic_table": self.diagnostic_table,
            "prior_mainline_concept": self.prior_mainline_concept,
            "semantic_role": self.semantic_role,
            "allowed_use": self.allowed_use,
            "forbidden_use": self.forbidden_use,
            "source_of_truth": self.source_of_truth,
            "intentionally_empty_when": self.intentionally_empty_when,
        }


V85_TO_MAINLINE_CROSSWALK: tuple[MainlineCrosswalkEntry, ...] = (
    MainlineCrosswalkEntry(
        diagnostic_table="run_manifest",
        prior_mainline_concept="run identity and calibration contract",
        semantic_role="source",
        allowed_use="Fix diagnostic run identity, schema/rules version, execution mode, and count semantics.",
        forbidden_use="Do not infer scientific validity or biology readiness from run identity alone.",
        source_of_truth="contracts.RunManifest plus run_manifest table",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="spacetime_cell",
        prior_mainline_concept="preneural_geometry / pointset view",
        semantic_role="derived",
        allowed_use="Runtime diagnostic coordinate record for a cell-like carrier at one window/stage.",
        forbidden_use="Do not treat as a physical cell source-of-truth or replace PhysicalCellGraphState.",
        source_of_truth="derived from PreNeuralCarrierSlice / PreNeuralPointSetSlice",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="information_fiber",
        prior_mainline_concept="preneural_signal_window view",
        semantic_role="derived",
        allowed_use="Runtime diagnostic signal-window record attached to a spacetime carrier.",
        forbidden_use="Do not treat as raw electrophysiology or final biological spike evidence.",
        source_of_truth="derived from SignalWindow / diagnostic dynamic driver",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="spacetime_fiber_binding",
        prior_mainline_concept="carrier-to-signal co-generation binding",
        semantic_role="derived",
        allowed_use="Audit inseparability of spacetime carrier and signal fiber in diagnostic runs.",
        forbidden_use="Do not interpret binding as proof of object formation.",
        source_of_truth="derived from spacetime_cell and information_fiber rows",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="transport_current_edge",
        prior_mainline_concept="transport process view, not necessarily transport_operator",
        semantic_role="derived",
        allowed_use="Diagnostic transport-current evidence between carrier rows.",
        forbidden_use="Do not claim true transport realism while weights/gating/costs remain proxy or trivial.",
        source_of_truth="derived from preneural transport builder and SPMS populator",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="object_hypothesis",
        prior_mainline_concept="P/R candidate view, not final p_band/r_band",
        semantic_role="derived",
        allowed_use="Diagnostic candidate object/hypothesis row from decomposition and occupancy support.",
        forbidden_use="Do not treat as certified object, frozen P band, or scientific conclusion.",
        source_of_truth="derived from PR decomposition and SPMS hypothesis population",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="o_candidate_record",
        prior_mainline_concept="O candidate surface",
        semantic_role="proxy_or_derived",
        allowed_use="Track O lineage candidate records and formation mode where available.",
        forbidden_use="Do not claim O formation when formation_mode is pass_through_proxy.",
        source_of_truth="stage2 object surface / diagnostic runner",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="t_surface",
        prior_mainline_concept="legacy/mainline T surface",
        semantic_role="derived_or_intentionally_empty",
        allowed_use="Use when populated with slice and transport references; otherwise consult crosswalk.",
        forbidden_use="Do not fail a SPMS-only diagnostic run solely because legacy T rows are intentionally empty.",
        source_of_truth="stage2 object surface when populated",
        intentionally_empty_when="SPMS-layer diagnostic run does not materialize legacy T surface rows.",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="p_band_record",
        prior_mainline_concept="legacy/mainline primary band",
        semantic_role="derived_or_intentionally_empty",
        allowed_use="Use only when populated by mainline freezer with origin anchors.",
        forbidden_use="Do not replace object_hypothesis or treat empty rows as failed SPMS diagnostic formation.",
        source_of_truth="stage2 freezer when populated",
        intentionally_empty_when="Diagnostic run reports P/R candidates through object_hypothesis instead of frozen bands.",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="r_band_record",
        prior_mainline_concept="legacy/mainline residual band",
        semantic_role="derived_or_intentionally_empty",
        allowed_use="Use only when populated by mainline freezer with residual anchors.",
        forbidden_use="Do not infer no residual pressure solely from empty legacy R band rows.",
        source_of_truth="stage2 freezer when populated",
        intentionally_empty_when="Diagnostic run reports residual pressure through Xi/residue tables instead of frozen bands.",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="xi_residue_record",
        prior_mainline_concept="residual evidence / Xi residue pool",
        semantic_role="derived",
        allowed_use="Audit unresolved residual pressure and support domains in diagnostic runs.",
        forbidden_use="Do not treat Xi rows as final refutation or final object discovery.",
        source_of_truth="Xi residue evaluator / decomposition residual",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="relation_entropy_record",
        prior_mainline_concept="relation entropy diagnostic ledger",
        semantic_role="report_only",
        allowed_use="Inspect diagnostic relation entropy and its support distribution/provenance.",
        forbidden_use="Do not use for refutation support while entropy remains synthetic or stage-index derived.",
        source_of_truth="Xi/relation entropy evaluator",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="proxy_provenance",
        prior_mainline_concept="proxy/synthetic component audit ledger",
        semantic_role="report_only",
        allowed_use="Declare which diagnostic components are proxy, synthetic, or pilot and when to replace them.",
        forbidden_use="Do not hide proxy usage or reinterpret proxy outputs as final biology.",
        source_of_truth="runtime provenance writer",
    ),
    MainlineCrosswalkEntry(
        diagnostic_table="emergence_alert",
        prior_mainline_concept="diagnostic emergence alert",
        semantic_role="report_only",
        allowed_use="Synthetic or diagnostic alerting for pipeline behavior and hard-case routing.",
        forbidden_use="Do not write synthetic emergence alerts to production/scientific statistics.",
        source_of_truth="emergence alert evaluator",
    ),
)


def crosswalk_rows() -> list[dict[str, str]]:
    """Return JSON/SQL-ready crosswalk rows."""
    return [entry.to_row() for entry in V85_TO_MAINLINE_CROSSWALK]


def lookup_crosswalk(diagnostic_table: str) -> MainlineCrosswalkEntry:
    """Return the crosswalk entry for a table, raising KeyError if unknown."""
    for entry in V85_TO_MAINLINE_CROSSWALK:
        if entry.diagnostic_table == diagnostic_table:
            return entry
    raise KeyError(diagnostic_table)


def tables_by_role(role: str) -> list[str]:
    """Return diagnostic table names matching a semantic role."""
    return [entry.diagnostic_table for entry in V85_TO_MAINLINE_CROSSWALK if entry.semantic_role == role]


__all__ = [
    "MainlineCrosswalkEntry",
    "V85_TO_MAINLINE_CROSSWALK",
    "crosswalk_rows",
    "lookup_crosswalk",
    "tables_by_role",
]
