# 🏛️ HỘI NGHỊ DIÊN HỒNG - BÁO CÁO SCHEMA DESIGN
## NeuralOpenClaw 2.0 Enhanced Memory Architecture

**Người review:** @Database-Architect (Tùng)  
**Ngày:** 2026-02-26  
**Thời gian review:** 15 phút  
**Status:** ✅ Complete

---

## 1. TỔNG QUAN

Đã review phần **Data Schema** trong `/docs/02-phase1-spec.md` và đánh giá kiến trúc Enhanced Memory cho Phase 1.

### Current State
- ✅ Spec đã định nghĩa rõ ràng các thành phần chính
- ✅ Có dataclass, enums, JSON format mẫu
- ❌ Chưa implement thực tế (file `src/memory/schema.py` chưa tồn tại)
- ❌ Chưa có indexing strategy cụ thể

---

## 2. ĐÁNH GIÁ SCHEMA HIỆN TẠI

### 2.1 Entity Dataclass

```python
@dataclass
class Entity:
    type: Literal["person", "location", "organization", "date", "action", "object"]
    value: str
    resolved_value: Optional[str] = None
    confidence: float = 1.0
```

**✅ Ưu điểm:**
- Đơn giản, dễ serialize
- Có `resolved_value` cho date/pronoun resolution
- Confidence score per entity

**⚠️ Thiếu:**
- ❌ Không có `entity_id` để deduplication
- ❌ Không có `source_text` (original span trong message)
- ❌ Không có `relations` (quan hệ giữa các entities)
- ❌ `type` quá hạn chế - thiếu "event", "concept", "metric"

**📋 Đề xuất thêm:**
```python
@dataclass
class Entity:
    entity_id: str                    # NEW: UUID for deduplication
    type: EntityType                  # NEW: Enum thay vì Literal
    value: str
    resolved_value: Optional[str] = None
    confidence: float = 1.0
    source_text: Optional[str] = None # NEW: Original text span
    char_start: Optional[int] = None  # NEW: Position in source
    char_end: Optional[int] = None    # NEW: Position in source
    relations: List[EntityRelation] = field(default_factory=list)  # NEW
    metadata: Dict[str, Any] = field(default_factory=dict)  # NEW: Flexible extensibility
```

### 2.2 EnhancedMemory Dataclass

```python
@dataclass
class EnhancedMemory:
    content: str
    summary: str
    entities: List[Entity]
    resolved_date: Optional[datetime]
    resolved_person: Optional[str]
    quality_score: MemoryQuality
    confidence: float
    persona: PersonaType
    category: str
    created_at: datetime
    source_session: str
    message_count: int
    verified: bool = False
    verification_count: int = 0
    last_accessed: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_permanent: bool = False
```

**✅ Ưu điểm:**
- Full lifecycle tracking (created, accessed, expires)
- Quality + confidence separation (good design!)
- Verification workflow support
- Persona-based categorization

**⚠️ Thiếu:**
- ❌ Không có `memory_id` (primary key)
- ❌ Không có `version` cho optimistic locking
- ❌ Không có `tags` cho flexible categorization
- ❌ `category` là string tự do → khó query
- ❌ Không có `parent_id` cho hierarchical memories
- ❌ Không có `embedding_id` reference cho vector search

**📋 Đề xuất thêm:**
```python
@dataclass
class EnhancedMemory:
    # Identity
    memory_id: str                    # NEW: UUID primary key
    version: int = 1                  # NEW: Optimistic locking
    
    # Core content
    content: str
    summary: str
    content_hash: str = None          # NEW: Deduplication
    
    # Entities
    entities: List[Entity]
    
    # Resolution
    resolved_date: Optional[datetime]
    resolved_person: Optional[str]
    resolved_location: Optional[str] = None  # NEW
    
    # Quality
    quality_score: MemoryQuality
    confidence: float
    quality_reasoning: str = None     # NEW: Why this score?
    
    # Categorization
    persona: PersonaType
    category: MemoryCategory          # NEW: Enum thay vì str
    tags: List[str] = field(default_factory=list)  # NEW
    
    # Relationships
    parent_id: Optional[str] = None   # NEW: Hierarchical
    related_memory_ids: List[str] = field(default_factory=list)  # NEW
    
    # Vector search
    embedding_id: Optional[str] = None  # NEW: Reference to vector store
    embedding_model: Optional[str] = None  # NEW
    
    # Metadata
    created_at: datetime
    updated_at: datetime = None       # NEW
    source_session: str
    message_ids: List[str] = None     # NEW: Original message references
    message_count: int
    
    # Validation
    verified: bool = False
    verified_by: Optional[str] = None # NEW: Who verified?
    verified_at: Optional[datetime] = None  # NEW
    verification_count: int = 0
    
    # Access tracking
    last_accessed: Optional[datetime] = None
    access_count: int = 0             # NEW: For LRU
    
    # Expiration
    expires_at: Optional[datetime] = None
    is_permanent: bool = False
    ttl_policy: str = None            # NEW: "session", "day", "week", "never"
    
    # Audit
    created_by: str = "system"        # NEW
    modification_history: List[ModificationRecord] = field(default_factory=list)  # NEW
```

