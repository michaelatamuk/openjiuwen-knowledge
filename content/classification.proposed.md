# Classification — DRAFT for review

Difficulty labels from a heuristic first pass. See `content/classification.md` for the rubric.


## 01 · Model foundations

| id | difficulty | question |
|---|---|---|
| 01-1 | intermediate | What's the difference between a token and a word, and why does tokenization affect cost and context limits |
| 01-2 | foundational | What is the difference between tokens and embeddings? |
| 01-3 | intermediate | Explain how self-attention works in a transformer |
| 01-4 | foundational | What is positional encoding, and why do transformers need it if attention has no inherent sense of order |
| 01-5 | foundational | What's the difference between an encoder-only, decoder-only, and encoder-decoder model, and where does GPT fit |
| 01-6 | foundational | What's the difference between a model's context window and its training data cutoff |
| 01-7 | intermediate | What happens when a conversation exceeds the model's context window |
| 01-8 | foundational | Why does model performance sometimes degrade with very long context, even when the context fits |
| 01-9 | foundational | What does temperature actually control, mathematically, in the output distribution |
| 01-10 | foundational | What's the difference between top-k sampling and top-p (nucleus) sampling |
| 01-11 | foundational | Why does greedy decoding sometimes produce worse output than sampling-based decoding |
| 01-12 | intermediate | Why do LLMs struggle with tasks like counting or basic arithmetic |
| 01-13 | foundational | What is hallucination, and why does it happen even in a well-trained model |
| 01-14 | foundational | What's the difference between the model being "wrong" and the model being "uncertain," and can you tell the difference from the output alone |
| 01-15 | intermediate | "How does the model know X" is really testing context window understanding |

## 02 · Model foundations

| id | difficulty | question |
|---|---|---|
| 02-1 | foundational | What's the difference between a system prompt and a user prompt |
| 02-2 | intermediate | Zero-shot vs. few-shot vs. chain-of-thought, when does each actually improve output |
| 02-3 | intermediate | How do you get consistent, parseable output like JSON from an LLM |
| 02-4 | intermediate | How does the framework validate a tool call's structured output before executing it |
| 02-5 | intermediate | How do you version prompts the same way you'd version code |
| 02-6 | intermediate | Any prompt behavior question is secretly a versioning and testing question |

## 03 · Model foundations

| id | difficulty | question |
|---|---|---|
| 03-1 | foundational | Token |
| 03-2 | foundational | Embedding |
| 03-3 | foundational | Context window |
| 03-4 | foundational | Temperature |
| 03-5 | foundational | Top-p (nucleus sampling) |
| 03-6 | foundational | RAG |
| 03-7 | foundational | Chunking |
| 03-8 | foundational | Vector database |
| 03-9 | foundational | Reranking |
| 03-10 | foundational | Hallucination |
| 03-11 | foundational | Fine-tuning |
| 03-12 | foundational | Prompt engineering |
| 03-13 | foundational | Few-shot prompting |
| 03-14 | foundational | Chain-of-thought prompting |
| 03-15 | foundational | Function calling |
| 03-16 | foundational | Agent |
| 03-17 | foundational | Memory |
| 03-18 | foundational | Latency |
| 03-19 | foundational | Quantization |
| 03-20 | foundational | Prompt injection |

## 04 · Model foundations

| id | difficulty | question |
|---|---|---|
| 04-1 | intermediate | Deciding when a problem actually needs an LLM versus a simpler rule-based system |
| 04-2 | intermediate | Larger model vs. smaller, faster one for a given task |
| 04-3 | advanced | "Compare two approaches" tests tradeoff reasoning tied to numbers, not a correct pick |

## 05 · Agents

