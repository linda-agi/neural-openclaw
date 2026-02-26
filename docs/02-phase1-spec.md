# NeuralOpenClaw 2.0 - Phase 1 Specification

## Understanding Layer Implementation

**Version:** 2.0 (Hội Nghị Diên Hồng Approved)  
**Date:** 2026-02-26  
**Status:** ✅ Approved for Implementation  
**Priority:** 🔴 Critical

---

## 🏛️ HỘI NGHỊ DIÊN HỒNG APPROVAL

**Meeting:** Hội Nghị Diên Hồng LCL Corp  
**Date:** 2026-02-26 15:30-16:30 UTC  
**Result:** ✅ **5/5 MOTIONS PASSED - UNANIMOUS (6/6 Yes)**

**Key Decisions:**
1. ✅ **Personal-First Architecture** (single-user, SQLite, simplified)
2. ✅ **OpenClaw-Native LLM Routing** (fetch từ gateway, auto-select)
3. ✅ **Success Criteria** (≥90% date, ≥85% entity, <4GB RAM, <15s latency)
4. ✅ **Simplified Security** (encryption, access control, audit, **NO rate limit**)
5. ✅ **Ủy quyền Implement Phase 1a** (4 weeks, Feb 26 - Mar 25)

**Meeting Notes:** `docs/meeting-notes-2026-02-26.md`

---

## 1. Overview

### Goal

Implement an **Understanding Layer** that processes chat messages and extracts structured, date-resolved, entity-linked memories with quality scores.

### Problem Solved

Current NeuralOpenClaw stores raw text without understanding:
- ❌ "today" remains relative → Cannot answer "when?"
- ❌ "I" remains pronoun → Cannot answer "who?"
- ❌ No quality control → Bad memories stored
- ❌ No context categorization → Memory mixing

### Solution

Add background LLM processing that:
- ✅ Extracts entities (who, what, when, where)
- ✅ Resolves relative dates → absolute dates
- ✅ Assigns quality scores (1-5 stars)
- ✅ Categorizes by persona (personal/technical)

### Scope (Hội Nghị Decision)

**Personal-First:** Single-user for Bro (not multi-tenant SaaS)  
**OpenClaw-Native:** Fetch models từ OpenClaw gateway (no duplicate config)  
**Resource-Aware:** Auto-detect RAM → Select model (local → cloud fallback)  
**Simplified:** SQLite storage, file encryption, basic audit, **NO rate limit**

---

## 2. Architecture

### Component Diagram (Updated for Personal-First)

```
┌─────────────────────────────────────────────────────────────┐
│              Phase 1 Architecture (Personal-First)          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Chat Session → [Message Counter]                           │
│                       │                                     │
│                       │ (every 20 messages)                 │
│                       ▼                                     │
│              [Background Processor]                         │
│              (async, non-blocking)                          │
│                       │                                     │
│                       ▼                                     │
│         ┌─────────────────────────────┐                    │
│         │  OpenClaw Model Router      │                    │
│         │  - Fetch from gateway       │                    │
│         │  - Auto-select by RAM       │                    │
│         │  - Local → Cloud fallback   │                    │
│         └─────────────────────────────┘                    │
│                       │                                     │
│                       ▼                                     │
│         ┌─────────────────────────────┐                    │
│         │  Understanding LLM          │                    │
│         │  Model: Auto-selected       │                    │
│         │  (OpenClaw providers)       │                    │
│         └─────────────────────────────┘                    │
│                       │                                     │
│                       ▼                                     │
│         ┌─────────────────────────────┐                    │
│         │  Structured Output          │                    │
│         │  - Entities (JSON)          │                    │
│         │  - Resolved dates           │                    │
│         │  - Quality score            │                    │
│         │  - Persona tag              │                    │
│         └─────────────────────────────┘                    │
│                       │                                     │
│                       ▼                                     │
│         ┌─────────────────────────────┐                    │
│         │  SQLite Memory Store        │                    │
│         │  - Enhanced schema          │                    │
│         │  - File encryption          │                    │
│         │  - Quality-indexed          │                    │
│         └─────────────────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Processing Flow

```
1. User sends 20 messages
        ↓
