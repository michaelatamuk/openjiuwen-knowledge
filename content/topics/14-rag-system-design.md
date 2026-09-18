# RAG system design

## 1. Design a RAG system for a customer support chatbot handling 100,000 queries a day

**General:** Start from the request rate and SLA, then choose components: ingestion (parse → chunk → embed → index), retrieval (hybrid dense+sparse), a reranker, a generation layer, caching, and observability. 100k/day is ~1.2 QPS average (bursts higher), so a single server-class vector DB is fine; the real work is cache hit rate, top-k tuning, guardrails, and a feedback loop. Size context and cost per query, then multiply.

**Jiuwen:** Provides the ingestion pipeline (`parse_files` → `chunk_documents` → `build_index`), hybrid retrieval with RRF, optional rerankers (graph store only), and the context/generation path via `KnowledgeRetrievalComponent` + `LLMComponent`. Product adds session cost tracking and a per-session cost cap. Gaps a design must cover: no packaged end-to-end RAG agent, no token budgeting on retrieved context, no quality monitoring (only error/latency tracing), and no semantic response cache.

```mermaid
flowchart LR
    Q["100k queries/day"] --> RET["hybrid retrieve (dense+sparse RRF)"]
    Q -.->|"absent"| CACHE["no query/response cache (only tool-call dedup cache)"]
    RET --> RR["optional rerank"] --> GEN["generate with retrieved context"]
    GEN --> OBS["observability: spans · cost per session"]
    OBS --> FB["feedback loop (partial)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:96/110/182</code> — ingest/retrieve pipeline<br>&bull; <code>agent-core/openjiuwen/core/retrieval/utils/fusion.py:15</code> — RRF hybrid merge<br>&bull; <code>agent-core/openjiuwen/core/workflow/components/resource/knowledge_retrieval_comp.py:109/243</code> — context assembly<br>&bull; <code>jiuwenswarm/jiuwenswarm/server/runtime/usage_cost.py:171</code> — session cost cap<br>&bull; <code>jiuwenswarm/jiuwenswarm/agents/harness/common/rails/tool_dedup_rail.py:47</code> — exact tool result cache</sub>

</details>

<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`; also covered in: rag-system._</sub>

---

## 2. Design a RAG pipeline for a codebase assistant that needs to stay current as code changes daily

**General:** Make re-indexing incremental and event-driven: a stable ID per file/chunk, delete-by-ID on change, append new chunks, and a trigger on commit/CI. Avoid full re-embeds except on model/index changes. Keep chunk boundaries structure-aware (functions/classes) and include file paths/branches as metadata so the assistant can cite and filter.

**Jiuwen:** The contract is delete-by-`doc_id` + rebuild: indexers scan a doc's chunk IDs, delete them, then re-chunk/re-embed/write (Milvus flushes between to defeat eventual consistency); new documents append into the pre-existing ANN index (no full re-index). `doc_id` is a first-class, scalar-inverted field. Chunking supports char/token/hybrid but has no code-aware/function-boundary chunker.

```mermaid
flowchart TD
    COMMIT["commit / CI"] --> DEL["delete_index(doc_id): remove old chunks"]
    DEL --> FL["Milvus flush (consistency) between delete and rebuild"]
    FL --> RE["re-chunk + re-embed + build_index"]
    NEW["new file"] --> APP["append into existing ANN index (no full re-index)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:219</code> — <code>update_documents</code>; <code>:74</code> <code>add_documents</code> appends<br>&bull; <code>agent-core/openjiuwen/core/retrieval/indexing/indexer/chroma_indexer.py:198</code> — <code>update_index</code> = delete + build; <code>:217</code> delete by <code>doc_id</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/indexing/indexer/milvus_indexer.py:209</code> — delete + flush + rebuild; <code>:346</code> <code>INVERTED</code> scalar index<br>&bull; <code>agent-core/openjiuwen/core/retrieval/indexing/processor/chunker/hybrid_chunker.py:19</code> — structural no-split guard</sub>

</details>

<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`; also covered in: rag-system._</sub>

