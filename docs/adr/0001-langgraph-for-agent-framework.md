# ADR-0001: LangGraph for Agent Framework

## Status

Accepted

## Context

We need a stateful, multi-turn conversational agent for B2B fashion wholesale ordering. The agent must:
- Maintain conversation context across turns
- Call multiple tools (search, stock, price, quote)
- Support retry on transient failures
- Persist state for debugging and time-travel

Options considered:
1. **Raw LangChain** — flexible but manual state management
2. **LangGraph** — built-in state machine, checkpointer, conditional edges
3. **Custom framework** — full control but high maintenance burden

## Decision

Use **LangGraph** with ReAct pattern. State flows through `AgentState` (TypedDict with `messages` key). Conditional edges route between LLM and tool nodes. `SqliteSaver` checkpointer persists state.

## Consequences

- State management is automatic via checkpointer
- Time-travel debugging available out of the box
- Retry policy configurable per-node
- Learning curve for LangGraph-specific patterns (StateGraph, conditional edges)
