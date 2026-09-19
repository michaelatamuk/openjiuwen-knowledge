<div class="topic-nav">
<a class="topic-nav__link topic-nav__prev" href="01-llm-foundations.html"><span class="topic-nav__dir">← Previous</span><span class="topic-nav__name">How LLMs work</span></a>
<a class="topic-nav__link topic-nav__next" href="20-ai-system-stack.html"><span class="topic-nav__dir">Next →</span><span class="topic-nav__name">Model serving</span></a>
</div>

# Foundational papers

## 1. Attention Is All You Need (Vaswani, 2017)

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** The Transformer architecture — self-attention replaces RNNs/CNNs for sequence modeling.

**Key points.**

- The Transformer architecture — self-attention replaces RNNs/CNNs for sequence modeling.
- Multi-head attention, positional encoding, and the encoder-decoder structure become the foundation for BERT, GPT, T5, and all subsequent LLMs.

**Concept.** The Transformer architecture — self-attention replaces RNNs/CNNs for sequence modeling. Multi-head attention, positional encoding, and the encoder-decoder structure become the foundation for BERT, GPT, T5, and all subsequent LLMs.

---

## 2. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding (Devlin, 2018)

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Masked language modeling (MLM) as a pretraining objective enables bidirectional context.

**Key points.**

- Masked language modeling (MLM) as a pretraining objective enables bidirectional context.
- The pretrain-then-finetune paradigm: one large pretrained model + thin task head + small labeled dataset, replacing per-task training.
- MLM randomly masks 15% of input tokens and trains the model to predict them — forcing bidirectional context unlike GPT's left-to-right objective.

**Concept.** Masked language modeling (MLM) as a pretraining objective enables bidirectional context. The pretrain-then-finetune paradigm: one large pretrained model + thin task head + small labeled dataset, replacing per-task training. MLM randomly masks 15% of input tokens and trains the model to predict them — forcing bidirectional context unlike GPT's left-to-right objective. The pretrain-then-finetune template became the foundation of modern NLP transfer learning.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

BERT-family models are used as a classifier backend for the guardrail framework: `LocalModelBackend._load_model` loads `AutoModelForSequenceClassification` (`core/security/guardrail/backends.py:445`), parsed by `BertBinaryParser` (`core/security/guardrail/context.py:106`). Jiuwen does not use BERT as a frozen embedding encoder.

</details>

---

## 3. Language Models are Few-Shot Learners — GPT-3 (Brown, 2020)

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** In-context learning (ICL) — performing new tasks from prompt examples without weight update — emerges at scale.

**Key points.**

- In-context learning (ICL) — performing new tasks from prompt examples without weight update — emerges at scale.
- At 175B parameters, few-shot performance approaches fine-tuned baselines on many benchmarks.
- Scale enables a model to recognize task patterns from prefix sequences and apply them at inference time.

**Concept.** In-context learning (ICL) — performing new tasks from prompt examples without weight update — emerges at scale. At 175B parameters, few-shot performance approaches fine-tuned baselines on many benchmarks. Scale enables a model to recognize task patterns from prefix sequences and apply them at inference time. This changed the practitioner interface from fine-tuning to prompting.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

ICL is done through prompt construction — `PromptTemplate` (`core/foundation/prompt/template.py:14`) plus prompt sections assembled by `RuntimePromptRail` (`jiuwenswarm/jiuwenswarm/agents/harness/common/rails/runtime_prompt_rail.py:39`). There is no retrieval-augmented ICL (no per-query similar-demonstration selection).

</details>

---

## 4. Training Compute-Optimal Large Language Models — Chinchilla (Hoffmann, 2022)

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Compute-optimal training is ~20 tokens per parameter.

**Key points.**

- Compute-optimal training is ~20 tokens per parameter.
- Most large models (GPT-3, Gopher) were undertrained — too many parameters for the data seen.
- Chinchilla (70B, 1.4T tokens) outperforms Gopher (280B) with 4× fewer parameters.

**Concept.** Compute-optimal training is ~20 tokens per parameter. Most large models (GPT-3, Gopher) were undertrained — too many parameters for the data seen. Chinchilla (70B, 1.4T tokens) outperforms Gopher (280B) with 4× fewer parameters. For a fixed compute budget, scale model size and training tokens equally. Data matters as much as parameters. Smaller model + more data outperforms larger model + less data.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Pretraining is outside the framework's scope; Chinchilla-aware base-model selection is an operator-level decision.
---