### 2.3 Enums

**PersonaType:** ✅ OK
```python
class PersonaType(Enum):
    PERSONAL = "personal"
    TECHNICAL = "technical"
    SOCIAL = "social"
```

**MemoryQuality:** ✅ OK
```python
class MemoryQuality(Enum):
    EXCELLENT = 5
    GOOD = 4
    FAIR = 3
    POOR = 2
    REJECT = 1
```

**📋 Đề xuất thêm enums:**
```python
class EntityType(Enum):
    PERSON = "person"
    LOCATION = "location"
    ORGANIZATION = "org"
    DATE = "date"
    TIME = "time"              # NEW
    ACTION = "action"
    OBJECT = "object"
    EVENT = "event"            # NEW
    CONCEPT = "concept"        # NEW
    METRIC = "metric"          # NEW
    CODE = "code"              # NEW
    FILE = "file"              # NEW
    URL = "url"                # NEW

class MemoryCategory(Enum):
    DECISION = "decision"
    FACT = "fact"
    EVENT = "event"
    PLAN = "plan"
    PREFERENCE = "preference"
    CONTEXT = "context"
    INSIGHT = "insight"
    QUESTION = "question"
    TASK = "task"
    ERROR = "error"

class RelationType(Enum):        # NEW: For entity relations
    PART_OF = "part_of"
    LOCATED_AT = "located_at"
    WORKS_FOR = "works_for"
    CREATED = "created"
    USED = "used"
    MENTIONED = "mentioned"
    RELATED_TO = "related_to"
```

---

## 3. PERFORMANCE IMPLICATIONS

### 3.1 Storage Size Estimate

| Field | Avg Size | Notes |
|-------|----------|-------|
| memory_id | 36 bytes | UUID string |
| content | 500 bytes | Avg message batch |
| summary | 200 bytes | LLM compressed |
| entities (5 per memory) | 800 bytes | 5 × 160 bytes |
| metadata | 200 bytes | JSON |
| timestamps | 40 bytes | 4 × ISO8601 |
| **Total per memory** | **~1.8 KB** | |

**Với 10,000 memories:** ~18 MB (SQLite thoải mái)

### 3.2 Query Patterns & Indexing Strategy

#### Critical Queries:

```sql
-- Q1: Get high-quality memories by persona
SELECT * FROM memories 
WHERE persona = ? AND quality_score >= ?
ORDER BY created_at DESC;

-- Q2: Get memories for specific date range
SELECT * FROM memories 
WHERE resolved_date BETWEEN ? AND ?
ORDER BY quality_score DESC;

-- Q3: Get unverified low-quality memories for review
SELECT * FROM memories 
WHERE verified = false AND quality_score < 3
ORDER BY created_at ASC;

-- Q4: Get recently accessed memories (LRU cache)
SELECT * FROM memories 
WHERE last_accessed > ?
ORDER BY last_accessed DESC;

-- Q5: Search by entity value
SELECT * FROM memories 
WHERE json_extract(entities, '$[*].value') LIKE ?;

-- Q6: Get expired memories for cleanup
SELECT * FROM memories 
WHERE expires_at < ? AND is_permanent = false;

-- Q7: Deduplication check
SELECT * FROM memories 
WHERE content_hash = ?;
```

#### Recommended Indexes:

```sql
-- Composite indexes for common queries
CREATE INDEX idx_persona_quality ON memories(persona, quality_score DESC);
CREATE INDEX idx_persona_category ON memories(persona, category);
CREATE INDEX idx_quality_verified ON memories(quality_score, verified);
CREATE INDEX idx_resolved_date ON memories(resolved_date) WHERE resolved_date IS NOT NULL;
CREATE INDEX idx_expires_at ON memories(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_last_accessed ON memories(last_accessed) WHERE last_accessed IS NOT NULL;
CREATE INDEX idx_content_hash ON memories(content_hash);  -- Deduplication
CREATE INDEX idx_source_session ON memories(source_session);

-- Partial indexes for performance
CREATE INDEX idx_high_quality ON memories(persona, quality_score) 
    WHERE quality_score >= 4;
    
CREATE INDEX idx_pending_verification ON memories(verified, quality_score) 
    WHERE verified = false AND quality_score >= 3;
```

### 3.3 JSON Entity Storage Trade-offs

**Option A: JSON Column (Recommended for Phase 1)**
```python
# Store entities as JSON in single column
entities_json = json.dumps([e.__dict__ for e in entities])
```
- ✅ Simple schema
- ✅ Flexible entity structure
- ❌ Slower entity-based queries
- ❌ Cannot index individual entity fields

