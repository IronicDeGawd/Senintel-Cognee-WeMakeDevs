# Cognee — AI memory platform (research)

> Sources: https://github.com/topoteretes/cognee ,
> https://docs.cognee.ai/core-concepts/main-operations/remember ,
> https://pypi.org/project/cognee/ (checked 2026-07-05).
> VERIFY exact signatures against docs.cognee.ai at implementation time.

## What it is
Open-source AI memory for agents. Ingests any-format data, builds a self-hosted
**hybrid knowledge graph + vector store**. Runs local (self-hosted) or Cognee Cloud.
Python SDK (`pip install cognee`).

## Two API layers
- **High-level (memory-native, Cognee 1.0):**
  - `remember(data)` — permanent write = add + cognify + improve (background pipeline).
  - `recall(query)` — query with auto-routing (picks best search strategy).
  - `improve()` / memify — strengthen memory over time.
  - `forget(dataset)` — surgical delete.
- **Granular:**
  - `cognee.add(data)` — ingest/prepare.
  - `cognee.cognify()` — build graph: classify → chunk → LLM entity/relation extract →
    summarize → embed → commit edges.
  - `cognee.search(query, query_type=...)` — 14 retrieval modes (RAG → graph traversal).

## Minimal usage shape (verify)
```python
import cognee
await cognee.add(text_or_path)      # ingest
await cognee.cognify()              # build graph + embeddings
results = await cognee.search("...")  # query
# high-level:
await cognee.remember(text)
hits = await cognee.recall("...")
```

## Config
- LLM/embeddings backend configurable (OpenAI, Gemini, local Ollama).
  We already have a Gemini key (shared/config.py) — point Cognee at it.
- Local mode: no external creds beyond the LLM key → good default/demo mode.
- Cognee Cloud: Developer plan free with code COGNEE-35 → targets the iPhone track.

## Notes / risks
- Async API → our code_guardian is sync in places; wrap with asyncio or make async.
- cognify() is a background pipeline; may take seconds → warm the memory before demo.
- Confirm datasets/namespacing so per-team/per-repo memory stays isolated (forget() scope).
