# ML foundations

## 1. What is the difference between AI, Machine Learning, and Deep Learning?

<span class="badge badge-type">Compare</span> <span class="badge badge-basic">basic</span>

**TL;DR.** AI is the broadest umbrella; ML is the subset that learns from data; Deep Learning is the sub-subset using multi-layer neural nets.

**Key points.**

- AI: any technique making a machine exhibit intelligent behaviour.
- ML: learns patterns from data rather than hand-coded rules.
- DL: ML with many-layer neural nets enabling end-to-end representation learning.

**Concept.** Nested definitions. Artificial Intelligence is the broadest umbrella: any technique that makes a machine exhibit behaviour associated with human intelligence — search, planning, rule systems, ML. Machine Learning is the subset where the machine learns patterns from data rather than following hand-coded rules. Deep Learning is the sub-subset of ML that uses neural networks with many layers, enabling end-to-end representation learning from raw inputs like images, text, or audio without manual feature engineering. Concretely: a rule-based spam filter is AI but not ML. A logistic regression spam classifier is AI and ML but not DL. A transformer-based classifier is all three.

![diagram](assets/diagrams/7098ae948fa134d2aa1be76ba038157dd35480dc.png)

---

## 2. What is supervised vs unsupervised vs reinforcement learning?

<span class="badge badge-type">Compare</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Supervised uses labelled pairs to learn a mapping; unsupervised discovers structure without labels; RL maximises cumulative reward via trial and error.

**Key points.**

- Supervised: labelled (x, y) pairs → learn f(x)→y.
- Unsupervised: no labels → clusters, embeddings, density.
- RL: reward signal → policy that maximises return.
- LLM training combines all three: self-supervised pretraining, SFT, RLHF.

**Concept.** Supervised: labelled `(x, y)` pairs; the model learns `f(x)→y` by minimising prediction loss. Examples: classification, regression, NER. Unsupervised: no labels; the model discovers structure in the data — clusters, embeddings, density. Examples: k-means, PCA, autoencoders, contrastive embedding training. Reinforcement learning: an agent takes actions in an environment, receives scalar reward signals, and learns a policy that maximises cumulative reward — no labelled correct action. Examples: game-playing agents, RLHF for LLM alignment. LLM training combines all three: self-supervised pre-training (structurally supervised but labels come from the data itself), SFT (supervised), RLHF (RL).

![diagram](assets/diagrams/aceb3e12c844fa8bd8333c435c7153e836508acb.png)

---

## 3. What is the bias-variance tradeoff?

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Generalisation error = bias² (underfitting) + variance (overfitting) + irreducible noise; the tradeoff is between model complexity and stability.

**Key points.**

- High bias: model too simple, misses patterns.
- High variance: model too complex, fits noise.
- Reducing bias (more complexity) tends to increase variance.
- Double descent: very large models can re-enter low-variance regime with enough data.

**Concept.** Every model's generalisation error decomposes into: bias (error from wrong assumptions — underfitting, model too simple), variance (error from sensitivity to training set fluctuations — overfitting, model too complex), and irreducible noise. High bias: model misses patterns. High variance: model fits noise. Reducing bias by adding complexity tends to increase variance and vice versa. The goal is to minimise total expected error. In modern large models, "double descent" complicates the classic picture: very high-capacity models can re-enter a low-variance regime with enough data and regularisation — which is why LLMs generalise despite billions of parameters.

![diagram](assets/diagrams/acf51b538c85e67f04d4bc2523b6619f7692c33c.png)

---

## 4. What is the difference between a parameter and a hyperparameter?

<span class="badge badge-type">Compare</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Parameters are learned weights updated by gradient descent; hyperparameters are engineer-set configuration choices not changed by training.

**Key points.**

- Parameters: W, b, attention matrices — set by gradient descent.
- Training hyperparams: LR, batch size, epochs, dropout, LoRA rank.
- Inference hyperparams: temperature, top-p, max_tokens — not weights.

**Concept.** Parameters are the learned weights of the model — the numbers changed during training via gradient descent (`W`, `b` in a linear layer; attention projection matrices in a transformer). Training data determines their values. Hyperparameters are the configuration choices made before or during training that the training process does not change: learning rate, batch size, number of layers, dropout rate, regularisation coefficient, training epochs, LoRA rank. A common source of confusion: context window size, temperature, and top-p are inference-time hyperparameters — they do not affect weights, only how the model generates at prediction time.

![diagram](assets/diagrams/0d661d408b14b15b27b9313ed75391622888bb5d.png)

---

## 5. What is gradient descent, and how does it work?

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Iterative optimisation that moves parameters in the direction of steepest loss decrease by subtracting learning_rate × gradient at each step.

**Key points.**