**Option B: Normalized Tables (Phase 2)**
```sql
CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    memory_id TEXT REFERENCES memories(memory_id),
    entity_type TEXT,
    value TEXT,
    resolved_value TEXT,
    confidence REAL
);
```
- ✅ Fast entity queries
- ✅ Can index entity fields
- ❌ More complex schema
- ❌ More JOINs

**📋 Recommendation:** Dùng **Option A cho Phase 1**, migrate sang Option B khi cần entity query performance.

---

## 4. USE CASE COVERAGE ANALYSIS

| Use Case | Schema Support | Gap |
|----------|---------------|-----|
| Date resolution ("today" → 2026-02-26) | ✅ `resolved_date` | None |
| Pronoun resolution ("I" → dat911zz) | ✅ `resolved_person` | None |
| Quality-based retrieval | ✅ `quality_score` + index | Need `quality_reasoning` |
| Persona separation | ✅ `persona` enum | None |
| Memory expiration | ✅ `expires_at`, `is_permanent` | Need `ttl_policy` |
| Verification workflow | ✅ `verified`, `verification_count` | Need `verified_by`, `verified_at` |
| Deduplication | ❌ | Need `content_hash` |
| Entity search | ⚠️ JSON query | Need normalized table (Phase 2) |
| Hierarchical memories | ❌ | Need `parent_id` |
| Related memories | ❌ | Need `related_memory_ids` |
| Vector search | ❌ | Need `embedding_id` |
| Audit trail | ❌ | Need `modification_history` |

---

## 5. RECOMMENDATIONS

### 5.1 Immediate Changes (Phase 1a)

**Priority 1 - Must Have:**
1. ✅ Add `memory_id: str` (UUID) as primary key
2. ✅ Add `content_hash: str` for deduplication
3. ✅ Convert `category: str` → `MemoryCategory` enum
4. ✅ Add `updated_at: datetime` for audit
5. ✅ Add `tags: List[str]` for flexible categorization
6. ✅ Add `quality_reasoning: str` for transparency

**Priority 2 - Should Have:**
7. Add `entity_id` to Entity dataclass
8. Add `source_text` to Entity for debugging
9. Add `message_ids: List[str]` to trace back to source
10. Add `access_count: int` for better LRU

### 5.2 Future Enhancements (Phase 2+)

**Phase 2 - Entity Relationships:**
- Normalize entities to separate table
- Add `EntityRelation` dataclass
- Add graph traversal queries

**Phase 3 - Vector Search:**
- Add `embedding_id` and `embedding_model` fields
- Integrate with vector database (Qdrant/Chroma)
- Hybrid search (keyword + semantic)

**Phase 4 - Advanced Features:**
- Hierarchical memories (`parent_id`)
- Memory versioning (`version` field)
- Full audit trail (`modification_history`)

### 5.3 Implementation Checklist

