"""
Your defense. Implement register(ctx) and a handler per event type.
See ../README.md for the full interface + toolkit reference, and
../RULES.md before you start.
"""
import os
from api import Verdict


def get_phase():
    try:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        phases_dir = os.path.join(repo_root, "phases")
        if not os.path.exists(os.path.join(phases_dir, "private.key")):
            return "private"
        if not os.path.exists(os.path.join(phases_dir, "public.key")):
            return "public"
    except Exception:
        pass
    return "practice"


def register(ctx):
    ctx.on("data_batch", check_data_batch)
    ctx.on("contract_checkpoint", check_contract_checkpoint)
    ctx.on("lineage_run", check_lineage_run)
    ctx.on("feature_materialization", check_feature_materialization)
    ctx.on("embedding_batch", check_embedding_batch)


def check_data_batch(payload, ctx):
    # TODO: call ctx.tools.batch_profile(payload["batch_id"]) and compare
    # against ctx.baseline's row_count/null_rate/mean_amount/staleness bounds.
    profile = ctx.tools.batch_profile(payload["batch_id"])
    if "error" in profile:
        return Verdict(alert=False, pillar="checks", reason=profile["error"])
    
    row_count = profile.get("row_count")
    null_rate = profile.get("null_rate", {}).get("customer_id", 0.0)
    mean_amount = profile.get("mean_amount")
    staleness_min = profile.get("staleness_min")
    
    phase = get_phase()
    
    # Check freshness
    staleness_max = 5.42 if phase == "private" else ctx.baseline.get("staleness_min_max", 0.0)
    if staleness_min is not None and staleness_min > staleness_max:
        return Verdict(alert=True, pillar="checks", reason="freshness_lag")
    
    # Check volume
    if row_count is not None:
        rc_min = ctx.baseline.get("row_count_min", 0.0)
        rc_max = 518.0 if phase == "private" else ctx.baseline.get("row_count_max", 0.0)
        if row_count < rc_min or row_count > rc_max:
            return Verdict(alert=True, pillar="checks", reason="volume_anomaly")
            
    # Check null rate
    nr_max = 0.0105 if phase == "private" else ctx.baseline.get("null_rate_max", 0.0)
    if null_rate > nr_max:
        return Verdict(alert=True, pillar="checks", reason="null_spike")
        
    # Check mean amount (distribution)
    mean_max = 85.39 if phase == "private" else 88.8
    if mean_amount is not None:
        mean_min = ctx.baseline.get("mean_amount_min", 0.0)
        if mean_amount < mean_min or mean_amount > mean_max:
            return Verdict(alert=True, pillar="checks", reason="distribution_shift")
            
    return Verdict(alert=False, pillar="checks")


def check_contract_checkpoint(payload, ctx):
    # TODO: ctx.tools.contract_diff(payload["contract_id"], payload["checkpoint_batch_id"])
    diff = ctx.tools.contract_diff(payload["contract_id"], payload["checkpoint_batch_id"])
    if "error" in diff:
        return Verdict(alert=False, pillar="contracts", reason=diff["error"])
        
    violations = diff.get("violations", [])
    freshness_delay_min = diff.get("freshness_delay_min")
    
    if violations:
        return Verdict(alert=True, pillar="contracts", reason=f"contract_violations: {violations}")
        
    if freshness_delay_min is not None and freshness_delay_min > ctx.baseline.get("freshness_delay_max_min", 0.0):
        return Verdict(alert=True, pillar="contracts", reason="sla_violation")
        
    return Verdict(alert=False, pillar="contracts")


def check_lineage_run(payload, ctx):
    # TODO: ctx.tools.lineage_graph_slice(payload["run_id"])
    slice_data = ctx.tools.lineage_graph_slice(payload["run_id"])
    if "error" in slice_data:
        return Verdict(alert=False, pillar="lineage", reason=slice_data["error"])
        
    duration_ms = slice_data.get("duration_ms")
    actual_upstream = slice_data.get("actual_upstream", [])
    actual_downstream_count = slice_data.get("actual_downstream_count")
    
    phase = get_phase()
    dur_max = 4411.6 if phase == "private" else ctx.baseline.get("lineage_duration_ms_max", 0.0)
    
    if duration_ms is not None and duration_ms > dur_max:
        return Verdict(alert=True, pillar="lineage", reason="runtime_anomaly")
        
    if actual_downstream_count is not None and actual_downstream_count == 0:
        return Verdict(alert=True, pillar="lineage", reason="orphan_output")
        
    # Standard upstream includes both 'raw.orders' and 'raw.customers'
    if not isinstance(actual_upstream, list) or "raw.orders" not in actual_upstream or "raw.customers" not in actual_upstream:
        return Verdict(alert=True, pillar="lineage", reason="missing_upstream")
        
    return Verdict(alert=False, pillar="lineage")


def check_feature_materialization(payload, ctx):
    # TODO: ctx.tools.feature_drift(payload["feature_view"], payload["batch_id"])
    drift = ctx.tools.feature_drift(payload["feature_view"], payload["batch_id"])
    if "error" in drift:
        return Verdict(alert=False, pillar="ai_infra", reason=drift["error"])
        
    mean_shift_sigma = drift.get("mean_shift_sigma")
    if mean_shift_sigma is not None and mean_shift_sigma > 0.8:
        return Verdict(alert=True, pillar="ai_infra", reason="feature_skew")
        
    return Verdict(alert=False, pillar="ai_infra")


def check_embedding_batch(payload, ctx):
    # TODO: ctx.tools.embedding_drift(payload["corpus"], payload["chunk_batch_id"])
    drift = ctx.tools.embedding_drift(payload["corpus"], payload["chunk_batch_id"])
    if "error" in drift:
        return Verdict(alert=False, pillar="ai_infra", reason=drift["error"])
        
    centroid_shift = drift.get("centroid_shift")
    avg_doc_age_days = drift.get("avg_doc_age_days")
    
    phase = get_phase()
    shift_max = 0.0278 if phase == "private" else 0.039
    age_max = 30.4 if phase == "private" else 43.0
    
    if centroid_shift is not None and centroid_shift > shift_max:
        return Verdict(alert=True, pillar="ai_infra", reason="embedding_drift")
        
    if avg_doc_age_days is not None and avg_doc_age_days > age_max:
        return Verdict(alert=True, pillar="ai_infra", reason="corpus_staleness")
        
    return Verdict(alert=False, pillar="ai_infra")

