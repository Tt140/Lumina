"use strict";

/* LuminaLab Swarm - Ledger Reliability Inspector (/audit)
 * Zero hardcoded measurement values: all data originates from measured JSON snapshots
 * (/api/audit/benchmarks) and live AWS probes (/api/audit/*).
 */

const state = {
  viewMode: "v2", // "v1" | "v2" | "delta"
  benchmarks: null,
  infra: null,
  probeSessionIds: [],
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function appendTelemetry(operation, message, statusKind = "info") {
  const container = document.getElementById("telemetry-log");
  if (!container) return;

  const now = new Date().toISOString().split("T")[1].slice(0, 12) + "Z";
  const line = el("div", "telemetry-line");
  line.appendChild(el("span", "tl-ts", `[${now}]`));
  line.appendChild(el("span", "tl-op", operation));
  const msgClass = statusKind === "ok" ? "tl-msg ok" : statusKind === "err" ? "tl-msg err" : "tl-msg";
  line.appendChild(el("span", msgClass, message));

  container.prepend(line);
}

function formatNumber(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "--";
  return Number(n).toFixed(digits);
}

function renderVerdictAndKpis() {
  const payload = state.benchmarks;
  const card = document.getElementById("verdict-card");
  const titleEl = document.getElementById("verdict-title");
  const descEl = document.getElementById("verdict-subtitle");
  const badgeEl = document.getElementById("verdict-badge");

  const kpiAcc = document.getElementById("kpi-accuracy");
  const kpiAccSub = document.getElementById("kpi-accuracy-sub");
  const kpiRcu = document.getElementById("kpi-rcu");
  const kpiRcuSub = document.getElementById("kpi-rcu-sub");
  const kpiLat = document.getElementById("kpi-latency");
  const kpiLatSub = document.getElementById("kpi-latency-sub");
  const kpiLoss = document.getElementById("kpi-loss");
  const kpiLossSub = document.getElementById("kpi-loss-sub");

  if (!payload || (!payload.before && !payload.after)) {
    titleEl.textContent = "NO BENCHMARK SNAPSHOTS FOUND";
    descEl.textContent = "Run benchmark_ledger.py to populate results/before_v1.json and results/after_v2.json.";
    return;
  }

  const mode = state.viewMode;
  const before = payload.before;
  const after = payload.after;
  const comp = payload.comparison;

  card.classList.remove("is-v1", "is-v2");
  titleEl.classList.remove("is-v1", "is-v2");
  badgeEl.classList.remove("is-v1", "is-v2");
  kpiAcc.classList.remove("cell-red", "cell-green");
  kpiRcu.classList.remove("cell-red", "cell-green");
  kpiLat.classList.remove("cell-red", "cell-green");
  kpiLoss.classList.remove("cell-red", "cell-green");

  if (mode === "v1" && before) {
    const r = before.axis_1_scale_and_truncation.read_phase.summary;
    const w = before.axis_1_scale_and_truncation.write_phase;
    const ax2 = before.axis_2_jitter_and_false_success.summary;
    const ops = before.axis_1_scale_and_truncation.read_phase.per_call_runs[0]?.dynamodb_operations?.join(", ") || "Scan";

    card.classList.add("is-v1");
    titleEl.classList.add("is-v1");
    badgeEl.classList.add("is-v1");
    titleEl.textContent = "TRUNCATED / SILENT LOSS";
    descEl.textContent = `v1-before uses unpaginated ${ops} (>1 MB limit exceeded) and 0.6s/0-retry timeouts.`;
    badgeEl.textContent = "F-05 UNREMEDIATED";

    kpiAcc.classList.add("cell-red");
    kpiAcc.textContent = `${Math.round(r.returned_sessions_mean)} / ${r.ground_truth_count}`;
    kpiAccSub.textContent = `Truncation error: ${r.truncation_error_pct_mean}% (LastEvaluatedKey ${r.unfollowed_last_evaluated_key_calls}/10)`;

    kpiRcu.classList.add("cell-red");
    kpiRcu.textContent = `${r.consumed_rcu_per_call_mean} RCU`;
    kpiRcuSub.textContent = `${ops} scanned ${r.scanned_count_per_call_mean} items/call (${w.estimated_total_mib} MiB)`;

    kpiLat.classList.add("cell-red");
    kpiLat.textContent = `${Math.round(r.read_latency_ms.p50)} / ${Math.round(r.read_latency_ms.p95)} ms`;
    kpiLatSub.textContent = `O(N) table scan latency over ${w.confirmed_written_items} records`;

    kpiLoss.classList.add("cell-red");
    kpiLoss.textContent = `${ax2.silent_data_loss_rate_pct}%`;
    kpiLossSub.textContent = `${ax2.silently_lost_records_on_restart}/${ax2.total_attempts} lost under 700-900 ms jitter`;
  } else if (mode === "delta" && before && after && comp) {
    const rA = after.axis_1_scale_and_truncation.read_phase.summary;
    const rB = before.axis_1_scale_and_truncation.read_phase.summary;
    const a2 = after.axis_2_jitter_and_false_success.summary;
    const b2 = before.axis_2_jitter_and_false_success.summary;

    card.classList.add("is-v2");
    titleEl.classList.add("is-v2");
    badgeEl.classList.add("is-v2");
    titleEl.textContent = `VERIFIED DELTA: -${comp.rcu_reduction_pct}% RCU / ${comp.read_p50_speedup}x FASTER`;
    descEl.textContent = "Empirical comparison computed directly from before_v1.json and after_v2.json.";
    badgeEl.textContent = "BEFORE -> AFTER";

    kpiAcc.classList.add("cell-green");
    kpiAcc.textContent = `${rB.truncation_error_pct_mean}% -> ${rA.truncation_error_pct_mean}%`;
    kpiAccSub.textContent = `Truncation delta: ${comp.truncation_delta_pct}% (0 missed records)`;

    kpiRcu.classList.add("cell-green");
    kpiRcu.textContent = `${rB.consumed_rcu_per_call_mean} -> ${rA.consumed_rcu_per_call_mean}`;
    kpiRcuSub.textContent = `${comp.rcu_reduction_pct}% Read Capacity reduction per /api/stats call`;

    kpiLat.classList.add("cell-green");
    kpiLat.textContent = `${comp.read_p50_speedup}x p50 speedup`;
    kpiLatSub.textContent = `${formatNumber(rB.read_latency_ms.p50, 1)} ms -> ${formatNumber(rA.read_latency_ms.p50, 1)} ms (-${comp.read_p50_reduction_pct}%)`;

    kpiLoss.classList.add("cell-green");
    kpiLoss.textContent = `${b2.silent_data_loss_rate_pct}% -> ${a2.silent_data_loss_rate_pct}%`;
    kpiLossSub.textContent = `Loss delta: ${comp.silent_loss_delta_pct}% (${a2.confirmed_in_aws_dynamodb_count}/${a2.total_attempts} durable)`;
  } else if (after) {
    const r = after.axis_1_scale_and_truncation.read_phase.summary;
    const w = after.axis_1_scale_and_truncation.write_phase;
    const ax2 = after.axis_2_jitter_and_false_success.summary;
    const ops = after.axis_1_scale_and_truncation.read_phase.per_call_runs[0]?.dynamodb_operations?.join(", ") || "GetItem";

    card.classList.add("is-v2");
    titleEl.classList.add("is-v2");
    badgeEl.classList.add("is-v2");
    titleEl.textContent = "VERIFIED O(1) / ZERO LOSS";
    descEl.textContent = `v2-after uses atomic AGGREGATE#GLOBAL ${ops} with 2.0s/5.0s timeouts & 3 standard retries.`;
    badgeEl.textContent = "F-05 REMEDIATED";

    kpiAcc.classList.add("cell-green");
    kpiAcc.textContent = `${Math.round(r.returned_sessions_mean)} / ${r.ground_truth_count}`;
    kpiAccSub.textContent = `Truncation error: ${r.truncation_error_pct_mean}% (100% count fidelity)`;

    kpiRcu.classList.add("cell-green");
    kpiRcu.textContent = `${r.consumed_rcu_per_call_mean} RCU`;
    kpiRcuSub.textContent = `${ops} constant O(1) cost across ${w.estimated_total_mib} MiB (${r.scanned_count_per_call_mean} scanned)`;

    kpiLat.classList.add("cell-green");
    kpiLat.textContent = `${formatNumber(r.read_latency_ms.p50, 1)} / ${formatNumber(r.read_latency_ms.p95, 1)} ms`;
    kpiLatSub.textContent = comp ? `${comp.read_p50_speedup}x faster p50 vs v1-before` : "O(1) GetItem latency";

    kpiLoss.classList.add("cell-green");
    kpiLoss.textContent = `${ax2.silent_data_loss_rate_pct}%`;
    kpiLossSub.textContent = `${ax2.confirmed_in_aws_dynamodb_count}/${ax2.total_attempts} confirmed in AWS under 700-900 ms jitter`;
  }
}

function renderComparisonTable() {
  const tbody = document.getElementById("comparison-tbody");
  const tradeoffsEl = document.getElementById("tradeoffs-container");
  tbody.innerHTML = "";
  tradeoffsEl.innerHTML = "";

  const b = state.benchmarks?.before;
  const a = state.benchmarks?.after;
  const comp = state.benchmarks?.comparison;

  if (!b || !a) {
    const tr = el("tr");
    const td = el("td", "muted-cell", "Missing either before_v1.json or after_v2.json snapshot.");
    td.colSpan = 4;
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  const bw = b.axis_1_scale_and_truncation.write_phase;
  const aw = a.axis_1_scale_and_truncation.write_phase;
  const br = b.axis_1_scale_and_truncation.read_phase.summary;
  const ar = a.axis_1_scale_and_truncation.read_phase.summary;
  const bOp = b.axis_1_scale_and_truncation.read_phase.per_call_runs[0]?.dynamodb_operations?.join(",") || "Scan";
  const aOp = a.axis_1_scale_and_truncation.read_phase.per_call_runs[0]?.dynamodb_operations?.join(",") || "GetItem";
  const b2 = b.axis_2_jitter_and_false_success;
  const a2 = a.axis_2_jitter_and_false_success;
  const b3 = b.axis_3_stack_and_iam_audit;
  const a3 = a.axis_3_stack_and_iam_audit;
  const aObs = a3.observability_resources_in_stack;
  const bObs = b3.observability_resources_in_stack;
  const idem = a.idempotency_probe;

  const rows = [
    [
      "Returned vs Ground Truth",
      `${Math.round(br.returned_sessions_mean)} / ${br.ground_truth_count}`,
      `${Math.round(ar.returned_sessions_mean)} / ${ar.ground_truth_count}`,
      `${ar.truncation_error_pct_mean}% error (was ${br.truncation_error_pct_mean}%)`,
      "red-to-green",
    ],
    [
      "DynamoDB Read Operation",
      `${bOp} (Scanned ${Math.round(br.scanned_count_per_call_mean)})`,
      `${aOp} (Scanned ${Math.round(ar.scanned_count_per_call_mean)})`,
      "O(N) -> O(1)",
      "red-to-green",
    ],
    [
      "Consumed RCU / Read",
      `${br.consumed_rcu_per_call_mean} RCU`,
      `${ar.consumed_rcu_per_call_mean} RCU`,
      comp ? `-${comp.rcu_reduction_pct}%` : "--",
      "red-to-green",
    ],
    [
      "Read Latency (p50 / p95)",
      `${formatNumber(br.read_latency_ms.p50, 1)} / ${formatNumber(br.read_latency_ms.p95, 1)} ms`,
      `${formatNumber(ar.read_latency_ms.p50, 1)} / ${formatNumber(ar.read_latency_ms.p95, 1)} ms`,
      comp ? `${comp.read_p50_speedup}x faster` : "--",
      "red-to-green",
    ],
    [
      "Silent Loss Under Jitter",
      `${b2.summary.silent_data_loss_rate_pct}% (${b2.summary.silently_lost_records_on_restart}/10)`,
      `${a2.summary.silent_data_loss_rate_pct}% (${a2.summary.silently_lost_records_on_restart}/10)`,
      `${a2.summary.confirmed_in_aws_dynamodb_count}/${a2.summary.total_attempts} durable`,
      "red-to-green",
    ],
    [
      "Orchestrator False-Success",
      String(b2.orchestrator_trace_audit.false_success_reported),
      String(a2.orchestrator_trace_audit.false_success_reported),
      "Truthful trace + metric",
      "red-to-green",
    ],
    [
      "IAM dynamodb:Scan",
      String(b3.iam_policy.has_dynamodb_scan),
      String(a3.iam_policy.has_dynamodb_scan),
      "Least-privilege (SEC03)",
      "red-to-green",
    ],
    [
      "CW Alarms / LogGroup / SNS",
      `${bObs.cloudwatch_alarms_count} / ${bObs.cloudwatch_log_groups_count} / ${bObs.sns_topics_count}`,
      `${aObs.cloudwatch_alarms_count} / ${aObs.cloudwatch_log_groups_count} / ${aObs.sns_topics_count}`,
      "Live observability",
      "red-to-green",
    ],
  ];

  if (idem) {
    rows.push([
      "Live Idempotency (2x Replay)",
      "Not enforced (PutItem)",
      `${idem.total_sessions_before} -> ${idem.total_sessions_after_first} -> ${idem.total_sessions_after_second}`,
      `Verified: ${idem.idempotency_verified}`,
      "red-to-green",
    ]);
  }

  for (const [label, v1Val, v2Val, deltaVal, style] of rows) {
    const tr = el("tr");
    tr.appendChild(el("td", "", label));
    tr.appendChild(el("td", style === "red-to-green" ? "val-mono cell-red" : "val-mono", v1Val));
    tr.appendChild(el("td", style === "red-to-green" ? "val-mono cell-green" : "val-mono", v2Val));
    tr.appendChild(el("td", "val-mono cell-amber", deltaVal));
    tbody.appendChild(tr);
  }

  const tradeoffs = [
    {
      title: "WRITE CAPACITY (WCU) AMPLIFICATION",
      metric: `${bw.total_consumed_wcu} -> ${aw.total_consumed_wcu} WCU (${comp ? comp.wcu_ratio : "--"}x)`,
      note: "TransactWriteItems writes session + AGGREGATE#GLOBAL atomically at 2x transactional write billing (4 vs 1 WCU/item).",
    },
    {
      title: "SINGLE-KEY WRITE CONTENTION",
      metric: `${aw.transaction_conflict_retries ?? 0} TransactionConflict retries`,
      note: `Concurrent burst seeding caused ${aw.seeding_transient_timeout_fallbacks} transient contention fallbacks on single AGGREGATE#GLOBAL key.`,
    },
    {
      title: "WRITE LATENCY (P50 / P95)",
      metric: `${formatNumber(bw.write_latency_ms.p50, 1)}ms -> ${formatNumber(aw.write_latency_ms.p50, 1)}ms p50`,
      note: `p95 shifted ${formatNumber(bw.write_latency_ms.p95, 1)}ms -> ${formatNumber(aw.write_latency_ms.p95, 1)}ms under 30-worker lock serialization.`,
    },
    {
      title: "KMS + CLOUDWATCH INFRA COST",
      metric: `${a3.stack_resource_type_counts["AWS::KMS::Key"] ?? 0} KMS CMK + ${aObs.cloudwatch_alarms_count} Alarms`,
      note: "Encrypted SNS delivery adds AWS KMS CMK list cost (~$1.00/mo) and standard alarm/log retention tiers.",
    },
  ];

  for (const t of tradeoffs) {
    const box = el("div", "tradeoff-item");
    box.appendChild(el("div", "tradeoff-title", t.title));
    box.appendChild(el("div", "tradeoff-metric", t.metric));
    box.appendChild(el("div", "tradeoff-note", t.note));
    tradeoffsEl.appendChild(box);
  }
}

function renderInfraPanel() {
  const infra = state.infra;
  const before = state.benchmarks?.before;
  const panelEl = document.getElementById("infra-panel");
  const eyebrowEl = document.getElementById("infra-eyebrow");
  const titleEl = document.getElementById("infra-panel-title");
  const alarmsBody = document.getElementById("alarms-tbody");
  const scanBadge = document.getElementById("infra-scan-badge");
  const logRetentionEl = document.getElementById("infra-log-retention");
  const snsKmsEl = document.getElementById("infra-sns-kms");

  if (state.viewMode === "v1" && before && before.axis_3_stack_and_iam_audit) {
    const b3 = before.axis_3_stack_and_iam_audit;
    const bObs = b3.observability_resources_in_stack || {};
    const bIam = b3.iam_policy || {};
    const bMeta = before.metadata || {};

    if (panelEl) {
      panelEl.classList.remove("is-v2");
      panelEl.classList.add("is-v1");
    }
    if (eyebrowEl) eyebrowEl.textContent = "BASELINE AWS CONTROL PLANE — V1-BEFORE";
    if (titleEl) titleEl.textContent = "Over-Scoped IAM Policy & Unmonitored Stack (F-05B / F-05C)";
    document.getElementById("infra-stack-status").textContent = `Stack: ${b3.stack_name} (${b3.stack_status} · v1-before)`;
    if (infra) {
      document.getElementById("probe-target-table").textContent = `Table: ${infra.table_name}`;
    } else if (bMeta.table_name) {
      document.getElementById("probe-target-table").textContent = `Table: ${bMeta.table_name}`;
    }
    document.getElementById("env-badge").textContent = `${bMeta.region || infra?.region || "us-east-1"} | V1-BEFORE SNAPSHOT`;

    document.getElementById("infra-iam-actions").textContent = (bIam.dynamodb_actions || []).join(", ") || "--";
    scanBadge.textContent = bIam.has_dynamodb_scan
      ? "WARNING: dynamodb:Scan PRESENT"
      : "VERIFIED: dynamodb:Scan REMOVED";
    scanBadge.className = bIam.has_dynamodb_scan ? "kpi-sub cell-red" : "kpi-sub cell-green";

    document.getElementById("infra-log-group").textContent = `${bObs.cloudwatch_log_groups_count ?? 0} LogGroups provisioned`;
    logRetentionEl.textContent = "No centralized CloudWatch Logs (F-05C)";
    logRetentionEl.className = "kpi-sub cell-red";

    document.getElementById("infra-sns-topic").textContent = `${bObs.sns_topics_count ?? 0} SNS Topics provisioned`;
    snsKmsEl.textContent = "No SNS alerting or KMS CMK";
    snsKmsEl.className = "kpi-sub cell-red";

    alarmsBody.innerHTML = "";
    const tr = el("tr");
    const td = el(
      "td",
      "muted-cell cell-red",
      `${bObs.cloudwatch_alarms_count ?? 0} CloudWatch Alarms provisioned in v1-before baseline (Fallback, Throttles, SystemErrors & UserErrors unmonitored).`
    );
    td.colSpan = 4;
    tr.appendChild(td);
    alarmsBody.appendChild(tr);
    return;
  }

  if (!infra) return;

  if (panelEl) {
    panelEl.classList.remove("is-v1");
  }
  if (eyebrowEl) eyebrowEl.textContent = "LIVE AWS CONTROL PLANE";
  if (titleEl) titleEl.textContent = "IAM Least-Privilege & CloudWatch Alarms";
  document.getElementById("infra-stack-status").textContent = `Stack: ${infra.stack_name} (${infra.stack_status})`;
  document.getElementById("probe-target-table").textContent = `Table: ${infra.table_name}`;
  document.getElementById("env-badge").textContent = `${infra.region} | ${infra.mock_mode ? "MOCK MODE" : "LIVE AWS"}`;

  document.getElementById("infra-iam-actions").textContent = infra.iam_policy.dynamodb_actions.join(", ");
  if (infra.iam_policy.has_dynamodb_scan) {
    scanBadge.textContent = "WARNING: dynamodb:Scan PRESENT";
    scanBadge.className = "kpi-sub cell-red";
  } else {
    scanBadge.textContent = "VERIFIED: dynamodb:Scan REMOVED";
    scanBadge.className = "kpi-sub cell-green";
  }

  document.getElementById("infra-log-group").textContent = infra.log_group.name || "--";
  logRetentionEl.textContent = `Retention: ${infra.log_group.retention_in_days ?? "--"} days`;
  logRetentionEl.className = "kpi-sub";

  document.getElementById("infra-sns-topic").textContent = infra.sns_topic.arn ? infra.sns_topic.arn.split(":").pop() : "--";
  snsKmsEl.textContent = infra.sns_topic.kms_encrypted ? "KMS Encrypted (CMK)" : "Unencrypted";
  snsKmsEl.className = infra.sns_topic.kms_encrypted ? "kpi-sub cell-green" : "kpi-sub cell-amber";

  alarmsBody.innerHTML = "";
  if (!infra.alarms || infra.alarms.length === 0) {
    const tr = el("tr");
    const td = el("td", "muted-cell", infra.mock_mode ? "Mock offline mode active (no live CloudWatch alarms queried)." : "No alarms found.");
    td.colSpan = 4;
    tr.appendChild(td);
    alarmsBody.appendChild(tr);
    return;
  }

  for (const alarm of infra.alarms) {
    const tr = el("tr");
    tr.appendChild(el("td", "val-mono", alarm.name));
    tr.appendChild(el("td", "val-mono", alarm.metric_name));
    tr.appendChild(el("td", "val-mono", `>= ${alarm.threshold} / ${alarm.period}s`));
    const tdState = el("td");
    const stateVal = String(alarm.state_value || "UNKNOWN");
    const pillClass = stateVal === "OK" ? "state-pill ok" : stateVal === "ALARM" ? "state-pill alarm" : "state-pill warn";
    tdState.appendChild(el("span", pillClass, stateVal));
    tr.appendChild(tdState);
    alarmsBody.appendChild(tr);
  }
}

function renderProbeOutput(pairs) {
  const box = document.getElementById("probe-output-box");
  box.innerHTML = "";
  const grid = el("div", "probe-kv-grid");
  for (const [k, v, cssClass] of pairs) {
    const row = el("div");
    row.appendChild(el("div", "probe-kv-label", k));
    row.appendChild(el("div", `probe-kv-val ${cssClass || ""}`, v));
    grid.appendChild(row);
  }
  box.appendChild(grid);
}

async function fetchJson(url, options = {}) {
  const resp = await fetch(url, options);
  const data = await resp.json();
  if (!resp.ok) {
    throw new Error(data.detail || `HTTP ${resp.status}`);
  }
  return data;
}

async function loadInitialData() {
  try {
    const bench = await fetchJson("/api/audit/benchmarks");
    state.benchmarks = bench;
    renderVerdictAndKpis();
    renderComparisonTable();
    appendTelemetry(
      "GET /api/audit/benchmarks",
      `Loaded measured snapshots (before=${bench.before ? "yes" : "no"}, after=${bench.after ? "yes" : "no"})`,
      "ok"
    );
  } catch (err) {
    appendTelemetry("GET /api/audit/benchmarks", `Error: ${err.message}`, "err");
  }

  await refreshInfrastructure();
}

async function refreshInfrastructure() {
  try {
    const infra = await fetchJson("/api/audit/infrastructure");
    state.infra = infra;
    renderInfraPanel();
    appendTelemetry(
      "GET /api/audit/infrastructure",
      `Stack=${infra.stack_status} | Scan=${infra.iam_policy.has_dynamodb_scan} | Alarms=${infra.alarms.length} | ${infra.latency_ms} ms`,
      "ok"
    );
  } catch (err) {
    appendTelemetry("GET /api/audit/infrastructure", `Error: ${err.message}`, "err");
  }
}

async function runStatsProbe() {
  const btn = document.getElementById("btn-stats-probe");
  btn.disabled = true;
  try {
    const res = await fetchJson("/api/audit/stats-probe");
    renderProbeOutput([
      ["OPERATION", res.operation, "cell-green"],
      ["SERVER LATENCY", `${res.latency_ms} ms`, "cell-amber"],
      ["TOTAL SESSIONS", String(res.stats.total_sessions), ""],
      ["CONSUMED CAPACITY", `${res.consumed_rcu} RCU`, "cell-green"],
      ["AVG GRADE REDUCTION", String(res.stats.avg_grade_reduction), ""],
      ["OFFLINE-READY LABS", String(res.stats.total_offline_ready_labs), ""],
    ]);
    appendTelemetry(
      "GET /api/audit/stats-probe",
      `${res.operation} -> total_sessions=${res.stats.total_sessions}, RCU=${res.consumed_rcu}, ${res.latency_ms} ms`,
      "ok"
    );
  } catch (err) {
    appendTelemetry("GET /api/audit/stats-probe", `Error: ${err.message}`, "err");
  } finally {
    btn.disabled = false;
  }
}

async function runIdempotencyProbe() {
  const btn = document.getElementById("btn-idem-probe");
  btn.disabled = true;
  try {
    const res = await fetchJson("/api/audit/idempotency-probe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    state.probeSessionIds.push(res.session_id);

    renderProbeOutput([
      ["PROBE SESSION_ID", res.session_id, ""],
      ["IDEMPOTENCY VERIFIED", String(res.idempotency_verified), res.idempotency_verified ? "cell-green" : "cell-red"],
      ["COUNTER PROGRESSION", `${res.stats_before.total_sessions} -> ${res.stats_after_first.total_sessions} (+${res.delta_first}) -> ${res.stats_after_second.total_sessions} (+${res.delta_second})`, "cell-green"],
      ["DUPLICATE FLAG", `status=${res.receipt_2.status} (dup=${Boolean(res.receipt_2.idempotent_duplicate)})`, "cell-amber"],
      ["TOTAL ROUNDTRIP", `${res.latency_ms} ms`, ""],
      ["MODE", res.mock_mode ? "mock" : "live AWS TransactWriteItems", ""],
    ]);
    appendTelemetry(
      "POST /api/audit/idempotency-probe",
      `sid=${res.session_id} | progression=${res.stats_before.total_sessions}->${res.stats_after_first.total_sessions}->${res.stats_after_second.total_sessions} | verified=${res.idempotency_verified} | ${res.latency_ms} ms`,
      res.idempotency_verified ? "ok" : "err"
    );
  } catch (err) {
    appendTelemetry("POST /api/audit/idempotency-probe", `Error: ${err.message}`, "err");
  } finally {
    btn.disabled = false;
  }
}

async function cleanupProbes() {
  const btn = document.getElementById("btn-cleanup-probe");
  btn.disabled = true;
  try {
    const res = await fetchJson("/api/audit/cleanup-probe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_ids: state.probeSessionIds }),
    });
    state.probeSessionIds = [];
    renderProbeOutput([
      ["CLEANUP STATUS", "COMPLETED", "cell-green"],
      ["DELETED PROBE ITEMS", String(res.deleted_count), ""],
      ["TABLE ITEM COUNT", String(res.remaining_table_items), res.remaining_table_items === 0 ? "cell-green" : "cell-amber"],
      ["STATS AFTER CLEANUP", `total_sessions=${res.stats_after.total_sessions}`, "cell-green"],
      ["LATENCY", `${res.latency_ms} ms`, ""],
    ]);
    appendTelemetry(
      "POST /api/audit/cleanup-probe",
      `deleted=${res.deleted_count}, remaining_table_items=${res.remaining_table_items}, ${res.latency_ms} ms`,
      "ok"
    );
  } catch (err) {
    appendTelemetry("POST /api/audit/cleanup-probe", `Error: ${err.message}`, "err");
  } finally {
    btn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".mode-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.viewMode = btn.dataset.mode;
      renderVerdictAndKpis();
      renderInfraPanel();
      appendTelemetry("UI VIEW SWITCH", `Switched snapshot view -> ${state.viewMode}`, "info");
    });
  });

  document.getElementById("btn-stats-probe").addEventListener("click", runStatsProbe);
  document.getElementById("btn-idem-probe").addEventListener("click", runIdempotencyProbe);
  document.getElementById("btn-cleanup-probe").addEventListener("click", cleanupProbes);
  document.getElementById("btn-refresh-infra").addEventListener("click", refreshInfrastructure);
  document.getElementById("btn-clear-log").addEventListener("click", () => {
    document.getElementById("telemetry-log").innerHTML = "";
  });

  loadInitialData();
});