---

## 3. Design a document search system for a legal firm with millions of confidential documents

**General:** The dominant requirement is access control, then scale. Every chunk must carry an ACL (owner, matter, tenant) and every query must be filtered by the caller's permissions *inside* the vector search (pre-filter), not after. Combine that with hybrid retrieval, a reranker, encryption at rest, audit logging, and per-matter isolation. Confidentiality also means no cross-matter leakage in the prompt context.

**Jiuwen:** Supports metadata filtering at the **store** layer (Milvus expr, Chroma `where`, PG JSONB) and per-KB collections (`kb_{kb_id}_chunks`), plus a permission engine and audit logging. But the retriever layer **drops** `RetrievalConfig.filters` — concrete retrievers hardcode `filters=None` — so permission-aware retrieval is not reachable through the KB path, and there is no document/chunk ACL field. Permission-aware retrieval would require re-plumbing filters through the retriever.

```mermaid
flowchart TD
    Q["legal query + user identity"] --> ACL{"ACL pre-filter in vector search"}
    ACL -.->|"dropped: retrievers hardcode filters=None"| X["filters never reach the store"]
    Q --> S["store supports metadata where (Milvus/Chroma/PG)"]
    Q --> ISO["per-KB collection kb_{kb_id}_chunks (not per-tenant)"]
    Q --> AUD["permission engine + audit (tool/file path, not doc ACL)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/common/config.py:53</code> — <code>RetrievalConfig.filters</code>; <code>agent-core/openjiuwen/core/retrieval/retriever/base.py:19</code> — abstract <code>retrieve</code> has no <code>filters</code>; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:186</code> — KB passes <code>filters</code>; <code>agent-core/openjiuwen/core/retrieval/retriever/vector_retriever.py:88</code> / <code>agent-core/openjiuwen/core/retrieval/retriever/hybrid_retriever.py:81</code> — hardcoded <code>filters=None</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/milvus_store.py:215</code> — Milvus filter expr; <code>agent-core/openjiuwen/core/retrieval/vector_store/chroma_store.py:265</code> — <code>where</code>; <code>agent-core/openjiuwen/core/retrieval/vector_store/pg_store.py:474</code> — JSONB<br>&bull; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:102</code> — <code>kb_{kb_id}_chunks</code><br>&bull; <code>agent-core/openjiuwen/harness/security/permission_engine/core.py:272</code> — <code>check_permission</code> (tool/file/net, not retrieval)<br>&bull; <code>agent-core/openjiuwen/core/common/security/user_config.py:69</code> — sensitive-path config (filesystem, not doc ACL)</sub>

</details>

<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`; also covered in: rag-system._</sub>

---

## 4. How retrieval architecture changes from 10,000 to 10 million documents

**General:** At small scale, a local in-process index (FAISS/Chroma) is fine. At large scale you need a dedicated vector DB with tuned ANN indexes (HNSW/IVF/quantization), sharding/partitioning, replication, and batch ingestion; you also start caring about memory, index build time, and recall/latency tuning per query. The interface stays the same but the operational envelope changes.

**Jiuwen:** Scale-out is delegated to the backend: Chroma = local persistent HNSW (small/medium), Milvus = server ANN with selectable AUTO/HNSW/IVF/SCANN and quantization variants (large), PGVector = pgvector HNSW (relational; the field type also declares `ivfflat`, but no IVFFlat index branch is implemented). Writes are batched (128) and flushed. Milvus BM25 for hybrid is native (`SPARSE_INVERTED_INDEX`) plus a jieba analyzer. The architecture is a single collection per KB (`kb_{kb_id}_chunks`) with one ANN index created once at collection creation. There is no sharding, partitioning, replica, or multi-collection fan-out anywhere.