- Step: compute loss, compute gradient, subtract lr × grad.
- SGD uses mini-batches — noisy but cheap per step.
- Variants: momentum, Adam (adaptive per-parameter LR).

**Concept.** An iterative optimisation algorithm that minimises a loss function by moving parameters in the direction of steepest descent. Each step: compute the loss, compute the gradient `∂L/∂w` for each parameter, subtract `learning_rate × gradient` from each parameter. Stochastic gradient descent (SGD) does this on a mini-batch rather than the full dataset — the gradient estimate is noisy but each step is cheap and often generalises better. Key variants: SGD with momentum (accumulates gradient history to reduce oscillation), Adam (adaptive per-parameter learning rates based on gradient moments).

---

## 6. Compute cosine similarity between two vectors without using a library

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** dot(A,B) / (|A| × |B|) — measures directional similarity, length-independent, range [-1,1].

**Key points.**

- Dot product divided by product of magnitudes.
- Length-independent: normalising to unit length reduces it to a dot product.
- Edge cases: zero vectors, dimension mismatch.

**Concept.** Cosine similarity = `dot(A, B) / (|A| × |B|)`. The dot product measures shared direction; dividing by the product of magnitudes normalises to `[-1, 1]`, making the result length-independent. In retrieval, pre-normalising all vectors to unit length reduces cosine similarity to a plain dot product, which is cheaper to compute at scale.

![diagram](assets/diagrams/35537c87cbbf6a4a8be10dac6442e3a366bbab46.png)

---

## 7. Given a confusion matrix, calculate precision, recall, and F1 manually

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Precision = TP/(TP+FP); Recall = TP/(TP+FN); F1 = harmonic mean of the two — each measures a different cost of classification error.

**Key points.**

- Precision: of predicted positives, how many are actually positive.
- Recall: of all actual positives, how many were caught.
- F1: harmonic mean; penalises imbalance between precision and recall.
- Multi-class: per-class TP/FP/FN, then macro/micro average.

**Concept.** For a binary classifier `[[TN, FP], [FN, TP]]`:
- Precision = TP / (TP + FP) — of predicted positives, how many were actually positive
- Recall = TP / (TP + FN) — of all actual positives, how many were caught
- F1 = 2 × (Precision × Recall) / (Precision + Recall) — harmonic mean, penalises imbalance

![diagram](assets/diagrams/6d80c58ebd99bfe295f3a2fdb3358322f59be805.png)

---

## 8. Implement k-nearest neighbors from scratch

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Lazy learner: store all training points, predict by majority vote of the k nearest examples by distance.

**Key points.**

- No training cost, all cost at inference (O(n·d) per query).
- Sensitive to feature scale — normalise first.
- ANN indexes (HNSW, IVF) approximate KNN at scale.

**Concept.** KNN at inference: store all training points, then for a new query: (1) compute distance from the query to every training point, (2) sort by distance, (3) take the k smallest, (4) return majority class (classification) or mean (regression). KNN is lazy — no training cost, all cost at inference, O(n·d) per query without indexing. Sensitive to feature scale (normalise first) and irrelevant dimensions. ANN indexes (HNSW, IVF) replicate the nearest-neighbour idea at scale.

![diagram](assets/diagrams/b4ab597c3bb33984c58741c2d84c527001dc7bfc.png)

---

## 9. Explain forward pass and backpropagation in a neural network

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Forward pass computes the prediction and loss; backpropagation applies the chain rule backwards to compute gradients for every weight.

**Key points.**

- Forward: input → layers → loss.
- Backward: chain rule ∂L/∂w = ∂L/∂output × ∂output/∂w.
- PyTorch autograd records graph forward, traverses backward.

**Concept.** The forward pass flows inputs through layers, applying learned weights and non-linearities, to produce a prediction and a scalar loss. Backpropagation then applies the chain rule backwards through every layer: `∂L/∂w = ∂L/∂output × ∂output/∂w` for each weight. PyTorch's autograd engine records the computation graph during the forward pass and traverses it in reverse during `.backward()`, accumulating `w.grad`. The optimiser then applies `w -= lr × w.grad`.

![diagram](assets/diagrams/ff62182dd127c73a0b82419ab61b2ce4e023aaa1.png)

---

## 10. What is vanishing/exploding gradient, and how do you fix it?

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Products of many Jacobians shrink (vanishing) or grow (exploding) exponentially; fixed by ReLU, residual connections, layer norm, and gradient clipping.

**Key points.**

- Vanishing: eigenvalue < 1 → early weights stop learning.
- Exploding: eigenvalue > 1 → NaN weights.
- Fixes: ReLU, residuals, layer norm, He init (vanishing); gradient clipping (exploding).
- Transformers largely avoid both via residual + layer norm at every block.

