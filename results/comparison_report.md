# LuminaLab Swarm — Live AWS Apples-to-Apples Comparison Report (F-05)

## Benchmark Provenance
- **Baseline (`v1-before`)**: `2026-11-24T01:58:53.952824+00:00` | Region `us-east-1` | Table `LuminaLab-Swarm-Stack-LuminaLabImpactTable-VT5UIOJUREZY`
- **Remediated (`v2-after`)**: `2026-11-24T02:22:40.105814+00:00` | Region `us-east-1` | Table `LuminaLab-Swarm-Stack-LuminaLabImpactTable-VT5UIOJUREZY`
- *All figures below are computed programmatically from `results/before_v1.json` and `results/after_v2.json`.*

## Executive Comparison Matrix (`Before v1` vs `After v2`)
| Metric | Before (`v1-before`) | After (`v2-after`) | Delta / Impact |
| --- | --- | --- | --- |
| Ground-Truth Records Seeded (`record_impact`) | `6943` (`1.4501 MiB`) | `6975` (`1.4501 MiB`) | `+32` items |
| Returned `total_sessions` (Mean over `10` reads) | `4604.0` | `6975.0` | `+2371.0` (`100%` match) |
| Missing / Truncated Records per Read | `2339.0` | `0.0` | `-2339.0` |
| Truncation Error Rate | `33.689%` | `0.0%` | `-33.689%` |
| DynamoDB Read Operation | `Scan` | `GetItem` | `O(N)` full-table scan -> `O(1)` lookup |
| Unfollowed `LastEvaluatedKey` Calls | `10 / 10` | `0 / 10` | Eliminated |
| Mean `ScannedCount` per Read | `4604.0` (`46040` total) | `0.0` (`0` total) | Eliminated table scans |
| Consumed Read Capacity (`RCU` / call) | `129.0` (`1290.0` / 10 calls) | `0.5` (`5.0` / 10 calls) | `-99.61%` (`-128.5` RCU/call) |
| Read Latency `p50` | `2939.996 ms` | `204.618 ms` | `-93.04%` (`14.37x` faster) |
| Read Latency `p95` | `3872.948 ms` | `429.266 ms` | `-88.92%` (`-3443.682 ms`) |
| Confirmed AWS Writes Under `700-900 ms` Jitter | `0 / 10` | `10 / 10` | `+10` durable writes |
| Silent Data Loss Rate After Restart | `100.0%` (`10` lost) | `0.0%` (`0` lost) | `-100.00%` |
| Orchestrator `AWS_DynamoDB` Trace Under Jitter | `status=success` (`false_success=True`) | `status=success` (`false_success=False`) | Confirmed live DynamoDB write |
| Broad `dynamodb:Scan` Permission in IAM Policy | `True` | `False` | Removed (`SEC03-BP01`) |
| Provisioned CloudWatch / SNS Observability Resources | `0` (`0` Alarms, `0` Logs, `0` SNS) | `6` (`4` Alarms, `1` LogGroup, `1` SNS) | `+6` resources |

## Live AWS Idempotency Verification (`v2-after`)
- **Probe `session_id`**: `bench-v2-after-855c23c9-idempotency-probe-01`
- **Before First Send**: `total_sessions = 0`
- **After First Send**: `status = recorded`, `total_sessions = 1` (`+1`)
- **After Duplicate Replay (Same `session_id`)**: `status = recorded` (`idempotent_duplicate = True`), `total_sessions = 1` (`+0`)
- **Stored DynamoDB Rows for `session_id`**: `1`
- **Idempotency Verified**: `True`

## Honest Measured Trade-offs (Cost, Contention & Latency)
| Trade-off Dimension | Before (`v1-before`) | After (`v2-after`) | Engineering Assessment |
| --- | --- | --- | --- |
| Total Write Capacity Units (`WCU`) for Seeding | `6942.0` (`1.00` WCU/session) | `27900.0` (`4.00` WCU/session) | `+20958.0` WCU (`4.02x`): `TransactWriteItems` performs a 2-item ACID commit (Put + Aggregate Update) billed at 2x transactional write units |
| Concurrent Write Latency (`p50` / `p95`, `36.366s` vs `71.077s` wall) | `138.438 ms` / `247.787 ms` | `157.181 ms` / `758.248 ms` | `+18.743 ms` p50 / `+510.461 ms` p95 during concurrent writes to single `AGGREGATE#GLOBAL` key |
| `TransactionConflict` Retries & Seed Fallbacks | `0` tx conflicts / `13` timeouts | `4401` tx conflict retries / `13` fallbacks | Updating one unsharded `AGGREGATE#GLOBAL` item at concurrent workers triggers write-lock contention (`TransactionConflict` retries handled in code; sustained write bursts would require write-sharding) |
| KMS Encryption & CloudWatch Observability Baseline | `$0.00/mo` KMS (`0` KMS keys, `0` alarms, `0` log groups) | `1` KMS CMK, `4` CloudWatch Alarms, `1` LogGroup (30d retention) | Adding KMS CMK for encrypted CloudWatch->SNS alerts introduces AWS standard list cost (`$1.00/month` per CMK + standard CloudWatch alarm/log ingestion tiers) |
| Post-Benchmark Cleanup Verification | `0` items remaining | `0` items remaining | Verified clean table (`0` items after benchmark & idempotency probe) |