</details>

---

## 5. Training Language Models to Follow Instructions with Human Feedback — InstructGPT (Ouyang, 2022)

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** RLHF pipeline for alignment: SFT on demonstrations → reward model trained on human preferences → PPO to maximize reward.

**Key points.**

- RLHF pipeline for alignment: SFT on demonstrations → reward model trained on human preferences → PPO to maximize reward.
- The paper behind ChatGPT's instruction-following.

**Concept.** RLHF pipeline for alignment: SFT on demonstrations → reward model trained on human preferences → PPO to maximize reward. The paper behind ChatGPT's instruction-following.

---

## 6. Direct Preference Optimization: Your Language Model is Secretly a Reward Model (Rafailov, 2023)

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** DPO eliminates the separate reward model and RL loop from RLHF.

**Key points.**

- DPO eliminates the separate reward model and RL loop from RLHF.
- Given (prompt, chosen, rejected) preference pairs, DPO directly optimizes the policy via a weighted cross-entropy loss — simpler, more stable, equivalent alignment.

**Concept.** DPO eliminates the separate reward model and RL loop from RLHF. Given (prompt, chosen, rejected) preference pairs, DPO directly optimizes the policy via a weighted cross-entropy loss — simpler, more stable, equivalent alignment.

---

## 7. LoRA: Low-Rank Adaptation of Large Language Models (Hu, 2021)

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Freeze all pretrained weights; inject two small trainable matrices A and B at each target layer (ΔW = BA, rank r ≪ hidden dim).

**Key points.**

- Freeze all pretrained weights; inject two small trainable matrices A and B at each target layer (ΔW = BA, rank r ≪ hidden dim).
- <1% trainable parameters; multiple adapters can share one base model.

**Concept.** Freeze all pretrained weights; inject two small trainable matrices A and B at each target layer (ΔW = BA, rank r ≪ hidden dim). <1% trainable parameters; multiple adapters can share one base model.

---

## 8. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis, 2020)

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Foundational RAG paper.

**Key points.**

- Foundational RAG paper.
- Ground generation in a retrieved knowledge base — combine a dense retriever (DPR) with a seq2seq generator — instead of relying purely on parametric memory.

**Concept.** Foundational RAG paper. Ground generation in a retrieved knowledge base — combine a dense retriever (DPR) with a seq2seq generator — instead of relying purely on parametric memory.

---

## 9. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models (Wei, 2022)

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Including step-by-step reasoning examples in the prompt (chain-of-thought few-shot) significantly improves performance on multi-step arithmetic, commonsense, and symbolic reasoning tasks.

**Key points.**

- Including step-by-step reasoning examples in the prompt (chain-of-thought few-shot) significantly improves performance on multi-step arithmetic, commonsense, and symbolic reasoning tasks.

**Concept.** Including step-by-step reasoning examples in the prompt (chain-of-thought few-shot) significantly improves performance on multi-step arithmetic, commonsense, and symbolic reasoning tasks.

---

## 10. ReAct: Synergizing Reasoning and Acting in Language Models (Yao, 2022)

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Interleave reasoning traces (Think) with tool calls (Act) and observations in the prompt.

**Key points.**

- Interleave reasoning traces (Think) with tool calls (Act) and observations in the prompt.
- This enables dynamic planning, error correction, and grounded retrieval within an agent loop.

**Concept.** Interleave reasoning traces (Think) with tool calls (Act) and observations in the prompt. This enables dynamic planning, error correction, and grounded retrieval within an agent loop.

---

## 11. Denoising Diffusion Probabilistic Models (Ho, 2020)

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Forward process adds Gaussian noise over T steps; U-Net trained to reverse it one step at a time.

**Key points.**

- Forward process adds Gaussian noise over T steps; U-Net trained to reverse it one step at a time.
- Stable supervised objective; enables high-quality image generation.
- Foundation for Stable Diffusion, DALL-E 2.

**Concept.** Forward process adds Gaussian noise over T steps; U-Net trained to reverse it one step at a time. Stable supervised objective; enables high-quality image generation. Foundation for Stable Diffusion, DALL-E 2. Inference: start from pure noise, run reverse T steps → generated image. Latent Diffusion Models (Stable Diffusion) compress to a VAE latent space for ~8× compute reduction. Quality levers: steps, guidance scale, scheduler.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Image generation is handled by external tools (`ToolCard` calls); diffusion is not part of the framework.
---