2. Trigger Background Processor
        ↓
3. Fetch last 20 messages from session
        ↓
4. Send to Understanding LLM with prompt
        ↓
5. LLM extracts structured data
        ↓
6. Validate output (schema check)
        ↓
7. Store in NeuralMemory with metadata
        ↓
8. Update quality index
```

---

## 3. Data Schema

### Enhanced Memory Schema

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Literal
from enum import Enum

class PersonaType(Enum):
    PERSONAL = "personal"      # Casual conversations with Bro
    TECHNICAL = "technical"    # Coding, architecture, decisions
    SOCIAL = "social"          # Group chats (no private data)

class MemoryQuality(Enum):
    EXCELLENT = 5   # High confidence, verified
    GOOD = 4        # Good confidence, likely correct
    FAIR = 3        # Moderate confidence, may need verification
    POOR = 2        # Low confidence, flag for review
    REJECT = 1      # Auto-reject, do not store

@dataclass
class Entity:
    type: Literal["person", "location", "organization", "date", "action", "object"]
    value: str
    resolved_value: Optional[str] = None  # e.g., "today" → "2026-02-26"
    confidence: float = 1.0

@dataclass
class EnhancedMemory:
    # Core content
    content: str                    # Original text
    summary: str                    # LLM-generated summary
    
    # Entities
    entities: List[Entity]          # Extracted entities
    
    # Resolution
    resolved_date: Optional[datetime]  # Absolute date if mentioned
    resolved_person: Optional[str]     # Who is "I"?
    
    # Quality
    quality_score: MemoryQuality    # 1-5 stars
    confidence: float               # 0.0-1.0
    
    # Categorization
    persona: PersonaType            # personal/technical/social
    category: str                   # e.g., "decision", "fact", "event"
    
    # Metadata
    created_at: datetime            # When memory was created
    source_session: str             # Session ID
    message_count: int              # Which message batch (1-20, 21-40, etc.)
    
    # Validation
    verified: bool = False          # User verified?
    verification_count: int = 0     # How many times verified
    last_accessed: Optional[datetime] = None  # LRU tracking
    
    # Expiration
    expires_at: Optional[datetime] = None  # TTL expiration
    is_permanent: bool = False      # Never expire?
```

### JSON Storage Format

```json
{
  "id": "mem_abc123",
  "content": "I am going shopping at the mall today",
  "summary": "User plans to go shopping at a mall",
  "entities": [
    {
      "type": "person",
      "value": "I",
      "resolved_value": "dat911zz",
      "confidence": 0.95
    },
    {
      "type": "location",
      "value": "mall",
      "resolved_value": null,
      "confidence": 0.8
    },
    {
      "type": "date",
      "value": "today",
      "resolved_value": "2026-02-26",
      "confidence": 1.0
    },
    {
      "type": "action",
      "value": "shopping",
      "resolved_value": null,
      "confidence": 0.9
    }
  ],
  "resolved_date": "2026-02-26T00:00:00Z",
  "resolved_person": "dat911zz",
  "quality_score": 4,
  "confidence": 0.85,
  "persona": "personal",
  "category": "event",
  "created_at": "2026-02-26T15:00:00Z",
  "source_session": "agent:main:main",
  "message_count": 20,
  "verified": false,
  "verification_count": 0,
  "last_accessed": null,
  "expires_at": null,
  "is_permanent": false
}
```

---

## 4. Understanding LLM Prompt

### System Prompt

