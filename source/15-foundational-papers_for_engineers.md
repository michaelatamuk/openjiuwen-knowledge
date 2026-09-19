# 15 Papers Every Generative AI Engineer Should Know

> **The pattern worth noticing:** Understanding the papers behind your daily tools changes how you debug, finetune, and design systems — not just how you call an API.

---

## 1. Attention Is All You Need (Vaswani, 2017)

**Core contribution:** The Transformer architecture — self-attention replaces RNNs/CNNs for sequence modeling. Multi-head attention, positional encoding, and the encoder-decoder structure become the foundation for BERT, GPT, T5, and all subsequent LLMs.

**Coverage map:** Covered by 01-4 (self-attention), 01-5 (positional encoding), 01-6 (encoder/decoder types), 00-18 (why multi-head attention).

---

## 2. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding (Devlin, 2018)

**Core contribution:** Masked language modeling (MLM) as a pretraining objective enables bidirectional context. The pretrain-then-finetune paradigm: one large pretrained model + thin task head + small labeled dataset, replacing per-task training.

**General:** MLM randomly masks 15% of input tokens and trains the model to predict them — forcing bidirectional context unlike GPT's left-to-right objective. The pretrain-then-finetune template became the foundation of modern NLP transfer learning.

**Jiuwen:** BERT-family models appear as frozen embedding encoders and finetuned classifiers (`AutoModelForSequenceClassification` in `guardrail_rail.py`).

**Gap.** No finetune path for encoder-based models in the KB pipeline; SFT in `agent_rl/` covers decoder-only generation only.

**Coverage map:** **New entry 01-17.**

---

## 3. Language Models are Few-Shot Learners — GPT-3 (Brown, 2020)

**Core contribution:** In-context learning (ICL) — performing new tasks from prompt examples without weight update — emerges at scale. At 175B parameters, few-shot performance approaches fine-tuned baselines on many benchmarks.

**General:** Scale enables a model to recognize task patterns from prefix sequences and apply them at inference time. This changed the practitioner interface from fine-tuning to prompting.

**Jiuwen:** `RuntimePromptRail` and `PromptTemplate` are the ICL interface at inference time. No retrieval-augmented ICL (no similar-demonstration selection per query).

**Coverage map:** **New entry 01-18.**

---

## 4. Training Compute-Optimal Large Language Models — Chinchilla (Hoffmann, 2022)

**Core contribution:** Compute-optimal training is ~20 tokens per parameter. Most large models (GPT-3, Gopher) were undertrained — too many parameters for the data seen. Chinchilla (70B, 1.4T tokens) outperforms Gopher (280B) with 4× fewer parameters.

**General:** For a fixed compute budget, scale model size and training tokens equally. Data matters as much as parameters. Smaller model + more data outperforms larger model + less data.

**Jiuwen:** Pretraining out of scope; Chinchilla-aware base model selection is an operator-level decision with no framework tooling.

**Coverage map:** **New entry 01-19.**

---

## 5. Training Language Models to Follow Instructions with Human Feedback — InstructGPT (Ouyang, 2022)

**Core contribution:** RLHF pipeline for alignment: SFT on demonstrations → reward model trained on human preferences → PPO to maximize reward. The paper behind ChatGPT's instruction-following.

**Coverage map:** Covered by 17-8 (RLHF vs DPO).

---

## 6. Direct Preference Optimization: Your Language Model is Secretly a Reward Model (Rafailov, 2023)

**Core contribution:** DPO eliminates the separate reward model and RL loop from RLHF. Given (prompt, chosen, rejected) preference pairs, DPO directly optimizes the policy via a weighted cross-entropy loss — simpler, more stable, equivalent alignment.

**Coverage map:** Covered by 17-8 (RLHF vs DPO).

---

## 7. LoRA: Low-Rank Adaptation of Large Language Models (Hu, 2021)

**Core contribution:** Freeze all pretrained weights; inject two small trainable matrices A and B at each target layer (ΔW = BA, rank r ≪ hidden dim). <1% trainable parameters; multiple adapters can share one base model.

**Coverage map:** Covered by 17-7 (LoRA dedicated entry).

---

## 8. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis, 2020)

**Core contribution:** Foundational RAG paper. Ground generation in a retrieved knowledge base — combine a dense retriever (DPR) with a seq2seq generator — instead of relying purely on parametric memory.

**Coverage map:** Covered by topic 10 (RAG pipelines and patterns).

---

## 9. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models (Wei, 2022)

**Core contribution:** Including step-by-step reasoning examples in the prompt (chain-of-thought few-shot) significantly improves performance on multi-step arithmetic, commonsense, and symbolic reasoning tasks.

