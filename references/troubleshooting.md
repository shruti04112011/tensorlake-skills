<!--
Source:
  - https://docs.tensorlake.ai/applications/overview.md
  - https://docs.tensorlake.ai/applications/production/troubleshooting.md
  - https://docs.tensorlake.ai/document-ingestion/production/integration.md
  - https://docs.tensorlake.ai/document-ingestion/production/benchmarks.md
SDK version: tensorlake 0.4.39
Last verified: 2026-04-07
-->

# TensorLake Troubleshooting & Production Guide

## Applications — Common Issues

### Function Timeout

- Increase the `timeout` value in your `@function` decorator
- Call `ctx.progress.update()` during execution to reset the timeout timer
- Check logs to identify what the function was doing before timeout

### Request Failed

- Retrieve full request state via API to identify the failure reason
- Filter logs by `ctx.request_id` to trace execution history

### Out of Memory

- Review the `memory` setting in the `@function` decorator
- Allocate more memory (up to 32 GB)
- Split large datasets into smaller batches

### Debugging Best Practices

- Use `print()` statements to track intermediate values (stdout is captured in logs)
- Use `ctx.request_id` to correlate logs across multiple function calls
- Verify CPU, memory, and disk resource allocations are adequate
- Check retry configurations for intermittent failures

---

## Document Ingestion — Production Integration

### Async Workflow Pattern

1. **Initiate parsing** — call the parse endpoint with `file_id` or `file_url`
2. **Poll status** — check parse job ID until completion (or use webhooks)
3. **Retrieve results** — fetch parsed output on success

### Request Parameters

- `file_id` or `file_url` — source document
- `page_range` — optional, defaults to all pages
- `labels` — optional metadata for tracking

### Response Structure

```json
{
  "chunks": ["...markdown content..."],
  "pages": [{"bounding_boxes": [...], "reading_order": [...]}],
  "status": "successful"
}
```

Status values: `pending`, `processing`, `successful`, `failure`

### Notification Options

- **Polling:** Check status endpoint at intervals
- **Webhooks:** Register for `tensorlake.document_ingestion.job.completed` / `.failed` events (see platform.md)

---

## Document Ingestion — Benchmarks

### Accuracy (vs. competitors)

| Provider | Cost/1K Pages | TEDS (Structure) | JSON F1 (Extraction) |
|----------|--------------|-------------------|----------------------|
| **TensorLake** | **$10** | **84.1%** | **91.7%** |
| AWS Textract | $15 | 81.0% | 88.4% |
| Azure Document Intelligence | $10 | 78.6% | 88.1% |
| Marker (open-source) | Free* | 71.1% | 71.2% |
| Docling (open-source) | Free* | 63.3% | 68.9% |

*Free solutions require self-hosting infrastructure.

### Table Parsing (OmniDocBench)

- TensorLake: **86.79% TEDS**
- Open-source competitors: sub-70% TEDS

### Production Impact

For 10,000 monthly documents, TensorLake achieves a **45% reduction** in manual reviews compared to 85% F1 baseline solutions (830 vs. 1,500 documents requiring review).

### Evaluation Methodology

Two-stage: OCR output assessed via TEDS scoring, then standardized LLM (GPT-4o) extraction evaluation using F1 metrics for field-level precision and recall.

---

## Architecture Overview

TensorLake is a **compute platform for agents** — it provides infrastructure, not an agent framework. You supply agent logic (OpenAI SDK, LangGraph, Claude SDK, or custom Python); the platform handles:

- **Deployment & scaling** — each function runs in its own container
- **Durable execution** — automatic checkpoints; retries resume from last successful step
- **Resource sandboxing** — configurable CPU, memory, GPU, and network per function
- **Observability** — unified logging and execution tracking

### Execution Models

- **Single-function agent loops** — straightforward workflows
- **Multi-function sandboxing** — tools with different resource needs
- **Harness pattern** — lightweight orchestrator + heavy worker functions
- **Parallel sub-agents** — futures and async patterns for fan-out
