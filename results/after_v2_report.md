# LuminaLab Swarm Benchmark Report (v2-after)

## Execution Metadata
- **Mode**: `v2-after`
- **Timestamp (UTC)**: `2026-11-24T02:22:40.105814+00:00`
- **Region**: `us-east-1`
- **Stack Name**: `LuminaLab-Swarm-Stack` (`UPDATE_COMPLETE`)
- **DynamoDB Table**: `LuminaLab-Swarm-Stack-LuminaLabImpactTable-VT5UIOJUREZY`
- **Pre-Benchmark Table Item Count**: `0`

## Axis 1: 1 MB Scan Truncation & Read Cost (F-05B)

### Write Seeding Summary (via `DynamoImpactLedger.record_impact`)
| Metric | Value |
| --- | --- |
| Ground-Truth Items Written | `6975` |
| Total Stored Data Size | `1,520,550` bytes (`1.4501 MiB` / `1.5206 MB`) |
| Average Item Payload Size | `218` bytes |
| Write Wall Time | `71.077 s` |
| Write Latency p50 / p95 | `157.181 ms` / `758.248 ms` |
| Total Consumed Write Capacity Units (WCU) | `27900.0` |
| `TransactionConflict` Retries During Concurrent Seed | `4401` |
| Transient Timeouts During Unthrottled Seed | `13` |

### Read Benchmark Summary (`10` calls to `get_aggregate_stats()`)
| Metric | Measured Result |
| --- | --- |
| Ground-Truth Item Count in Table | `6975` |
| Returned `total_sessions` (Min / Max / Mean) | `6975` / `6975` / `6975.0` |
| Mean Missing Records per Read | `0.0` |
| Mean Truncation Error Rate | `0.0%` |
| Calls Returning `LastEvaluatedKey` | `0 / 10` |
| Calls with Unfollowed `LastEvaluatedKey` | `0 / 10` |
| Mean `ScannedCount` per Read | `0.0` (Total: `0`) |
| Consumed RCU per Read (Mean / p50) | `0.5` / `0.5` (Total: `5.0`) |
| Read Latency p50 / p95 | `204.618 ms` / `429.266 ms` |

#### Per-Call `get_aggregate_stats()` Measurements
| Call | Returned | Ground Truth | Truncation % | `LastEvaluatedKey` | Ops | `ScannedCount` | RCU | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 6975 | 6975 | 0.0% | `False` | `GetItem` | 0 | 0.5 | 612.813 |
| 2 | 6975 | 6975 | 0.0% | `False` | `GetItem` | 0 | 0.5 | 202.234 |
| 3 | 6975 | 6975 | 0.0% | `False` | `GetItem` | 0 | 0.5 | 204.897 |
| 4 | 6975 | 6975 | 0.0% | `False` | `GetItem` | 0 | 0.5 | 132.211 |
| 5 | 6975 | 6975 | 0.0% | `False` | `GetItem` | 0 | 0.5 | 175.215 |
| 6 | 6975 | 6975 | 0.0% | `False` | `GetItem` | 0 | 0.5 | 204.573 |
| 7 | 6975 | 6975 | 0.0% | `False` | `GetItem` | 0 | 0.5 | 204.785 |
| 8 | 6975 | 6975 | 0.0% | `False` | `GetItem` | 0 | 0.5 | 204.931 |
| 9 | 6975 | 6975 | 0.0% | `False` | `GetItem` | 0 | 0.5 | 204.566 |
| 10 | 6975 | 6975 | 0.0% | `False` | `GetItem` | 0 | 0.5 | 204.663 |

## Axis 2: Network Jitter, Silent Data Loss & False Success (F-05A)

- **Client Config**: `connect_timeout=2.0s`, `read_timeout=5.0s`, `retries={"total_max_attempts": 3, "mode": "standard"}`
- **Injected Transport Jitter Window**: `700.0 - 900.0 ms` across `10` attempts

| Metric | Measured Result |
| --- | --- |
| Returned `recorded` (AWS Confirmed) | `10 / 10` |
| Returned `recorded_local_fallback` | `0 / 10` |
| Confirmed Present in AWS DynamoDB (`GetItem`) | `10 / 10` |
| `_local_store` Count Before Process Restart | `0` |
| `_local_store` Count After Process Restart | `0` |
| Silently Lost Records After Restart | `0` (`0.0%`) |

### `LuminaSwarmOrchestrator` Trace Audit Under Jitter
- **DynamoDB Receipt Status**: `recorded`
- **`swarm_trace` (`AWS_DynamoDB`) Status**: `success`
- **Confirmed in Live DynamoDB**: `True`
- **False-Success Bug Reproduced**: `False`

## Axis 3: Live Stack IAM & Observability Audit (F-05B / F-05C)

| Audit Check | Live AWS Finding |
| --- | --- |
| `LuminaLabSwarmPolicy` DynamoDB Actions | `dynamodb:GetItem, dynamodb:PutItem, dynamodb:UpdateItem` |
| Broad `dynamodb:Scan` Permission Present | `False` |
| `AWS::CloudWatch::Alarm` in Stack | `4` |
| `AWS::Logs::LogGroup` in Stack | `1` |
| `AWS::SNS::Topic` in Stack | `1` |
| `AWS::CloudWatch::Dashboard` in Stack | `0` |
| Live CloudWatch Matching Alarms | `4` |

## Axis 4: Post-Benchmark Cleanup Verification
- **Cleanup Executed**: `True`
- **DynamoDB Items Deleted**: `6987` / `6987`
- **Post-Cleanup Table Item Count**: `0`

## Live Idempotency Probe (Duplicate `session_id` Replay)
| Step | Observed Value |
| --- | --- |
| `total_sessions` Before First Send | `0` |
| Receipt 1 Status | `recorded` |
| `total_sessions` After First Send | `1` (Delta: `+1`) |
| Receipt 2 Status (`idempotent_duplicate`) | `recorded` (`True`) |
| `total_sessions` After Duplicate Send | `1` (Delta: `+0`) |
| DynamoDB Session Item Count Verified | `1` |
| Post-Probe Cleanup Table Item Count | `0` |
| Idempotency Verified (`+1` then `+0`) | `True` |
