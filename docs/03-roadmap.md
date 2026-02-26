# NeuralOpenClaw 2.0 - Roadmap

## Vision

Transform NeuralOpenClaw from a token-efficient memory system into an **intelligent, context-aware memory layer** that truly understands and remembers.

---

## Timeline Overview

```
2026-02-26  →  Analysis & Spec Complete
     ↓
2026-03-07  →  Phase 1 Complete (Understanding Layer)
     ↓
2026-03-21  →  Phase 2 Complete (Quality System)
     ↓
2026-04-04  →  Phase 3 Complete (Persona Memory)
     ↓
2026-04-18  →  Phase 4 Complete (Benchmark & Validation)
     ↓
2026-05-01  →  v2.0.0 Release
```

---

## Phases

### 🔴 Phase 1: Understanding Layer (Critical)
**Timeline:** 2026-02-26 → 2026-03-07 (2 weeks)  
**Priority:** Critical  
**Status:** 📝 Spec Complete → Ready to Implement

**Goals:**
- [ ] Background LLM processor (every 20 messages)
- [ ] Entity extraction (who, what, when, where)
- [ ] Date resolution ("today" → 2026-02-26)
- [ ] Quality scoring (1-5 stars)
- [ ] Enhanced memory schema

**Deliverables:**
- `src/understanding/` module
- Enhanced `EnhancedMemory` schema
- CLI commands: `process`, `quality`, `persona`
- Benchmark: 20 trick questions

**Success Metrics:**
- Date resolution accuracy: ≥90%
- Entity resolution accuracy: ≥85%
- Processing latency: <5s per batch

**Docs:**
- [`02-phase1-spec.md`](./02-phase1-spec.md) - Full specification

---

### 🟡 Phase 2: Quality System (High Priority)
**Timeline:** 2026-03-08 → 2026-03-21 (2 weeks)  
**Priority:** High  
**Status:** ⏳ Planned

**Goals:**
- [ ] User feedback loop (verify/correct memories)
- [ ] Auto-rejection of low-quality memories
- [ ] Memory deduplication
- [ ] Confidence calibration

**Deliverables:**
- Verification CLI: `nocl verify --id <id>`
- Auto-reject pipeline
- Duplicate detection algorithm
- Quality dashboard

**Success Metrics:**
- User correction rate: <10%
- Duplicate rate: <5%
- Quality score correlation: ≥0.8 (vs human)

---

### 🟡 Phase 3: Persona-based Memory (High Priority)
**Timeline:** 2026-03-22 → 2026-04-04 (2 weeks)  
**Priority:** High  
**Status:** ⏳ Planned

**Goals:**
- [ ] Separate storage per persona (personal/technical/social)
- [ ] Persona-aware retrieval
- [ ] Context switching
- [ ] Privacy rules per persona

**Deliverables:**
- Persona partitioning in storage
- Persona-aware query API
- Privacy filters
- Session type detection

**Success Metrics:**
- Persona detection accuracy: ≥90%
- Context mixing: <5%
- Privacy violations: 0

---

### 🟢 Phase 4: Benchmark & Validation (Medium Priority)
**Timeline:** 2026-04-05 → 2026-04-18 (2 weeks)  
**Priority:** Medium  
**Status:** ⏳ Planned

**Goals:**
- [ ] Full benchmark suite (20 trick questions)
- [ ] Automated testing pipeline
- [ ] Performance profiling
- [ ] Quality trend tracking

**Deliverables:**
- `tests/benchmark/` suite
- Weekly quality reports
- Performance dashboard
- CI/CD integration

**Success Metrics:**
- Overall benchmark accuracy: ≥80%
- Test coverage: ≥90%
- Performance regression: 0%

---

### 🟢 Phase 5: Advanced Features (Future)
**Timeline:** 2026-04-19 → 2026-05-01 (2 weeks)  
**Priority:** Medium  
**Status:** ⏳ Future

**Goals:**
- [ ] Causal chain extraction
- [ ] Relationship mapping
- [ ] Predictive suggestions
- [ ] Cross-session reasoning

**Deliverables:**
- Causal graph storage
- Relationship API
- Suggestion engine
- v2.0.0 release

---

## Architecture Evolution

### Current (v1.0)

```
User → SmartMemoryRouter → NeuralMemory → ContextAssembler → LLM
```

### Phase 1 (v1.5)