| id | difficulty | question |
|---|---|---|
| 05-1 | foundational | What's the difference between a chatbot and an agent |
| 05-2 | foundational | What's the difference between a workflow and an agent |
| 05-3 | foundational | What's the difference between a linear chain and a graph with conditional branches |
| 05-4 | foundational | What's the ReAct pattern, and why interleave reasoning with actions instead of planning everything upfront |
| 05-5 | intermediate | How do you set a hard limit on iterations or steps within a framework |
| 05-6 | intermediate | What decides when an agent stops and returns a final answer instead of calling another tool |
| 05-7 | intermediate | How do you decide how many retrieval hops are enough, and how do you prevent the system from looping indefinitely |
| 05-8 | intermediate | Preventing an agent from getting stuck in an infinite tool-calling loop |
| 05-9 | intermediate | How does an agent decide when to retrieve again versus when it has enough context to answer |
| 05-10 | intermediate | "The agent is stuck" tests whether you've shipped one, not studied one |
| 05-11 | intermediate | "The agent is stuck in a loop" is testing production experience |

## 06 · Agents

| id | difficulty | question |
|---|---|---|
| 06-1 | intermediate | How does function calling actually work under the hood |
| 06-2 | intermediate | How does a framework register and expose tools to the underlying model |
| 06-3 | intermediate | How do you handle a tool that a framework doesn't natively support |
| 06-4 | intermediate | How do you handle a tool call that fails or returns malformed output |
| 06-5 | intermediate | Designing retry logic that doesn't cause duplicate side effects on a tool call |
| 06-6 | advanced | How would you add a custom retry policy for a specific tool without breaking the framework's default behavior |
| 06-7 | intermediate | Handling concurrent API calls when an agent needs to call multiple tools at once |
| 06-8 | intermediate | How does the framework handle a step that times out or throws an error |
| 06-9 | intermediate | Controlling cost when an agent can call tools repeatedly |
| 06-10 | intermediate | Agentic tool-calling pattern |

## 07 · Agents

| id | difficulty | question |
|---|---|---|
| 07-1 | intermediate | How does an agent break a complex task into smaller subtasks |
| 07-2 | intermediate | How do you handle a task where the plan needs to change mid-execution based on a tool's result |
| 07-3 | foundational | What's the difference between a single-step agent and a multi-step planning agent |
| 07-4 | foundational | What's the planner-executor pattern, and when do you need it |
| 07-5 | intermediate | How does a framework track state across multiple steps in an agent's execution |
| 07-6 | advanced | How would you pause an agent mid-execution and resume it later with the same state |
| 07-7 | advanced | How would you add human-in-the-loop approval before a specific step executes |
| 07-8 | foundational | What's the difference between short-term and long-term memory in an agent |
| 07-9 | intermediate | How do you decide what to store in memory versus what to discard |
| 07-10 | intermediate | How do you prevent memory from growing unbounded across a long session |
| 07-11 | advanced | How would you summarize conversation history without losing important details |
| 07-12 | intermediate | Planner–executor pattern |
| 07-13 | intermediate | Critic or reflection loop |
| 07-14 | intermediate | Memory-augmented agent |
| 07-15 | intermediate | Router pattern |

## 08 · Agents

| id | difficulty | question |
|---|---|---|
| 08-1 | foundational | What does an agent framework actually give you that raw API calls don't |
| 08-2 | foundational | What's the difference between a graph-based framework like LangGraph and a role-based framework like CrewAI |
| 08-3 | intermediate | How do you decide between LangGraph, CrewAI, and the Anthropic Agent SDK for a given project |
| 08-4 | advanced | What tradeoffs come with choosing a heavier framework versus writing a lighter custom orchestration layer |
| 08-5 | intermediate | When does a framework add unnecessary abstraction instead of solving a real problem |
| 08-6 | intermediate | What happens when the framework's abstractions don't match how your actual business logic needs to work |
| 08-7 | intermediate | How does the framework decide which node or agent runs next |
| 08-8 | intermediate | How do you version and roll back an agent's workflow definition, not just its prompts |
| 08-9 | advanced | How do you evaluate whether a framework will scale with your team, not just your first prototype |