**Concept.** In deep networks, gradients are products of many Jacobians chained together. Eigenvalues consistently below 1 → gradients shrink exponentially toward early layers (vanishing) — early weights stop learning. Eigenvalues consistently above 1 → gradients grow exponentially (exploding) — NaN weights.

![diagram](assets/diagrams/11cad2100859ded4b92a852d0e0896adb86719e0.png)

---

## 11. What is the difference between batch normalization and layer normalization?

<span class="badge badge-type">Compare</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Batch norm normalises over the batch dimension (good for CNNs); layer norm normalises over the feature dimension (standard in Transformers and LLMs).

**Key points.**

- BatchNorm: over batch dim; needs large batches; good for CNNs.
- LayerNorm: over feature dim; independent of batch size; standard in Transformers.
- Small batch or variable-length sequence? Always LayerNorm.

**Concept.** Batch normalisation normalises across the batch dimension — mean and variance computed over all examples in the batch, per feature. Requires a reasonable batch size for stable statistics. Effective in CNNs and feedforward networks; struggles with small batches, variable-length sequences, and batch size 1 at inference.

![diagram](assets/diagrams/a957d1e3f196e0e5a5947f34c972b127caaec012.png)

---

## 12. What is dropout, and why does it help generalisation?

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Randomly zeroes activations with probability p during training, forcing distributed representations and acting as an ensemble of 2^n thinned networks.

**Key points.**

- Each neuron zeroed with probability p; inference scales by 1/(1-p).
- Prevents co-adaptation between neurons.
- Applied to attention weights, FFN, and embeddings in Transformers.
- LoRA dropout is a key regularisation knob for PEFT fine-tuning.

**Concept.** Dropout randomly zeroes each neuron's activation with probability `p` (typically 0.1–0.5) on each forward pass during training. At inference, dropout is disabled and activations are scaled by `1/(1-p)` (inverted dropout). Why it works: by randomly removing neurons, the network cannot co-adapt (learn to rely on specific neurons to compensate for each other's mistakes in a memorisation-specific way) and is forced to learn redundant, distributed representations. The effect is similar to training an ensemble of `2^n` thinned networks and averaging them at inference. In transformers, dropout is applied to attention weights, FFN layers, and embeddings. In LoRA fine-tuning, dropout on the low-rank matrices is a key regularisation knob.

![diagram](assets/diagrams/25d46b7cbb064800a9b458e3408575f1378e34c7.png)

---

## 13. What is the difference between CNNs and RNNs, and when would you use each?

<span class="badge badge-type">Compare</span> <span class="badge badge-basic">basic</span>

**TL;DR.** CNNs use shared spatial filters (images, 1D signals); RNNs maintain a sequential hidden state (time series, variable-length text before Transformers).

**Key points.**

- CNN: translation-invariant, shared weights, efficient for grids.
- RNN/LSTM: sequential hidden state, order-aware, bottleneck on long sequences.
- Transformers replaced RNNs for text; CNNs dominate for images.

**Concept.** Convolutional Neural Networks (CNNs) apply learned filters spatially using shared weights — translation-invariant and efficient for structured grid data (images, audio spectrograms, 1D signals). Not designed for variable-length sequential dependencies. Recurrent Neural Networks (RNNs, LSTMs, GRUs) process sequences step by step, maintaining a hidden state. Designed for sequential data where order matters and length varies: time series, text (pre-transformer), audio frames. Weakness: the hidden state is a bottleneck for long sequences; vanishing gradients make long-range dependencies hard. Transformers have largely replaced RNNs for text because attention can directly attend to any position. CNNs remain dominant for image tasks.

![diagram](assets/diagrams/124bcda521c386066eac284688421186b2fd5ba9.png)

---

## 14. What is transfer learning, and when is it useful?

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Use a model trained on one task as the starting point for another — either freezing weights (feature extraction) or continuing to train them (fine-tuning).

**Key points.**

- Feature extraction: freeze pre-trained weights, train new head.
- Fine-tuning: continue training all or some pre-trained weights.
- Every use of a foundation model is transfer learning.

**Concept.** Transfer learning uses a model trained on one task or dataset as the starting point for a different but related task, rather than training from scratch. Two forms: (1) feature extraction — freeze pre-trained weights, train a new task-specific head; (2) fine-tuning — continue training all or some pre-trained weights on the new task's data. Useful almost always when labelled data for the target task is limited, when compute budget is constrained, or when source and target domains are related. In the LLM context, every use of a foundation model (GPT-4, LLaMA, Claude) is transfer learning. SFT and LoRA/PEFT are explicit transfer learning from a base model to a narrower task.

![diagram](assets/diagrams/0c6dc948cfc7a71e8aa577f6c072053d59065539.png)

---