```
You are an expert memory analyst for an AI personal assistant.
Your task is to extract structured, accurate information from chat messages.

## Rules:
1. ALWAYS resolve relative dates ("today", "yesterday", "tomorrow") to absolute dates
2. ALWAYS resolve pronouns ("I", "me", "my") to the user's name
3. Extract ALL entities (people, places, organizations, dates, actions, objects)
4. Assign quality scores honestly (1-5 stars)
5. Categorize by persona (personal/technical/social)
6. Be conservative - if unsure, assign lower confidence

## Quality Score Guidelines:
- 5 stars: Clear, unambiguous, verified facts
- 4 stars: High confidence, likely correct
- 3 stars: Moderate confidence, may need verification
- 2 stars: Low confidence, ambiguous
- 1 star: Very low confidence, contradictory, or nonsensical (REJECT)

## Persona Categories:
- personal: Casual conversations, daily activities, preferences
- technical: Coding, architecture, tools, debugging, decisions
- social: Group chats, social interactions (NO private data)

Output MUST be valid JSON matching the schema.
```

### User Prompt Template

```
Analyze the following chat messages and extract structured memory.

**Current Date:** {current_date}
**User Name:** {user_name}
**Session Type:** {session_type}

**Messages:**
{messages_batch}

**Output JSON:**
```

### Example Input/Output

**Input:**
```
Current Date: 2026-02-26
User Name: dat911zz
Session Type: personal

Messages:
- "I am going shopping at the mall today"
- "Need to buy a new laptop for work"
- "Maybe MacBook Pro or Dell XPS"
```

**Output:**
```json
{
  "content": "I am going shopping at the mall today. Need to buy a new laptop for work. Maybe MacBook Pro or Dell XPS.",
  "summary": "User plans shopping trip to mall to buy work laptop, considering MacBook Pro or Dell XPS",
  "entities": [
    {"type": "person", "value": "I", "resolved_value": "dat911zz", "confidence": 1.0},
    {"type": "location", "value": "mall", "resolved_value": null, "confidence": 0.8},
    {"type": "date", "value": "today", "resolved_value": "2026-02-26", "confidence": 1.0},
    {"type": "action", "value": "shopping", "resolved_value": null, "confidence": 0.9},
    {"type": "object", "value": "laptop", "resolved_value": null, "confidence": 0.95},
    {"type": "object", "value": "MacBook Pro", "resolved_value": null, "confidence": 1.0},
    {"type": "object", "value": "Dell XPS", "resolved_value": null, "confidence": 1.0},
    {"type": "organization", "value": "Apple", "resolved_value": null, "confidence": 0.9},
    {"type": "organization", "value": "Dell", "resolved_value": null, "confidence": 0.9}
  ],
  "resolved_date": "2026-02-26",
  "resolved_person": "dat911zz",
  "quality_score": 4,
  "confidence": 0.88,
  "persona": "personal",
  "category": "plan",
  "is_permanent": false,
  "expires_at": null
}
```

---

## 5. Implementation Plan

### Module Structure

```
src/
├── understanding/
│   ├── __init__.py
│   ├── processor.py          # Background processor
│   ├── extractor.py          # LLM entity extractor
│   ├── resolver.py           # Date/entity resolver
│   ├── scorer.py             # Quality scorer
│   └── prompt_templates.py   # Prompt templates
├── memory/
│   ├── __init__.py
│   ├── schema.py             # Enhanced memory schema
│   ├── store.py              # Memory storage
│   └── index.py              # Quality index
└── cli/
    └── commands.py           # nocl commands
```

### Step-by-Step Implementation

#### Step 1: Enhanced Schema (Day 1)
```python
# src/memory/schema.py
- Implement EnhancedMemory dataclass
- Implement Entity dataclass
- Implement PersonaType, MemoryQuality enums
- Add JSON serialization/deserialization
```

#### Step 2: Understanding LLM (Day 2-3)
```python
# src/understanding/extractor.py
- Implement entity extraction prompt
- Call LLM (qwen-3b-coder or configured model)
- Parse JSON output
- Validate schema
```

#### Step 3: Date/Entity Resolver (Day 3-4)
```python
# src/understanding/resolver.py
- Resolve relative dates (today, yesterday, tomorrow, next week)
- Resolve pronouns (I, me, my, we, us)
- Normalize entities (locations, organizations)
```