## 09 · Agents

| id | difficulty | question |
|---|---|---|
| 09-1 | foundational | What's the difference between a supervisor pattern and a peer-to-peer pattern in these frameworks |
| 09-2 | intermediate | How does a framework handle communication between multiple agents |
| 09-3 | intermediate | How does the framework handle one agent's output becoming another agent's input |
| 09-4 | intermediate | How do you prevent multiple agents from producing conflicting or redundant results |
| 09-5 | advanced | How do you debug a failure when it's unclear which agent in the chain caused it |
| 09-6 | advanced | When is a multi-agent system overkill compared to a single well-designed agent |

## 10 · RAG

| id | difficulty | question |
|---|---|---|
| 10-1 | intermediate | Walking through a RAG pipeline end to end, query to final answer |
| 10-2 | intermediate | The pipeline: query embedding, vector search, context assembly, prompt construction, generation |
| 10-3 | foundational | What is Modular RAG, and how is it different from a simple RAG pipeline |
| 10-4 | intermediate | Deciding chunk size, and what breaks at each extreme |
| 10-5 | intermediate | What happens if your chunks are too small or too large |
| 10-6 | advanced | Fixed-size vs. semantic chunking, the actual retrieval tradeoff |
| 10-7 | intermediate | Overlapping vs. non-overlapping chunks |
| 10-8 | intermediate | Chunking structured content like tables, code, or nested headings without losing structure |
| 10-9 | intermediate | Context relevant but answer vague: chunk boundaries likely cut the answer mid context |
| 10-10 | intermediate | Picking an embedding model, and whether bigger always means better retrieval |
| 10-11 | intermediate | Should queries and documents use the same embedding model |
| 10-12 | intermediate | Why swapping embedding models forces a full re-embedding of the corpus |
| 10-13 | intermediate | Multilingual documents: multilingual embedding models, translate at query or index time |
| 10-14 | intermediate | Handling multiple document types and formats in the same system |
| 10-15 | intermediate | RAG vs. pasting retrieved text into a long-context prompt |
| 10-16 | intermediate | Simple RAG pipeline |
| 10-17 | intermediate | Modular RAG with reranking |
| 10-18 | foundational | What is agentic RAG, and how is it different from a standard fixed RAG pipeline |
| 10-19 | advanced | How would you prevent an agentic RAG system from retrieving in an unnecessary loop and burning cost |

## 11 · RAG

| id | difficulty | question |
|---|---|---|
| 11-1 | intermediate | Dense vs. sparse retrieval, and fusing both with reciprocal rank fusion |
| 11-2 | intermediate | When keyword search outperforms semantic search |
| 11-3 | intermediate | Why a purely semantic system can fail on queries with exact codes, IDs, or names |
| 11-4 | intermediate | How do you decide between retrieving 5 documents versus 20 |
| 11-5 | advanced | How would you design retrieval to work across structured data (SQL tables) and unstructured data (documents) in the same system |
| 11-6 | intermediate | What reranking adds that initial retrieval doesn't already do |
| 11-7 | intermediate | How do you know if your reranker is actually improving results, or just reordering noise, without an A/B test |
| 11-8 | intermediate | Would you rerank every query, or only some, and how do you decide |
| 11-9 | intermediate | How much latency reranking adds, and deciding if it's worth it |
| 11-10 | intermediate | Bi-encoder for retrieval vs. cross-encoder for reranking |
| 11-11 | intermediate | Cutting tokens without losing quality: tighter reranking, summarizing long chunks |

## 12 · RAG