```python
# src/memory/schema.py (new file)

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import hashlib
import json

class PersonaType(Enum):
    PERSONAL = "personal"
    TECHNICAL = "technical"
    SOCIAL = "social"

class MemoryQuality(Enum):
    EXCELLENT = 5
    GOOD = 4
    FAIR = 3
    POOR = 2
    REJECT = 1

class EntityType(Enum):
    PERSON = "person"
    LOCATION = "location"
    ORGANIZATION = "org"
    DATE = "date"
    TIME = "time"
    ACTION = "action"
    OBJECT = "object"
    EVENT = "event"
    CONCEPT = "concept"
    METRIC = "metric"
    CODE = "code"
    FILE = "file"
    URL = "url"

class MemoryCategory(Enum):
    DECISION = "decision"
    FACT = "fact"
    EVENT = "event"
    PLAN = "plan"
    PREFERENCE = "preference"
    CONTEXT = "context"
    INSIGHT = "insight"
    QUESTION = "question"
    TASK = "task"
    ERROR = "error"

@dataclass
class Entity:
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EntityType = EntityType.OBJECT
    value: str = ""
    resolved_value: Optional[str] = None
    confidence: float = 1.0
    source_text: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "type": self.type.value,
            "value": self.value,
            "resolved_value": self.resolved_value,
            "confidence": self.confidence,
            "source_text": self.source_text,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        return cls(
            entity_id=data.get("entity_id", str(uuid.uuid4())),
            type=EntityType(data.get("type", "object")),
            value=data.get("value", ""),
            resolved_value=data.get("resolved_value"),
            confidence=data.get("confidence", 1.0),
            source_text=data.get("source_text"),
            char_start=data.get("char_start"),
            char_end=data.get("char_end"),
            metadata=data.get("metadata", {})
        )

@dataclass
class EnhancedMemory:
    # Identity
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    
    # Core content
    content: str = ""
    summary: str = ""
    content_hash: Optional[str] = None
    
    # Entities
    entities: List[Entity] = field(default_factory=list)
    
    # Resolution
    resolved_date: Optional[datetime] = None
    resolved_person: Optional[str] = None
    resolved_location: Optional[str] = None
    
    # Quality
    quality_score: MemoryQuality = MemoryQuality.FAIR
    confidence: float = 0.5
    quality_reasoning: Optional[str] = None
    
    # Categorization
    persona: PersonaType = PersonaType.PERSONAL
    category: MemoryCategory = MemoryCategory.FACT
    tags: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    source_session: str = ""
    message_ids: List[str] = field(default_factory=list)
    message_count: int = 0
    
    # Validation
    verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_count: int = 0
    
    # Access tracking
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    
    # Expiration
    expires_at: Optional[datetime] = None
    is_permanent: bool = False
    ttl_policy: Optional[str] = None
    
    # Audit
    created_by: str = "system"
    
    def __post_init__(self):
        if self.content_hash is None and self.content:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "version": self.version,
            "content": self.content,
            "summary": self.summary,
            "content_hash": self.content_hash,
            "entities": [e.to_dict() for e in self.entities],
            "resolved_date": self.resolved_date.isoformat() if self.resolved_date else None,
            "resolved_person": self.resolved_person,
            "resolved_location": self.resolved_location,
            "quality_score": self.quality_score.value,
            "confidence": self.confidence,
            "quality_reasoning": self.quality_reasoning,
            "persona": self.persona.value,
            "category": self.category.value,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "source_session": self.source_session,
            "message_ids": self.message_ids,
            "message_count": self.message_count,
            "verified": self.verified,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verification_count": self.verification_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_permanent": self.is_permanent,
            "ttl_policy": self.ttl_policy,
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnhancedMemory":
        entities = [Entity.from_dict(e) for e in data.get("entities", [])]
        resolved_date = datetime.fromisoformat(data["resolved_date"]) if data.get("resolved_date") else None
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        verified_at = datetime.fromisoformat(data["verified_at"]) if data.get("verified_at") else None
        last_accessed = datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
        expires_at = datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        
        return cls(
            memory_id=data.get("memory_id", str(uuid.uuid4())),
            version=data.get("version", 1),
            content=data.get("content", ""),
            summary=data.get("summary", ""),
            content_hash=data.get("content_hash"),
            entities=entities,
            resolved_date=resolved_date,
            resolved_person=data.get("resolved_person"),
            resolved_location=data.get("resolved_location"),
            quality_score=MemoryQuality(data.get("quality_score", 3)),
            confidence=data.get("confidence", 0.5),
            quality_reasoning=data.get("quality_reasoning"),
            persona=PersonaType(data.get("persona", "personal")),
            category=MemoryCategory(data.get("category", "fact")),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=updated_at,
            source_session=data.get("source_session", ""),
            message_ids=data.get("message_ids", []),
            message_count=data.get("message_count", 0),
            verified=data.get("verified", False),
            verified_by=data.get("verified_by"),
            verified_at=verified_at,
            verification_count=data.get("verification_count", 0),
            last_accessed=last_accessed,
            access_count=data.get("access_count", 0),
            expires_at=expires_at,
            is_permanent=data.get("is_permanent", False),
            ttl_policy=data.get("ttl_policy"),
            created_by=data.get("created_by", "system")
        )
    
    def touch(self) -> None:
        """Update last_accessed and access_count."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
    
    def update(self, **kwargs) -> None:
        """Update fields and bump version."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        self.version += 1
```

---

## 6. KẾT LUẬN

### ✅ Schema hiện tại: 7/10
- Good foundation cho Phase 1
- Thiếu critical fields cho production use
- Chưa có indexing strategy

### 📋 Action Items:

| Priority | Task | Estimated Time |
|----------|------|----------------|
| 🔴 P0 | Create `src/memory/schema.py` với enhanced dataclasses | 2 hours |
| 🔴 P0 | Add database migration script for indexes | 1 hour |
| 🟡 P1 | Implement `content_hash` deduplication logic | 1 hour |
| 🟡 P1 | Add `quality_reasoning` field to LLM prompt | 30 min |
| 🟡 P1 | Update JSON storage format in spec | 30 min |
| 🟢 P2 | Plan entity normalization for Phase 2 | 1 hour |
| 🟢 P2 | Design vector search integration | 2 hours |

### 🎯 Recommendation:
**Proceed with Phase 1 implementation** nhưng áp dụng các changes trong mục **5.1 Immediate Changes** trước khi code. Điều này tránh refactor lớn sau này.

---

**Báo cáo hoàn thành.** Sẵn sàng cho discussion tại Hội Nghị Diên Hồng.

🏛️ *Database-Architect out.*