#### Step 4: Quality Scorer (Day 4-5)
```python
# src/understanding/scorer.py
- Implement quality scoring logic
- Confidence calculation
- Auto-reject threshold (quality < 2)
```

#### Step 5: Background Processor (Day 5-6)
```python
# src/understanding/processor.py
- Message counter (trigger every 20 messages)
- Fetch session messages
- Call understanding pipeline
- Store enhanced memories
- Error handling + retry logic
```

#### Step 6: Storage Integration (Day 6-7)
```python
# src/memory/store.py
- Update store() to accept EnhancedMemory
- Add quality index
- Add persona partitioning
- Add expiration handling
```

#### Step 7: CLI Commands (Day 7-8)
```python
# src/cli/commands.py
- nocl.py process --batch 20  # Manual trigger
- nocl.py quality --show      # Show quality scores
- nocl.py persona --list      # List persona memories
- nocl.py verify --id <id>    # Verify a memory
```

#### Step 8: Testing & Benchmark (Day 8-10)
```python
# tests/test_understanding.py
- Test entity extraction accuracy
- Test date resolution
- Test quality scoring
- Create 20 trick questions benchmark
```

---

## 6. Configuration

### Config File: `config/understanding_config.yaml`

```yaml
understanding:
  # Processing trigger
  trigger:
    type: "message_count"  # or "cron"
    message_count: 20      # Process every N messages
    cron_schedule: null    # e.g., "*/30 * * * *" for every 30 min
  
  # LLM settings
  llm:
    model: "qwen-local/qwen-3b-coder"  # Cheap, fast model
    fallback_models:
      - "ollama/qwen3-coder-next"
      - "bailian-api/qwen-flash"
    max_tokens: 2000
    temperature: 0.1  # Low temp for consistency
    timeout_seconds: 30
  
  # Quality thresholds
  quality:
    auto_store_threshold: 3    # Only store if quality >= 3
    auto_reject_threshold: 2   # Auto-reject if quality < 2
    verification_threshold: 4  # Flag for verification if quality >= 4
  
  # Persona settings
  persona:
    default: "personal"
    detection_rules:
      technical_keywords: ["code", "bug", "api", "function", "deploy"]
      social_keywords: ["group", "chat", "team", "meeting"]
      personal_keywords: ["I", "my", "today", "plan", "want"]
  
  # Expiration defaults
  expiration:
    default_ttl_hours: null    # No expiration by default
    temporary_ttl_hours: 24    # For temporary facts
    session_ttl_hours: 12      # For session context
  
  # Performance
  performance:
    batch_size: 20             # Messages per batch
    max_concurrent: 2          # Max parallel processors
    cache_enabled: true        # Cache LLM results
    cache_ttl_hours: 1         # Cache duration
```

---

## 7. API Changes

### New CLI Commands

```bash
# Manual trigger for processing
nocl.py process --session <session_id> --batch-size 20

# Show memory quality stats
nocl.py quality --show
nocl.py quality --persona personal
nocl.py quality --min-score 4

# List memories by persona
nocl.py persona --list
nocl.py persona --show personal
nocl.py persona --show technical

# Verify/correct a memory
nocl.py verify --id <memory_id> --score 5
nocl.py verify --id <memory_id> --reject

# Export memories for benchmark
nocl.py export --format json --out memories.json
```

### Python API

```python
from neural_openclaw import UnderstandingProcessor, EnhancedMemory

# Initialize processor
processor = UnderstandingProcessor(
    model="qwen-local/qwen-3b-coder",
    trigger_count=20,
    quality_threshold=3
)

# Process a batch of messages
messages = [...]  # Last 20 messages
memories = await processor.process_batch(messages)

# Store enhanced memory
await memory_store.store(memories[0])

# Query by quality
high_quality = await memory_store.query(
    min_quality=4,
    persona="personal"
)
```

---

## 8. Testing & Benchmark

### Benchmark Design

Based on Reddit post recommendation: **20 trick questions**

#### Example Questions

1. **Date Resolution:**
   - Q: "When did I say I was going shopping?"
   - Expected: "2026-02-26" (not "today")