## 15. How do you evaluate a classification model beyond accuracy?

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Accuracy is misleading on imbalanced data; use precision/recall/F1, confusion matrix, ROC-AUC, PR-AUC, and log loss for a complete picture.

**Key points.**

- Precision/Recall/F1: cost-weighted classification quality.
- Confusion matrix: reveals per-class error patterns.
- ROC-AUC: ranking quality, threshold-independent.
- PR-AUC: better than ROC-AUC for severely imbalanced data.

**Concept.** Accuracy is misleading on imbalanced datasets — a classifier that always predicts the majority class achieves 95% accuracy on a 95/5 split. Richer metrics:
- **Precision / Recall / F1** — precision = TP/(TP+FP); recall = TP/(TP+FN); F1 = harmonic mean. Precision matters when false positives are costly (spam filters); recall when false negatives are costly (cancer screening).
- **Confusion matrix** — reveals per-class error patterns and which classes are being confused.
- **ROC-AUC** — area under the ROC curve; measures ranking quality across all thresholds. Threshold-independent.
- **PR-AUC** — area under the Precision-Recall curve; better than ROC-AUC for severely imbalanced data.
- **Log loss / cross-entropy** — penalises confident wrong predictions; measures calibration.
- **Calibration curve** — do predicted probabilities reflect actual event rates?

![diagram](assets/diagrams/d4d6809ee84be731f1bf8e6d35d93e065a97096f.png)

---

## 16. What is cross-validation, and why does it matter?

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** k-fold CV splits data into k folds and rotates the held-out set, producing a low-variance generalisation estimate that uses every sample.

**Key points.**

- Train on k-1 folds, evaluate on the held-out fold, repeat k times.
- Average of k scores is more reliable than a single split.
- Essential for honest hyperparameter tuning.

**Concept.** Cross-validation estimates how well a model generalises when you have limited data. In k-fold CV: split data into k equal folds; train on k-1 folds and evaluate on the held-out fold; repeat k times rotating the held-out fold; average the k evaluation scores. The result is a low-variance generalisation estimate that uses every sample for both training and evaluation. Why it matters: a single train/test split gives a noisy estimate dependent on which examples landed in the test set. CV reduces that variance. Essential for honest hyperparameter tuning — tuning on a fixed held-out set leaks information and overfits the hyperparameters to that specific split. In the LLM context: rarely used on the full model (too expensive) but useful when fine-tuning on small datasets.

![diagram](assets/diagrams/e914e001594abac993a7b248ef300718cb9c390c.png)

---

## 17. What is overfitting, and how do you prevent it?

<span class="badge badge-type">Concept</span> <span class="badge badge-basic">basic</span>

**TL;DR.** Overfitting: training loss falls but validation loss rises as the model memorises noise; prevent with more data, regularisation, early stopping, or reduced capacity.

**Key points.**

- Signal: train loss ↓, val loss ↑.
- Prevent: more data, L2/dropout regularisation, early stopping.
- For LLMs: LoRA reduces trainable parameters; monitor validation perplexity.

**Concept.** Overfitting occurs when a model learns the training data too well — including noise and idiosyncrasies — and fails to generalise to unseen examples. Training loss decreases but validation loss increases (the classic divergence signal). Prevention:
- **More data / augmentation** — the most reliable fix
- **Regularisation** — L2 (weight decay) penalises large weights; L1 encourages sparsity; dropout randomly zeroes activations
- **Early stopping** — stop when validation loss stops improving
- **Reduce model capacity** — smaller architecture or fewer fine-tuned parameters (LoRA)
- **Cross-validation** — ensures evaluation is not from a lucky split

![diagram](assets/diagrams/58b510be6f9252ddfc46936c3ba16b5ad1a29214.png)

---

## 18. Why does the Transformer use multi-head attention instead of a single head?

<span class="badge badge-type">Concept</span> <span class="badge badge-intermediate">intermediate</span>

**TL;DR.** Multiple heads run in parallel on lower-dimensional projections, each free to specialise on different relationship types simultaneously, with no extra compute cost.

**Key points.**

- Single head: one relationship type at a time.
- Multi-head: each head specialises (syntax, coreference, position, etc.).
- Same compute cost: d_model splits into h × d_k per head.

**Concept.** A single attention head learns one type of relationship simultaneously — for example, syntactic dependency or positional proximity. Multiple heads run in parallel on lower-dimensional projections, each free to specialise on different relationship types: one head may track subject-verb agreement, another coreference, another relative position. Concatenating and projecting the outputs lets the model integrate all those signals. The compute cost is equivalent to one full-dimensional head (because `d_model` splits into `h × d_k` heads), but the representational expressivity is higher. Evidence: ablating individual heads degrades performance on different tasks depending on which head was removed.

![diagram](assets/diagrams/20ac27f224e6a31e923f2d5d890a0c3197960d22.png)

---