| id | difficulty | question |
|---|---|---|
| 12-1 | foundational | What is query rewriting or query expansion, and when does it meaningfully improve retrieval quality |
| 12-2 | advanced | How would you handle a vague or ambiguous user query before it even reaches retrieval |
| 12-3 | advanced | How would you decompose a complex, multi-part question into smaller retrievable sub-questions |
| 12-4 | foundational | What is multi-hop retrieval, and when does single-pass retrieval fail to answer a question |
| 12-5 | intermediate | Handling a question requiring information from multiple documents |
| 12-6 | intermediate | When to skip RAG and rely on parametric knowledge instead |

## 13 · RAG

| id | difficulty | question |
|---|---|---|
| 13-1 | intermediate | How do you measure whether your retrieval step is actually working |
| 13-2 | intermediate | Retrieval looks correct, answer is wrong: check if the chunk actually contains the answer |
| 13-3 | intermediate | How do you handle hallucinations when retrieved context doesn't actually answer the question |
| 13-4 | intermediate | How do you handle retrieval when documents contain conflicting or outdated information on the same topic |
| 13-5 | intermediate | No relevant documents exist: expected behavior is a confidence-gated "not enough information" |
| 13-6 | intermediate | Same question, different answers on different days: non-deterministic reranking or embedding drift |
| 13-7 | intermediate | Vocabulary mismatch, where the answer exists but uses different wording |
| 13-8 | intermediate | Structuring error handling for a pipeline where retrieval, reranking, or generation can each fail independently |
| 13-9 | advanced | Building a retrieval eval set without labeled relevant documents yet |
| 13-10 | advanced | "Design a RAG system" tests failure mode awareness, not architecture recall |
| 13-11 | intermediate | "The model made something up" is testing hallucination handling, not model quality |

## 14 · RAG

| id | difficulty | question |
|---|---|---|
| 14-1 | advanced | Design a RAG system for a customer support chatbot handling 100,000 queries a day |
| 14-2 | advanced | Design a RAG pipeline for a codebase assistant that needs to stay current as code changes daily |
| 14-3 | advanced | Design a document search system for a legal firm with millions of confidential documents |
| 14-4 | intermediate | How retrieval architecture changes from 10,000 to 10 million documents |
| 14-5 | advanced | How do you shard or partition a vector database as it grows |
| 14-6 | intermediate | Keeping retrieval fast as the vector database grows, without a full re-index |
| 14-7 | intermediate | What database would you choose for the vector store, and why that one over the alternatives |
| 14-8 | advanced | How do you decide between a hosted vector database and a self-managed one at scale |
| 14-9 | intermediate | What happens to the user experience if the vector database is down, what's your fallback |
| 14-10 | intermediate | Handling a document updated or deleted after it's already indexed |
| 14-11 | advanced | How would you design the system so users never get an answer based on stale, outdated information |
| 14-12 | advanced | How do you design for the case where retrieval returns zero relevant documents |
| 14-13 | advanced | Your system needs sub-500ms responses, walk me through where you'd spend that budget across retrieval, reranking, and generation |

## 15 · Evaluation & production

