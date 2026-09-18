# AI Engineer Interview Questions I Keep Seeing Everywhere (LinkedIn, Blind, Interview Prep Forums)

Compiled from recurring social/forum posts. This is a **questions-only** source list (the original post provided no answers); categories and wording are kept as published.

# System Design and Architecture

## 1. Design a RAG based customer support system for 1 million users

## 2. How would you architect a multi agent system for research automation

## 3. Walk me through what happens when a user query hits your pipeline, end to end

## 4. How would you design a system that routes queries to different specialized agents

# RAG and Retrieval

## 5. How do you choose chunk size when splitting documents for embedding

## 6. What's the difference between RAG and fine-tuning, and when would you use each

## 7. How do you handle hallucinations when retrieved context doesn't answer the question

## 8. Why isn't vector similarity search alone enough, and what does reranking fix

# Agents and Tool Use

## 9. How does function calling work under the hood

## 10. How do you prevent an agent from getting stuck in an infinite tool-calling loop

## 11. How do you handle a tool call that fails or returns malformed output

## 12. When is a multi-agent system overkill compared to a single well-designed agent

# Evaluation and Testing

## 13. How do you evaluate an LLM application beyond "it looks correct"

## 14. What's the difference between faithfulness and relevance in RAG evaluation

## 15. How would you build a regression test suite for a prompt-based system

## 16. How do you A/B test a prompt change safely in production

# Cost, Latency, and Scale

## 17. How do you control cost when an agent can call tools repeatedly

## 18. How would you reduce latency in a multi-step LLM pipeline

## 19. What happens to your architecture at 10x current traffic

## 20. How do you decide between a larger model and a smaller, faster one for a given task

# Security

## 21. What is prompt injection, and how would you defend against it

## 22. How do you handle untrusted content coming from a tool result or retrieved document

## 23. How do you prevent sensitive data from leaking into a model's context or output

# Behavioral / Judgment

## 24. Tell me about a time an AI feature didn't work as expected in production. What did you do

## 25. A stakeholder wants to ship a feature before your eval scores are where you want them. How do you handle it

## 26. How do you decide when a problem needs an LLM versus a simpler rule-based system

---

**The pattern worth noticing:** The questions barely change month to month. What changes is how deep the follow-up goes. A junior candidate explains what RAG is. A senior candidate explains why they'd choose 5 retrieved documents over 20 for a specific latency budget, and what they'd monitor after shipping it.