**Coverage map:** Covered by 02-2 (zero-shot vs. few-shot vs. chain-of-thought).

---

## 10. ReAct: Synergizing Reasoning and Acting in Language Models (Yao, 2022)

**Core contribution:** Interleave reasoning traces (Think) with tool calls (Act) and observations in the prompt. This enables dynamic planning, error correction, and grounded retrieval within an agent loop.

**Coverage map:** Covered by 05-4 (ReAct pattern) and 05-5 (why interleave reasoning and actions).

---

## 11. Denoising Diffusion Probabilistic Models (Ho, 2020)

**Core contribution:** Forward process adds Gaussian noise over T steps; U-Net trained to reverse it one step at a time. Stable supervised objective; enables high-quality image generation. Foundation for Stable Diffusion, DALL-E 2.

**General:** Inference: start from pure noise, run reverse T steps → generated image. Latent Diffusion Models (Stable Diffusion) compress to a VAE latent space for ~8× compute reduction. Quality levers: steps, guidance scale, scheduler.

**Jiuwen:** No diffusion integration; image generation tools appear as external `ToolCard` calls.

**Coverage map:** **New entry 01-23.**

---

## 12. Learning Transferable Visual Models From Natural Language Supervision — CLIP (Radford, 2021)

**Core contribution:** Joint image-text pretraining via contrastive learning on 400M pairs creates a shared embedding space. Enables zero-shot image classification, text-to-image retrieval, and multimodal RAG.

**General:** Text and image encoders trained together; cosine similarity between text and image embeddings is semantically meaningful. Underpins DALL-E 2 and Stable Diffusion text conditioning.

**Jiuwen:** Embedding pipeline is text-only; CLIP-based cross-modal retrieval is absent. `MultimodalImageRail` routes images to generation, not to an embedding index.

**Coverage map:** **New entry 01-22.**

---

## 13. FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness (Dao, 2022)

**Core contribution:** Tiled attention computation that stays in SRAM — never materializes the full NxN attention matrix in HBM. O(N) memory, 2–4× faster, enables practical long-context (32k–1M token) training and inference.

**General:** Standard attention is O(N²) in memory. FlashAttention removes this constraint. Used by default in modern LLMs and serving frameworks (vLLM, TRT-LLM).

**Jiuwen:** Infrastructure concern handled by vLLM at the serving layer. Jiuwen manages long context at the application level (offloading at 50k, compaction at 180k).

**Coverage map:** **New entry 01-20.**

---

## 14. Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity (Fedus, 2021)

**Core contribution:** Mixture of Experts with single-expert routing (k=1) scales model capacity without proportional FLOPs. 1.6T-parameter model at ~same compute as dense 7B; 4× speedup over T5-XXL.

**General:** MoE: N expert FFN layers + router activates k per token → total params = N×k, FLOPs ≈ k-expert dense. Practitioner implication: total parameter count overstates compute cost for MoE models.

**Jiuwen:** Model architecture opaque to framework; no MoE-aware routing, expert metadata, or active-parameter tracking.

**Coverage map:** **New entry 01-21.**

---

## 15. Constitutional AI: Harmlessness from AI Feedback (Bai, 2022)

**Core contribution:** Replace most human preference labeling with model self-critique against explicit principles (the "constitution"). SL-CAI: generate → critique → revise → SFT. RL-CAI: model-generated preference pairs → reward model → RLHF. Far fewer human labels; auditable principle list.

**General:** The constitution is an explicit, versioned list of principles — easier to update than a latent reward model. Claude's alignment is based on CAI.

**Jiuwen:** Safety uses static classifiers (`SecurityRail`, `GuardrailRail`, `GuardianRail`); no self-critique loop, no constitution file.

**Coverage map:** **New entry 18-12.**

---

## Coverage summary

| Paper | Year | New KB entry |
|---|---|---|
| Attention Is All You Need | 2017 | No (covered: 01-4, 01-5, 01-6, 00-18) |
| BERT | 2018 | **01-17** |
| GPT-3 | 2020 | **01-18** |
| Chinchilla | 2022 | **01-19** |
| InstructGPT | 2022 | No (covered: 17-8) |
| DPO | 2023 | No (covered: 17-8) |
| LoRA | 2021 | No (covered: 17-7) |
| RAG (Lewis) | 2020 | No (covered: topic 10) |
| Chain-of-Thought | 2022 | No (covered: 02-2) |
| ReAct | 2022 | No (covered: 05-4, 05-5) |
| DDPM | 2020 | **01-23** |
| CLIP | 2021 | **01-22** |
| FlashAttention | 2022 | **01-20** |
| Switch Transformers | 2021 | **01-21** |
| Constitutional AI | 2022 | **18-12** |