| id | difficulty | question |
|---|---|---|
| 15-1 | intermediate | How do you evaluate an LLM's output beyond "it looks correct" |
| 15-2 | intermediate | Why evaluate retrieval and generation as two separate stages instead of one end-to-end score |
| 15-3 | intermediate | Why exact-match scoring fails when a correct answer can be phrased multiple valid ways |
| 15-4 | advanced | Recall@k, and what a low score tells you about your retrieval setup |
| 15-5 | intermediate | Precision@k = relevant docs in top k / k — how it differs from Recall@k, and why both can be low even when the pipeline "looks" fine |
| 15-6 | intermediate | MRR, and when it matters more than Recall@k |
| 15-7 | intermediate | NDCG: weights relevant results by position against an ideal ranking — why position matters beyond "was it retrieved" |
| 15-8 | intermediate | Faithfulness vs. relevance in RAG evaluation |
| 15-9 | intermediate | Computing faithfulness: decomposing an answer into atomic claims, scoring each against the source with an NLI model or LLM-as-judge |
| 15-10 | intermediate | Measuring hallucination rate: claim extraction from the output, then verification against retrieved context |
| 15-11 | foundational | What is perplexity, and what does a lower score actually tell you |
| 15-12 | intermediate | Known limitations of using an LLM as a judge |
| 15-13 | intermediate | How do you evaluate when there's no ground truth answer, only a query and a corpus |
| 15-14 | advanced | How would you build an eval dataset from scratch if you don't have one yet |
| 15-15 | intermediate | How many examples before eval results are statistically meaningful, not just noise |
| 15-16 | advanced | How would you compare two models for a specific task, not just a general leaderboard score |
| 15-17 | intermediate | Building a regression test suite to catch a quality drop before it ships |
| 15-18 | intermediate | Evaluating continuously in production, not just once before launch |
| 15-19 | intermediate | How do you detect when your retrieval quality has degraded over time |
| 15-20 | advanced | High eval scores but users still complaining — what does that gap tell you about your eval set |
| 15-21 | intermediate | Tying an eval metric back to a business outcome a stakeholder actually cares about |
| 15-22 | intermediate | "How do you know it's working" tests evaluation depth, not confidence |
| 15-23 | intermediate | "How do you know it's working" is testing evaluation depth |

## 16 · Evaluation & production

| id | difficulty | question |
|---|---|---|
| 16-1 | advanced | Where cost concentrates: embedding is cheap and one-time, generation scales with traffic |
| 16-2 | advanced | How would you reduce cost for a high-volume RAG system without degrading answer quality |
| 16-3 | advanced | How do you control cost in a system where usage scales unpredictably |
| 16-4 | intermediate | First cut at 50% cost reduction: route simple queries to a smaller model, reduce top-k |
| 16-5 | intermediate | Designing caching for repeated or semantically similar queries |
| 16-6 | intermediate | Reducing latency in a multi-step LLM pipeline |
| 16-7 | intermediate | Multithreading vs. multiprocessing, which matters more for I/O-bound LLM API calls |
| 16-8 | advanced | What happens to your architecture at 10x current traffic |
| 16-9 | intermediate | Scaling questions test whether you've thought past the demo |
| 16-10 | advanced | What's your rollback plan if a prompt or model update degrades output quality? |
| 16-11 | intermediate | A stakeholder wants to ship before your eval scores are ready, how do you handle it |

## 17 · Model adaptation

| id | difficulty | question |
|---|---|---|
| 17-1 | foundational | What's the difference between pretraining and fine-tuning |
| 17-2 | foundational | What is instruction tuning, and how is it different from base model pretraining |
| 17-3 | foundational | What's the difference between full fine-tuning and parameter-efficient fine-tuning like LoRA |
| 17-4 | intermediate | When would you fine-tune instead of using a longer, more detailed prompt |
| 17-5 | foundational | What's the difference between RAG and fine-tuning, and when would you use each |
| 17-6 | foundational | What's the risk of fine-tuning on a small, narrow dataset |

## 18 · Safety & security

| id | difficulty | question |
|---|---|---|
| 18-1 | intermediate | What prompt injection is, and how you'd defend against it |
| 18-2 | intermediate | Handling untrusted content from a tool result or retrieved document |
| 18-3 | intermediate | How do you handle a user trying to jailbreak your system's guardrails |
| 18-4 | intermediate | How do you make sure a user only retrieves documents they're actually authorized to see |
| 18-5 | intermediate | How do you prevent an agent from taking a destructive or irreversible action by mistake |
| 18-6 | intermediate | How do you prevent a model from generating harmful or biased content |
| 18-7 | intermediate | Preventing sensitive data from leaking into a model's context or output logs |
| 18-8 | advanced | Design a multi-tenant RAG system where each customer's data must stay isolated from others |
| 18-9 | intermediate | Security-adjacent questions are disguised as normal engineering questions |
| 18-10 | intermediate | Any question about untrusted input is testing prompt injection awareness |
