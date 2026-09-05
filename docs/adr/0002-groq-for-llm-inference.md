# ADR-0002: Groq for LLM Inference

## Status

Accepted

## Context

The agent needs fast LLM inference for real-time conversational UX. B2B customers expect quick responses during ordering. Key requirements:
- Sub-second response time
- Tool calling support
- Cost-effective for production use

Options considered:
1. **OpenAI GPT-4** — high quality but ~2-5s latency
2. **Groq (Llama 3.3 70B / Qwen 3.6 27B)** — ~100ms inference, free tier available
3. **Self-hosted** — full control but infrastructure overhead

## Decision

Use **Groq** as primary LLM provider. Currently running Qwen 3.6 27B. Groq's LPU inference engine provides ultra-low latency suitable for real-time conversational UX.

## Consequences

- ~100ms inference enables snappy multi-turn conversations
- Free tier sufficient for development and early production
- Vendor lock-in to Groq's API (mitigated by LangChain abstraction)
- Model switching possible via `GROQ_MODEL` env var