</details>

---

## 12. Learning Transferable Visual Models From Natural Language Supervision — CLIP (Radford, 2021)

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Joint image-text pretraining via contrastive learning on 400M pairs creates a shared embedding space.

**Key points.**

- Joint image-text pretraining via contrastive learning on 400M pairs creates a shared embedding space.
- Enables zero-shot image classification, text-to-image retrieval, and multimodal RAG.
- Text and image encoders trained together; cosine similarity between text and image embeddings is semantically meaningful.

**Concept.** Joint image-text pretraining via contrastive learning on 400M pairs creates a shared embedding space. Enables zero-shot image classification, text-to-image retrieval, and multimodal RAG. Text and image encoders trained together; cosine similarity between text and image embeddings is semantically meaningful. Underpins DALL-E 2 and Stable Diffusion text conditioning.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Cross-modal retrieval here uses provider-based multimodal embeddings (`DashscopeEmbedding.embed_multimodal`, `VLLMEmbedding.embed_multimodal`) rather than a CLIP encoder; `MultimodalImageRail` prepares image attachments for the generation model, not an embedding index.

</details>

---

## 13. FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness (Dao, 2022)

<span class="badge badge-type">Concept</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** Tiled attention computation that stays in SRAM — never materializes the full NxN attention matrix in HBM.

**Key points.**

- Tiled attention computation that stays in SRAM — never materializes the full NxN attention matrix in HBM.
- O(N) memory, 2–4× faster, enables practical long-context (32k–1M token) training and inference.
- Standard attention is O(N²) in memory.

**Concept.** Tiled attention computation that stays in SRAM — never materializes the full NxN attention matrix in HBM. O(N) memory, 2–4× faster, enables practical long-context (32k–1M token) training and inference. Standard attention is O(N²) in memory. FlashAttention removes this constraint. Used by default in modern LLMs and serving frameworks (vLLM, TRT-LLM).

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Infrastructure concern handled by vLLM at the serving layer. Jiuwen manages long context at the application level (offloading at 50k, compaction at 180k).

</details>

---

## 14. Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity (Fedus, 2021)

<span class="badge badge-type">Concept</span> <span class="badge badge-advanced">advanced</span>

**TL;DR.** Mixture of Experts with single-expert routing (k=1) scales model capacity without proportional FLOPs.

**Key points.**

- Mixture of Experts with single-expert routing (k=1) scales model capacity without proportional FLOPs.
- 1.6T-parameter model at ~same compute as dense 7B; 4× speedup over T5-XXL.
- MoE: N expert FFN layers + router activates k per token → total params = N×k, FLOPs ≈ k-expert dense.

**Concept.** Mixture of Experts with single-expert routing (k=1) scales model capacity without proportional FLOPs. 1.6T-parameter model at ~same compute as an 11B dense model (T5-XXL); 4× speedup over T5-XXL. MoE: N expert FFN layers + router activates k per token → total params = N×k, FLOPs ≈ k-expert dense. Practitioner implication: total parameter count overstates compute cost for MoE models.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Model architecture is opaque to the framework: no MoE-aware routing, expert metadata, or active-parameter tracking.
---

</details>

---

## 15. Constitutional AI: Harmlessness from AI Feedback (Bai, 2022)

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Replace most human preference labeling with model self-critique against explicit principles (the "constitution").

**Key points.**

- Replace most human preference labeling with model self-critique against explicit principles (the "constitution").
- SL-CAI: generate → critique → revise → SFT.
- RL-CAI: model-generated preference pairs → reward model → RLHF.

**Concept.** Replace most human preference labeling with model self-critique against explicit principles (the "constitution"). SL-CAI: generate → critique → revise → SFT. RL-CAI: model-generated preference pairs → reward model → RLHF. Far fewer human labels; auditable principle list. The constitution is an explicit, versioned list of principles — easier to update than a latent reward model. Claude's alignment is based on CAI.

<details markdown="1">
<summary><b>Under the hood</b></summary>

**Implementation**

Safety is enforced by static classifiers and rails (`SecurityRail`, `PromptInjectionGuardrail`, `SafetyPromptRail`); alignment follows standard training rather than a constitution-driven self-critique loop.

</details>

---