2. **Entity Resolution:**
   - Q: "Who is going shopping?"
   - Expected: "dat911zz" (not "I")

3. **Context Understanding:**
   - Q: "What laptop am I considering?"
   - Expected: "MacBook Pro or Dell XPS"

4. **Quality Filtering:**
   - Q: "Show me high-confidence plans"
   - Expected: Only memories with quality >= 4

5. **Persona Separation:**
   - Q: "What technical decisions did I make?"
   - Expected: Only memories with persona="technical"

### Test Suite

```python
# tests/test_benchmark.py

class TestMemoryBenchmark:
    def setup_method(self):
        self.benchmark_questions = load_20_trick_questions()
        self.expected_answers = load_expected_answers()
    
    def test_date_resolution_accuracy(self):
        # Test all date-related questions
        accuracy = run_benchmark("date_resolution")
        assert accuracy >= 0.90  # Target: 90%
    
    def test_entity_resolution_accuracy(self):
        accuracy = run_benchmark("entity_resolution")
        assert accuracy >= 0.85  # Target: 85%
    
    def test_quality_filtering_accuracy(self):
        accuracy = run_benchmark("quality_filtering")
        assert accuracy >= 0.80  # Target: 80%
    
    def test_overall_benchmark(self):
        accuracy = run_full_benchmark()
        assert accuracy >= 0.80  # Target: 80% overall
```

### Performance Metrics

| Metric | Baseline | Target (Phase 1) | Measurement |
|--------|----------|------------------|-------------|
| Date Resolution Accuracy | 0% | 90% | Benchmark Q1-5 |
| Entity Resolution Accuracy | 0% | 85% | Benchmark Q6-10 |
| Quality Score Correlation | N/A | 0.8 | vs human ratings |
| Processing Latency | N/A | <5s per batch | Time per 20 msgs |
| Token Efficiency | Baseline | +15% | Compare token usage |

---

## 9. Rollout Plan

### Phase 1a: Core Implementation (Week 1)
- [ ] Enhanced schema
- [ ] Understanding LLM integration
- [ ] Date/entity resolver
- [ ] Quality scorer

### Phase 1b: Integration (Week 2)
- [ ] Background processor
- [ ] Storage integration
- [ ] CLI commands
- [ ] Configuration

### Phase 1c: Testing (Week 3)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Benchmark suite
- [ ] Performance testing

### Phase 1d: Deployment (Week 4)
- [ ] Documentation
- [ ] User guide
- [ ] Migration guide (if needed)
- [ ] Release v2.0.0

---

## 10. Success Criteria

Phase 1 is complete when:

- [ ] ✅ Understanding Layer processes 20-message batches
- [ ] ✅ Date resolution accuracy >= 90% (benchmark)
- [ ] ✅ Entity resolution accuracy >= 85% (benchmark)
- [ ] ✅ Quality scoring implemented (1-5 stars)
- [ ] ✅ Persona categorization working (personal/technical/social)
- [ ] ✅ CLI commands functional
- [ ] ✅ All tests passing
- [ ] ✅ Documentation complete

---

## 11. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM extraction errors | High | Schema validation + retry logic |
| Date resolution ambiguity | Medium | Conservative confidence scoring |
| Processing latency | Medium | Async processing, cheap model |
| Token cost increase | Low | Batch processing, local LLM |
| Memory schema breaking changes | High | Backward-compatible migration |

---

## 12. Future Phases

### Phase 2: Quality Improvements
- User feedback loop (verify/correct memories)
- Auto-rejection of low-quality memories
- Memory deduplication

### Phase 3: Persona-based Memory
- Separate storage per persona
- Persona-aware retrieval
- Context switching

### Phase 4: Advanced Features
- Causal chain extraction
- Relationship mapping
- Predictive suggestions

---

**Document Status:** Ready for Implementation  
**Next Action:** Begin Step 1 (Enhanced Schema)  
**Estimated Timeline:** 4 weeks  
**Priority:** 🔴 Critical