```mermaid
flowchart LR
    S["scale"] --> SM["~10K: Chroma (local HNSW)"]
    S --> LG["millions: Milvus (AUTO/HNSW/IVF/SCANN + quantization)"]
    S --> REL["relational: PGVector (HNSW)"]
    SM --> W["batched writes (128)"]
    LG --> W
    REL --> W
    W -.->|"absent"| SHARD["no sharding · partition · replica · fan-out"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/store.py:16</code> — <code>create_vector_store</code> (Milvus/Chroma/PGVector); <code>agent-core/openjiuwen/core/retrieval/common/config.py:67</code> — store type enum<br>&bull; <code>agent-core/openjiuwen/core/retrieval/indexing/indexer/milvus_indexer.py:433</code> — index type AUTOINDEX/HNSW/IVF/FLAT/SCANN; <code>:346</code> inverted scalar indexes<br>&bull; <code>agent-core/openjiuwen/core/foundation/store/vector_fields/milvus_fields.py:282</code> — <code>MilvusHNSW</code> (M=30, efConstruction=360); <code>:100</code> IVFFlat defaults; <code>:164</code> SCANN<br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/pg_store.py:203</code> — HNSW index; <code>agent-core/openjiuwen/core/foundation/store/vector_fields/pg_fields.py:37</code> — pgvector defaults<br>&bull; <code>agent-core/openjiuwen/core/foundation/store/vector_fields/chroma_fields.py:47</code> — Chroma HNSW defaults<br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/base.py:57</code> — <code>add(..., batch_size=128)</code></sub>

</details>

<sub>_Canonical source: `source/rag-retrieval-interview-questions_for_engineers.md`; also covered in: rag-1, rag-retrieval, rag-system._</sub>

---

## 5. How do you shard or partition a vector database as it grows

**General:** Options: partition by a key (tenant/category) so queries hit one partition; shard by hash/range across nodes; or replicate + route by collection. Most vector DBs expose partition keys or collections; plan for metadata routing and rebalancing. Sharding trades query fan-out for per-shard size.

**Jiuwen:** **No sharding or hash/range partitioning.** The only partition-like unit is the per-KB collection (`kb_{kb_id}_chunks`/`_triples`) plus the `database_name` field. There are no Milvus partition keys, shard config, or tenant-hash routing.

```mermaid
flowchart TD
    G["grow the index"] --> KB["per-KB collection (only unit of separation)"]
    G -.->|"absent"| SH["hash/range sharding · partition keys · tenant routing · rebalancing"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:102</code> — <code>kb_{kb_id}_chunks</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/common/config.py:79</code> — <code>database_name</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/milvus_store.py:512</code> — <code>delete_table</code>/drop granularity only</sub>

</details>

<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`; also covered in: rag-system._</sub>

---

## 6. Keeping retrieval fast as the vector database grows, without a full re-index

**General:** Append-only incremental indexing into a pre-built ANN index avoids full rebuilds; deletes/filters stay fast with scalar/inverted indexes; search-time parameters (efSearch, nprobe) tune the recall/latency dial without reindexing. At some point you need compaction/merge of segments and periodic index rebuilds — that is an operational concern, not a query-time one.

**Jiuwen:** Growth is handled by append-only batched writes into a pre-existing ANN index; existing vectors are untouched, so adding documents triggers no full re-index. Fast deletes/filters use the Milvus inverted scalar index on `document_id`/`chunk_id`. `get_search_params` derives `ef = top_k * efSearchFactor` per query (a search-time recall knob). `lazy_load` defers heavy module imports (Milvus/Chroma/parsers), not data. There is **no query result cache**, no reindex/compaction trigger, and no `ALTER INDEX` path — once the collection is created, ANN algorithm/params cannot change.

```mermaid
flowchart TD
    ADD["add_documents"] --> APP["append into existing ANN index (batched, no rebuild)"]
    ADD --> SC["scalar inverted index on document_id/chunk_id → fast delete/filter"]
    Q["query"] --> SP["get_search_params: ef = top_k × efSearchFactor (tune without reindex)"]
    APP -.->|"absent"| CACHE["no query cache · no compaction trigger · no ALTER INDEX"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/milvus_store.py:519</code> — <code>_ensure_loaded</code> lazy load; <code>:144</code> index_type change guard; <code>:117</code> <code>get_search_params</code> ef dial; <code>:199</code> flush after write<br>&bull; <code>agent-core/openjiuwen/core/retrieval/indexing/indexer/milvus_indexer.py:321</code> — <code>_ensure_collection</code> no-op if exists; <code>:346</code> inverted scalar indexes<br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/pg_store.py:157</code> — reflects existing table; <code>:203</code> index created once<br>&bull; <code>agent-core/openjiuwen/core/retrieval/lazy_load.py:143</code> — <code>lazy_load</code> (module imports)<br>&bull; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:74</code> — <code>add_documents</code> appends via <code>build_index</code></sub>

</details>

<sub>_Canonical source: `source/rag-retrieval-interview-questions_for_engineers.md`; also covered in: rag-retrieval._</sub>

---

## 7. What database would you choose for the vector store, and why that one over the alternatives

**General:** Choose by scale and features, not familiarity: local/embedded (FAISS/Chroma) for prototypes; a managed vector DB (Pinecone / Zilliz Cloud) for scale and hybrid search; or pgvector when you already run Postgres and want one datastore, transactions, and metadata joins. Evaluate hybrid support, filtering, operational cost, and lock-in.

**Jiuwen:** Three backends behind one factory: Chroma (local persisted, **vector-only** — sparse/hybrid rejected), Milvus (server, native BM25 + hybrid with RRF), PostgreSQL+pgvector (server, `tsvector` sparse + vector). The KB selects the index type (`hybrid` default). So hybrid/RRF requires Milvus or PG; Chroma is the small/local choice.

```mermaid
flowchart TD
    CFG["VectorStoreConfig"] --> F["create_vector_store(config)"]
    F --> CH["Chroma: local, vector-only (sparse/hybrid rejected)"]
    F --> MI["Milvus: server, native BM25 + hybrid RRF"]
    F --> PG["PGVector: server, tsvector sparse + vector"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/store.py:16</code> — factory dispatch; <code>agent-core/openjiuwen/core/retrieval/common/config.py:67</code> — <code>StoreType = Milvus | Chroma | PGVector</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/chroma_store.py:129</code> — <code>PersistentClient</code> (local); <code>agent-core/openjiuwen/core/retrieval/vector_store/milvus_store.py:108</code> — <code>MilvusClient(uri=...)</code> (server); <code>agent-core/openjiuwen/core/retrieval/vector_store/pg_store.py:108</code> — <code>create_async_engine(...)</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/knowledge_base.py:59</code> — Chroma rejects sparse/hybrid in local mode<br>&bull; <code>agent-core/openjiuwen/core/retrieval/common/config.py:32/60</code> — index types <code>hybrid</code>/<code>bm25</code>/<code>vector</code></sub>

</details>

<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`; also covered in: rag-system._</sub>

---

## 8. How do you decide between a hosted vector database and a self-managed one at scale

**General:** Hosted (Pinecone/Zilliz Cloud): less ops, elastic scaling, predictable latency, but cost scales with data/queries and there is vendor lock-in. Self-managed (Milvus/Qdrant/pgvector): control, cost at steady state, data residency, but you own scaling, backups, upgrades, and on-call. Decide by team ops capacity, data sensitivity, query volume, and elasticity needs — not by the library API.

**Jiuwen:** `create_vector_store` dispatches Chroma (local/embedded), Milvus (server, fits hosted or self-managed), and PostgreSQL+pgvector (self-managed relational). The choice is pure config; there is no autoscaling, managed-service integration, or ops tooling in-repo. Chroma local cannot do hybrid, so production hybrid means Milvus or PG.

```mermaid
flowchart TD
    D{"hosted vs self-managed"} --> LOCAL["Chroma: local/embedded (prototype, vector-only)"]
    D --> SRV["Milvus: server (hosted or self-managed), hybrid"]
    D --> PG["PGVector: self-managed relational"]
    D -.->|"in-repo"| X["no autoscaling · managed-service integration · ops tooling"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/store.py:16</code> — factory<br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/chroma_store.py:129</code> — local; <code>agent-core/openjiuwen/core/retrieval/vector_store/milvus_store.py:108</code> — server; <code>agent-core/openjiuwen/core/retrieval/vector_store/pg_store.py:108</code> — relational<br>&bull; <code>agent-core/openjiuwen/core/retrieval/knowledge_base.py:59</code> — Chroma rejects hybrid<br>&bull; <code>agent-core/openjiuwen/core/retrieval/common/config.py:67</code> — <code>StoreType</code></sub>

</details>



<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`; also covered in: rag-system._</sub>

---

## 9. What happens to the user experience if the vector database is down, what's your fallback

**General:** Decide the degradation: fail fast with a clear message, serve cached results, fall back to a secondary index (sparse/BM25 or a replica), or disable retrieval and answer from parametric knowledge with a caveat. Add a circuit breaker, health checks, and timeouts so one dependency cannot hang the request. Replicate the index so a single node is not a SPOF.

**Jiuwen:** There is **no availability fallback** for a down vector DB. Dense `search()` does not catch exceptions — a store failure propagates through the retriever and fails the workflow node. Sparse searches silently return `[]` on error, Milvus hybrid has a same-DB split-search fallback, and `retrieve_multi_kb` swallows per-KB errors (empty list), which contains blast radius across KBs. There is no circuit breaker, health probe, or result cache.

```mermaid
flowchart TD
    DB["vector DB down"] --> DENSE["dense search: exception propagates → node fails"]
    DB --> SPARSE["sparse search: swallows → []"]
    DB --> HYB["Milvus hybrid: same-DB split-search fallback"]
    DB --> MK["multi-KB: per-KB errors swallowed (contained)"]
    DB -.->|"absent"| X["circuit breaker · health probe · replica · cache fallback"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/milvus_store.py:357</code> — <code>hybrid_search</code> → <code>_hybrid_search_fallback</code>; <code>:284</code> <code>sparse_search</code> returns <code>[]</code>; <code>:519</code> <code>_ensure_loaded</code> timeouts<br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/chroma_store.py:326</code> — sparse/text returns <code>[]</code> on error<br>&bull; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:300</code> — <code>retrieve_multi_kb</code> swallows per-KB errors<br>&bull; <code>agent-core/openjiuwen/core/workflow/components/resource/knowledge_retrieval_comp.py:123</code> — re-raises <code>build_error</code></sub>

</details>

<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`; also covered in: rag-system._</sub>

---

## 10. Handling a document updated or deleted after it's already indexed

**General:** You need a stable document id and a delete-by-id path; updates are delete-then-insert (or upsert). Chunk ids must be derived from the document id so all chunks of a document can be found and removed atomically. The hard parts are atomicity (a crash between delete and reinsert loses the doc) and eventual consistency in the vector store.

**Jiuwen:** The contract is delete-by-`doc_id` + rebuild. Chroma/Milvus indexers do **not** upsert: they scan a doc's chunk IDs, delete them, then re-chunk/re-embed/write (Milvus flushes between to defeat eventual consistency). `doc_id` is a first-class field (`document_id`, scalar-inverted in Milvus) enabling filter deletes. PG is the only store with native upsert-by-primary-key (`INSERT ... ON CONFLICT (id) DO UPDATE`), but no PG indexer wraps it. There is no atomic/transactional replace — a crash between delete and rebuild loses the document, and chunk IDs are regenerated UUIDs each run so "same document" relies solely on `doc_id`.

```mermaid
flowchart TD
    UP["update_documents(doc_id)"] --> DEL["delete_index(doc_id): filter delete all chunks"]
    DEL --> FL["Milvus flush (consistency) between delete and rebuild"]
    FL --> RE["re-chunk + re-embed + build_index"]
    DEL -.->|"crash here"| LOSS["document lost (no transaction)"]
    PG["PG store: INSERT ... ON CONFLICT DO UPDATE (upsert)"] -.->|"no PG indexer wraps it"| X["unused upsert path"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/knowledge_base.py:176/184</code> — abstract <code>delete_documents</code> / <code>update_documents</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:192</code> — <code>delete_documents</code>; <code>:219</code> <code>update_documents</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/indexing/indexer/chroma_indexer.py:198</code> — <code>update_index</code> = delete + build; <code>:217</code> delete by <code>doc_id</code>; <code>:142</code> duplicate guard<br>&bull; <code>agent-core/openjiuwen/core/retrieval/indexing/indexer/milvus_indexer.py:209</code> — delete + flush + rebuild; <code>:231</code> filter delete <code>document_id == doc_id</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/vector_store/pg_store.py:300</code> — <code>INSERT ... ON CONFLICT DO UPDATE</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/graph_knowledge_base.py:253</code> — delete chunk + triple index; <code>:294</code> update = delete + re-add</sub>

</details>

<sub>_Canonical source: `source/rag-retrieval-interview-questions_for_engineers.md`; also covered in: rag-1, rag-practical, rag-retrieval, rag-system._</sub>

---

## 11. How would you design the system so users never get an answer based on stale, outdated information

**General:** Attach timestamps/versions to documents, prefer recency in ranking (or hard-filter to a freshness window), tombstone superseded versions, and surface recency to the generator. Propagate deletes promptly from the source (event-driven) so the index matches source-of-truth, and reconcile periodically.

**Jiuwen:** The retrieval layer has **no notion of document time**: `RetrievalResult`/`TextChunk` carry only text/score/metadata, parsers populate no timestamp, and ranking is score/rank only (RRF, max-score) — no recency boost or outdated filter. Conflict handling is memory-write-only (`MemUpdateChecker`, newest wins); a freshness/time-decay notion exists only for experience records.

```mermaid
flowchart TD
    R["retrieved chunks (no timestamp)"] --> M["RRF / max-score only"]
    M --> GEN["answer (staleness left to the model)"]
    R -.->|"absent"| X["recency boost · freshness window · tombstoning · source reconciliation"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/common/retrieval_result.py:23</code> — no timestamp field; <code>agent-core/openjiuwen/core/retrieval/common/document.py:30</code> — <code>TextChunk</code><br>&bull; <code>agent-core/openjiuwen/core/retrieval/utils/fusion.py:39</code> — RRF by text/rank; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:313</code> — max-score merge<br>&bull; <code>agent-core/openjiuwen/core/memory/manage/update/mem_update_checker.py:22/252</code> — memory-only conflict (newest wins)<br>&bull; <code>agent-core/openjiuwen/agent_evolving/experience/scorer.py:219</code> — <code>calc_freshness</code> (experiences only)</sub>

</details>

<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`; also covered in: rag-system._</sub>

---

## 12. How do you design for the case where retrieval returns zero relevant documents

**General:** Detect it (score threshold or answerability) and abstain: return "I don't have enough information" or ask a clarifying question, rather than answering from noise. Optionally fall back to a broader retrieval (sparse), a knowledge-graph hop, or parametric knowledge with a caveat. Log zero-result queries — they signal coverage gaps.

**Jiuwen:** The KB path implements **dense-empty → sparse** fallback, but has **no abstention**: when both are empty it returns `[]` and the workflow component concatenates an empty context with no "no answer" signal. Explicit abstention (`is_abstain`, `abstain_no_backfill`) exists only in the separate Symphony progressive-retrieval engine, not in `core/retrieval` KB retrieval. `score_threshold` defaults to `None`.

```mermaid
flowchart TD
    R["retrieval"] --> E{"dense empty?"}
    E -->|yes| SP["sparse fallback"]
    E -->|no| OK["return"]
    SP --> Z{"still empty?"}
    Z -->|yes| EMPTY["[] + empty context (no abstention)"]
    Z -->|no| OK
    EMPTY -.->|"absent in KB path"| ABS["'not enough information' / clarify (Symphony only)"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/retrieval/retriever/vector_retriever.py:83</code> — dense-empty → sparse; <code>agent-core/openjiuwen/core/retrieval/retriever/hybrid_retriever.py:97</code> — same<br>&bull; <code>agent-core/openjiuwen/core/workflow/components/resource/knowledge_retrieval_comp.py:241</code> — empty results → empty context<br>&bull; <code>agent-core/openjiuwen/core/retrieval/common/config.py:47</code> — <code>score_threshold</code> defaults <code>None</code><br>&bull; <code>agent-core/openjiuwen/symphony/retrieval/search/runtime/selector.py:305</code> — <code>is_abstain</code>; <code>agent-core/openjiuwen/symphony/retrieval/search/runtime/engine.py:94</code>; <code>agent-core/openjiuwen/symphony/retrieval/search/runtime/progressive.py:1060</code> — <code>abstain_no_backfill</code></sub>

</details>

<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`; also covered in: rag-system._</sub>

---

## 13. Your system needs sub-500ms responses, walk me through where you'd spend that budget across retrieval, reranking, and generation

**General:** Budget roughly: embedding + vector search tens of ms, rerank tens–low-hundreds of ms, generation the rest (and generation dominates when you stream, because TTFT is what the user perceives). To hit 500ms: stream tokens, cache embeddings/results, keep top-k small, rerank only when it pays, route to a fast model, and parallelize independent steps. Measure TTFT, not total.

**Jiuwen:** Provides streaming (ReAct → session → WebSocket frames) with per-call `ttft_ms`, parallel tool execution with resource lanes, KV/prefix cache affinity, a model backup/failover rail, and IntelliRouter for deployment selection. Reranking is **optional and absent from the default KB path** (graph store only), so the rerank budget is not spent unless wired. There is no latency/SLA-based routing or result cache.

```mermaid
flowchart LR
    B["500ms budget"] --> E["embed + search: tens of ms"]
    B --> R["rerank: optional (not in KB path)"]
    B --> G["generation: stream → TTFT dominates"]
    G --> L["streaming · parallel tools · KV/prefix cache · model routing/backup"]
    L -.->|"absent"| X["latency/SLA routing · result cache"]
```

<details>
<summary>Anchors</summary>

<sub><strong>Anchors:</strong><br>&bull; <code>agent-core/openjiuwen/core/single_agent/agents/react_agent.py:336</code> — <code>parallel_tool_calls</code>; <code>:1758</code> <code>ttft_ms</code>; <code>:2938</code> <code>stream</code><br>&bull; <code>agent-core/openjiuwen/core/single_agent/ability_manager.py:431/467</code> — parallel batches + <code>parallel_safe</code> lanes<br>&bull; <code>agent-core/openjiuwen/core/single_agent/rail/model_backup.py:9</code> — <code>ModelBackupRail.on_model_exception</code> failover<br>&bull; <code>jiuwenswarm/jiuwenswarm/server/runtime/session/kv_cache/kv_cache_model_provider.py:80</code> — KV/prefix affinity<br>&bull; <code>agent-core/openjiuwen/core/retrieval/simple_knowledge_base.py:182</code> — KB path calls no reranker</sub>

</details>

<sub>_Canonical source: `source/rag-system-design-interview-questions_for_engineers.md`; also covered in: rag-system._</sub>
