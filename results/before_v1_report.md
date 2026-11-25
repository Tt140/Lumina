# LuminaLab Swarm Benchmark Report (v1-before)

## Execution Metadata
- **Mode**: `v1-before`
- **Timestamp (UTC)**: `2026-11-24T01:58:53.952824+00:00`
- **Region**: `us-east-1`
- **Stack Name**: `LuminaLab-Swarm-Stack` (`CREATE_COMPLETE`)
- **DynamoDB Table**: `LuminaLab-Swarm-Stack-LuminaLabImpactTable-VT5UIOJUREZY`
- **Pre-Benchmark Table Item Count**: `0`

## Axis 1: 1 MB Scan Truncation & Read Cost (F-05B)

### Write Seeding Summary (via `DynamoImpactLedger.record_impact`)
| Metric | Value |
| --- | --- |
| Ground-Truth Items Written | `6943` |
| Total Stored Data Size | `1,520,517` bytes (`1.4501 MiB` / `1.5205 MB`) |
| Average Item Payload Size | `219` bytes |
| Write Wall Time | `36.366 s` |
| Write Latency p50 / p95 | `138.438 ms` / `247.787 ms` |
| Total Consumed Write Capacity Units (WCU) | `6942.0` |
| Transient Timeouts During Unthrottled Seed | `13` |

### Read Benchmark Summary (`10` calls to `get_aggregate_stats()`)
| Metric | Measured Result |
| --- | --- |
| Ground-Truth Item Count in Table | `6943` |
| Returned `total_sessions` (Min / Max / Mean) | `4604` / `4604` / `4604.0` |
| Mean Missing Records per Read | `2339.0` |
| Mean Truncation Error Rate | `33.689%` |
| Calls Returning `LastEvaluatedKey` | `10 / 10` |
| Calls with Unfollowed `LastEvaluatedKey` | `10 / 10` |
| Mean `ScannedCount` per Read | `4604.0` (Total: `46040`) |
| Consumed RCU per Read (Mean / p50) | `129.0` / `129.0` (Total: `1290.0`) |
| Read Latency p50 / p95 | `2939.996 ms` / `3872.948 ms` |

#### Per-Call `get_aggregate_stats()` Measurements
| Call | Returned | Ground Truth | Truncation % | `LastEvaluatedKey` | Ops | `ScannedCount` | RCU | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4604 | 6943 | 33.689% | `True` | `Scan` | 4604 | 129.0 | 3702.751 |
| 2 | 4604 | 6943 | 33.689% | `True` | `Scan` | 4604 | 129.0 | 2656.22 |
| 3 | 4604 | 6943 | 33.689% | `True` | `Scan` | 4604 | 129.0 | 4012.201 |
| 4 | 4604 | 6943 | 33.689% | `True` | `Scan` | 4604 | 129.0 | 2950.464 |
| 5 | 4604 | 6943 | 33.689% | `True` | `Scan` | 4604 | 129.0 | 3643.184 |
| 6 | 4604 | 6943 | 33.689% | `True` | `Scan` | 4604 | 129.0 | 3307.791 |
| 7 | 4604 | 6943 | 33.689% | `True` | `Scan` | 4604 | 129.0 | 2782.967 |
| 8 | 4604 | 6943 | 33.689% | `True` | `Scan` | 4604 | 129.0 | 2583.777 |
| 9 | 4604 | 6943 | 33.689% | `True` | `Scan` | 4604 | 129.0 | 2776.754 |
| 10 | 4604 | 6943 | 33.689% | `True` | `Scan` | 4604 | 129.0 | 2929.528 |

## Axis 2: Network Jitter, Silent Data Loss & False Success (F-05A)

- **Client Config**: `connect_timeout=0.6s`, `read_timeout=0.6s`, `retries={"total_max_attempts": 1, "mode": "legacy"}`
- **Injected Transport Jitter Window**: `700.0 - 900.0 ms` across `10` attempts

| Metric | Measured Result |
| --- | --- |
| Returned `recorded` (AWS Confirmed) | `0 / 10` |
| Returned `recorded_local_fallback` | `10 / 10` |
| Confirmed Present in AWS DynamoDB (`GetItem`) | `0 / 10` |
| `_local_store` Count Before Process Restart | `10` |
| `_local_store` Count After Process Restart | `0` |
| Silently Lost Records After Restart | `10` (`100.0%`) |

### `LuminaSwarmOrchestrator` Trace Audit Under Jitter
- **DynamoDB Receipt Status**: `recorded_local_fallback`
- **`swarm_trace` (`AWS_DynamoDB`) Status**: `success`
- **Confirmed in Live DynamoDB**: `False`
- **False-Success Bug Reproduced**: `True`

## Axis 3: Live Stack IAM & Observability Audit (F-05B / F-05C)

| Audit Check | Live AWS Finding |
| --- | --- |
| `LuminaLabSwarmPolicy` DynamoDB Actions | `dynamodb:GetItem, dynamodb:PutItem, dynamodb:Scan, dynamodb:UpdateItem` |
| Broad `dynamodb:Scan` Permission Present | `True` |
| `AWS::CloudWatch::Alarm` in Stack | `0` |
| `AWS::Logs::LogGroup` in Stack | `0` |
| `AWS::SNS::Topic` in Stack | `0` |
| `AWS::CloudWatch::Dashboard` in Stack | `0` |
| Live CloudWatch Matching Alarms | `0` |

## Axis 4: Post-Benchmark Cleanup Verification
- **Cleanup Executed**: `True`
- **DynamoDB Items Deleted**: `6943` / `6943`
- **Post-Cleanup Table Item Count**: `0`
