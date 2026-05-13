"""
noether_entropy_ledger_pilot.py

EXTERNAL_TRANSITIONAL Module
Bridge ID: ledger_pilot_bridge

Role: High-level variational mechanics and entropy computations.
Only generates isolation and anomaly reports. Must never block mainline execution.

P7 fix: Now computes real entropy proxies from transport and P-band data.
"""
import numpy as np


class NoetherEntropyLedgerPilot:
    """Entropy/conservation pilot for external anomaly reporting.

    This module produces REPORTS only — never blocks mainline or writes to core objects.
    """

    def generate_report(self, t_packet, o_surface, p_band, transport_op=None):
        """Generate entropy and conservation report from real data.

        Args:
            t_packet: TStagePacket
            o_surface: ObservableSurface
            p_band: PrimaryBandRecord (may be None)
            transport_op: Optional TransportOperator for transport entropy

        Returns external isolation report dict.
        """
        # Transport entropy proxy: from transport distortion + survival ratio
        transport_entropy = 0.0
        if transport_op is not None:
            survival = getattr(transport_op, 'survival_ratio', 0.0)
            distortion = getattr(transport_op, 'transport_distortion', 0.0)
            # Higher distortion and lower survival = higher entropy
            transport_entropy = abs(distortion) * (1.0 - survival) if survival > 0 else 0.0

        # P-band stability proxy
        p_stability = 0.0
        if p_band is not None:
            p_stability = getattr(p_band, 'coherence_score', 0.0)

        # Free energy proxy: transport cost + (1 - coherence)
        free_energy_proxy = transport_entropy + (1.0 - p_stability)

        # Anomaly flag: high entropy + low coherence
        is_anomalous = free_energy_proxy > 1.5

        return {
            "status": "SUSPENDED_NUMERICAL_CLOSURE",
            "report_type": "external_isolation_report",
            "external_free_energy_proxy": round(free_energy_proxy, 6),
            "transport_entropy_proxy": round(transport_entropy, 6),
            "p_stability_proxy": round(p_stability, 6),
            "anomaly_flag": is_anomalous,
            "stage_k": t_packet.stage_k if t_packet else -1,
        }