```
User → Message Counter → Understanding LLM → Enhanced NeuralMemory → Router → Context → LLM
                    ↓
              (every 20 msgs)
```

### Phase 3 (v2.0)

```
User → Message Counter → Understanding LLM → Persona Memory Store → Router → Context → LLM
                    ↓              ↓
              (every 20 msgs)  [personal/technical/social]
```

---

## Comparison: Reddit vs NeuralOpenClaw 2.0

| Feature | Reddit Architecture | NeuralOpenClaw 2.0 |
|---------|---------------------|-------------------|
| Understanding Layer | ✅ Grok every 20 msgs | ✅ qwen-3b-coder every 20 msgs |
| Date Resolution | ✅ Yes | ✅ Yes (Phase 1) |
| Entity Resolution | ✅ Yes | ✅ Yes (Phase 1) |
| Quality Ranking | ✅ 1-5 stars | ✅ 1-5 stars (Phase 1) |
| Persona-based | ✅ Yes | ✅ Yes (Phase 3) |
| Tool Caching | ❌ No | ✅ Yes (existing) |
| Session Compression | ❌ No | ✅ Yes (existing) |
| Privacy Protection | Manual | ✅ Auto-redaction (existing) |
| CLI | Graph UI | ✅ nocl command (existing) |
| Benchmark | ✅ 20 questions | ✅ 20 questions (Phase 4) |

**NeuralOpenClaw 2.0 = Reddit Architecture + Existing Features** 🎯

---

## Key Decisions

### 1. Processing Trigger
**Decision:** Message count (every 20 messages)  
**Rationale:** Matches Reddit architecture, balances latency vs quality  
**Alternative:** Cron-based (rejected: may miss important messages)

### 2. LLM Model
**Decision:** qwen-3b-coder (cheap, local)  
**Rationale:** Cost-effective, fast, good enough for extraction  
**Fallback:** ollama/qwen3-coder-next, bailian-api/qwen-flash

### 3. Quality Threshold
**Decision:** Auto-store ≥3 stars, Auto-reject <2 stars  
**Rationale:** Conservative approach, avoids bad memories  
**Tunable:** Via config file

### 4. Persona Categories
**Decision:** 3 personas (personal, technical, social)  
**Rationale:** Covers all use cases, simple to implement  
**Extensible:** Can add more later

### 5. Storage Schema
**Decision:** Enhanced JSON with metadata  
**Rationale:** Backward-compatible, queryable, extensible  
**Migration:** Not required (additive changes)

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM extraction errors | High | Medium | Schema validation, retry logic |
| Date ambiguity | Medium | Medium | Conservative confidence scoring |
| Processing latency | Medium | Low | Async processing, cheap model |
| Token cost increase | Low | Low | Batch processing, local LLM |
| Schema breaking changes | High | Low | Backward-compatible design |
| User adoption | Medium | Low | Clear docs, CLI tools, benchmark |

---

## Success Metrics (Overall)

| Metric | Baseline (v1.0) | Target (v2.0) | Improvement |
|--------|-----------------|---------------|-------------|
| Date Resolution Accuracy | 0% | 90% | +90% |
| Entity Resolution Accuracy | 0% | 85% | +85% |
| Memory Quality Score | N/A | 4.0/5.0 | New metric |
| Benchmark Accuracy | N/A | 80% | New metric |
| Token Efficiency | Baseline | +35% | +35% |
| User Satisfaction | N/A | 4.5/5.0 | New metric |

---

## Getting Involved

### For Developers
1. Read [`01-architecture-analysis.md`](./01-architecture-analysis.md)
2. Read [`02-phase1-spec.md`](./02-phase1-spec.md)
3. Pick a task from Phase 1 checklist
4. Submit PR with tests

### For Users
1. Install NeuralOpenClaw v2.0 (when released)
2. Run benchmark suite
3. Report issues/feedback
4. Contribute trick questions

---

## References

- Reddit Post: https://www.reddit.com/r/openclaw/comments/1raymjw/architecture_of_unlimited_quality_memory/
- Original NeuralOpenClaw: https://github.com/linda-agi/neural-openclaw
- Analysis Doc: [`01-architecture-analysis.md`](./01-architecture-analysis.md)
- Phase 1 Spec: [`02-phase1-spec.md`](./02-phase1-spec.md)

---

**Last Updated:** 2026-02-26  
**Version:** 1.0  
**Status:** Planning Complete → Ready for Phase 1 Implementation
