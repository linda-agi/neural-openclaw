# 🏛️ HỘI NGHỊ DIÊN HỒNG - AUDIT PLAN & QUALITY VERIFICATION FRAMEWORK

**Role:** @Auditor-General - Tổng kiểm soát viên  
**Date:** 2026-02-26  
**Session:** agent:main:subagent:3d6a31f0-5b3d-48c2-9c9c-2b7e229a0ecb  
**Preparation Time:** 15 phút  

---

## 📋 EXECUTIVE SUMMARY

### Audit Scope
- **Documents Reviewed:**
  - ✅ `01-architecture-analysis.md` - Architecture comparison
  - ✅ `02-phase1-spec.md` - Phase 1 implementation spec
  - ✅ `03-roadmap.md` - Project roadmap

### Critical Findings
| Finding | Severity | Status |
|---------|----------|--------|
| Understanding Layer lacks verification mechanism | 🔴 Critical | Requires immediate attention |
| Quality scoring criteria too subjective | 🟡 High | Needs calibration framework |
| No hallucination detection in extraction pipeline | 🔴 Critical | Must add validation layer |
| Benchmark design incomplete (only 5 examples) | 🟡 High | Need full 20 questions |
| Success criteria lack statistical rigor | 🟡 Medium | Need confidence intervals |

---

## 🔍 PART 1: UNDERSTANDING LAYER VERIFICATION

### 1.1 How to Verify Understanding Layer Works Correctly?

**Current Design Flaw:**
```
Chat → Understanding LLM → Structured Output → Store
                              ❌
                    NO VALIDATION LAYER
```

**Proposed Verification Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│           Understanding Layer Verification Pipeline         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Chat Messages → Understanding LLM → Structured Output     │
│                                              │              │
│                                              ▼              │
│         ┌─────────────────────────────────────────────┐    │
│         │  Validation Layer (3-tier)                  │    │
│         │  1. Schema Validation (syntax)              │    │
│         │  2. Consistency Check (logic)               │    │
│         │  3. Cross-reference (facts)                 │    │
│         └─────────────────────────────────────────────┘    │
│                              │                              │
│                    ┌─────────┴─────────┐                   │
│                    ▼                   ▼                   │
│            ✅ Pass              ❌ Fail                    │
│            Store Memory        Flag for Review            │
│                                    │                      │
│                                    ▼                      │
│                          Human-in-the-loop                │
│                          (Bro verifies)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Verification Procedures

#### Tier 1: Schema Validation (Automated)
```python
# tests/verification/test_schema_validation.py

def validate_memory_schema(memory: EnhancedMemory) -> ValidationResult:
    """
    Validate memory against strict schema rules.
    """
    checks = [
        # Required fields
        ("content exists", memory.content is not None),
        ("summary exists", memory.summary is not None),
        ("entities list", isinstance(memory.entities, list)),
        ("quality score valid", memory.quality_score in range(1, 6)),
        ("persona valid", memory.persona in PersonaType),
        
        # Date resolution checks
        ("resolved_date is datetime", 
         isinstance(memory.resolved_date, datetime) if memory.resolved_date else True),
        
        # Confidence bounds
        ("confidence in [0,1]", 0 <= memory.confidence <= 1),
        
        # Entity validation
        ("all entities have type", all(e.type for e in memory.entities)),
        ("all entities have value", all(e.value for e in memory.entities)),
        ("entity confidence in [0,1]", all(0 <= e.confidence <= 1 for e in memory.entities)),
    ]
    
    return ValidationResult(
        passed=all(check[1] for check in checks),
        failed_checks=[check[0] for check in checks if not check[1]]
    )
```

#### Tier 2: Consistency Check (Automated)
```python
# tests/verification/test_consistency.py

def check_temporal_consistency(memory: EnhancedMemory) -> ValidationResult:
    """
    Check for temporal contradictions.
    """
    checks = []
    
    # Check 1: resolved_date should not be in the future (unless it's a plan)
    if memory.resolved_date and memory.category != "plan":
        checks.append(("not future date", memory.resolved_date <= datetime.now()))
    
    # Check 2: If "yesterday" mentioned, resolved_date should be yesterday
    # (requires original message text)
    
    # Check 3: Entity dates should be consistent
    date_entities = [e for e in memory.entities if e.type == "date"]
    if len(date_entities) > 1:
        # Multiple dates should not contradict
        checks.append(("dates consistent", verify_date_consistency(date_entities)))
    
    return ValidationResult(
        passed=all(check[1] for check in checks),
        failed_checks=[check[0] for check in checks if not check[1]]
    )


def check_entity_consistency(memory: EnhancedMemory) -> ValidationResult:
    """
    Check for entity contradictions.
    """
    checks = []
    
    # Check 1: Pronoun resolution should be consistent
    pronoun_entities = [e for e in memory.entities if e.value in ["I", "me", "my", "we"]]
    for entity in pronoun_entities:
        checks.append((
            f"pronoun '{entity.value}' resolved",
            entity.resolved_value is not None
        ))
    
    # Check 2: Same entity type should not have conflicting values
    # (e.g., two different "today" resolutions in same memory)
    
    return ValidationResult(
        passed=all(check[1] for check in checks),
        failed_checks=[check[0] for check in checks if not check[1]]
    )
```

#### Tier 3: Cross-reference Validation (Semi-automated)
```python
# tests/verification/test_cross_reference.py

def cross_reference_with_history(
    memory: EnhancedMemory, 
    memory_store: MemoryStore
) -> ValidationResult:
    """
    Check if new memory contradicts existing memories.
    """
    checks = []
    
    # Find related memories
    related = memory_store.find_related(
        entities=memory.entities,
        time_range=timedelta(days=7)
    )
    
    # Check for contradictions
    for existing in related:
        contradiction = detect_contradiction(memory, existing)
        if contradiction:
            checks.append((
                f"no contradiction with mem_{existing.id}",
                False
            ))
    
    return ValidationResult(
        passed=all(check[1] for check in checks),
        failed_checks=[check[0] for check in checks if not check[1]],
        conflicting_memories=[r.id for r in related if detect_contradiction(memory, r)]
    )
```

### 1.3 Verification Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Schema Validation Pass Rate | 100% | Automated tests |
| Consistency Check Pass Rate | ≥95% | Automated tests |
| Cross-reference Conflicts | <5% | Manual review |
| False Positive Rate | <10% | Human verification |
| Processing Overhead | <500ms | Performance profiling |

---

## ⭐ PART 2: QUALITY SCORING OBJECTIVITY

### 2.1 Current Quality Scoring Issues

**Problem:** Quality scoring guidelines are too subjective:
```
5 stars: Clear, unambiguous, verified facts
4 stars: High confidence, likely correct
3 stars: Moderate confidence, may need verification
2 stars: Low confidence, ambiguous
1 star: Very low confidence, contradictory
```

**Issues:**
- ❌ "Clear" vs "ambiguous" - subjective
- ❌ "High confidence" vs "moderate confidence" - no clear boundary
- ❌ No calibration against ground truth
- ❌ LLM may be overconfident or underconfident

### 2.2 Proposed Objective Quality Framework

#### Multi-dimensional Quality Score

```python
@dataclass
class QualityDimensions:
    # Dimension 1: Clarity (0-1)
    clarity_score: float        # Based on linguistic complexity
    
    # Dimension 2: Specificity (0-1)
    specificity_score: float    # Based on entity density
    
    # Dimension 3: Consistency (0-1)
    consistency_score: float    # Based on internal contradictions
    
    # Dimension 4: Verifiability (0-1)
    verifiability_score: float  # Can this be verified?
    
    # Dimension 5: Completeness (0-1)
    completeness_score: float   # Are all entities resolved?
    
    def calculate_overall(self) -> float:
        """Weighted average based on importance."""
        weights = {
            'clarity': 0.15,
            'specificity': 0.20,
            'consistency': 0.25,  # Most important
            'verifiability': 0.20,
            'completeness': 0.20
        }
        return (
            self.clarity_score * weights['clarity'] +
            self.specificity_score * weights['specificity'] +
            self.consistency_score * weights['consistency'] +
            self.verifiability_score * weights['verifiability'] +
            self.completeness_score * weights['completeness']
        )
```

#### Objective Scoring Rules

```python
# src/understanding/scorer.py

def calculate_clarity_score(text: str) -> float:
    """
    Measure linguistic clarity objectively.
    """
    # Factors:
    # - Sentence length (shorter = clearer)
    # - Ambiguous words count (fewer = clearer)
    # - Grammar correctness
    
    ambiguous_words = ['maybe', 'possibly', 'might', 'could', 'some', 'thing']
    ambiguous_count = sum(1 for word in ambiguous_words if word in text.lower())
    
    # Normalize: 0 ambiguous = 1.0, 5+ ambiguous = 0.0
    clarity = max(0, 1.0 - (ambiguous_count / 5))
    return clarity


def calculate_specificity_score(entities: List[Entity]) -> float:
    """
    Measure specificity based on entity resolution.
    """
    if not entities:
        return 0.5  # Neutral if no entities
    
    resolved_count = sum(1 for e in entities if e.resolved_value is not None)
    return resolved_count / len(entities)


def calculate_consistency_score(memory: EnhancedMemory) -> float:
    """
    Check internal consistency.
    """
    # Check for contradictions within the memory
    contradictions = detect_internal_contradictions(memory)
    
    # 0 contradictions = 1.0, 1+ contradictions = lower score
    return max(0, 1.0 - (len(contradictions) * 0.25))


def calculate_verifiability_score(entities: List[Entity]) -> float:
    """
    Can this memory be verified externally?
    """
    verifiable_types = ['date', 'location', 'organization', 'person']
    verifiable_count = sum(1 for e in entities if e.type in verifiable_types)
    
    return min(1.0, verifiable_count / 2)  # Need at least 2 verifiable entities


def calculate_completeness_score(memory: EnhancedMemory) -> float:
    """
    Check if all required fields are populated.
    """
    required_fields = ['content', 'summary', 'entities', 'persona', 'category']
    populated = sum(1 for field in required_fields if getattr(memory, field))
    
    return populated / len(required_fields)
```

#### Quality Score Calibration

```python
# tests/verification/test_quality_calibration.py

def calibrate_quality_scorer(
    test_memories: List[EnhancedMemory],
    human_ratings: List[int]
) -> CalibrationReport:
    """
    Compare LLM quality scores against human ratings.
    """
    from scipy.stats import pearsonr, spearmanr
    
    llm_scores = [m.quality_score for m in test_memories]
    
    # Calculate correlation
    pearson_corr, pearson_p = pearsonr(llm_scores, human_ratings)
    spearman_corr, spearman_p = spearmanr(llm_scores, human_ratings)
    
    # Calculate accuracy (within 1 star)
    accuracy = sum(
        1 for llm, human in zip(llm_scores, human_ratings)
        if abs(llm - human) <= 1
    ) / len(llm_scores)
    
    return CalibrationReport(
        pearson_correlation=pearson_corr,
        pearson_pvalue=pearson_p,
        spearman_correlation=spearman_corr,
        spearman_pvalue=spearman_p,
        accuracy_within_1_star=accuracy,
        mean_absolute_error=mean_absolute_error(llm_scores, human_ratings)
    )
```

### 2.3 Quality Scoring Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Pearson correlation with human ratings | ≥0.8 | Calibration test |
| Accuracy within 1 star | ≥85% | Calibration test |
| Mean absolute error | <0.8 stars | Calibration test |
| Inter-rater reliability (humans) | ≥0.9 | Human calibration |
| Score distribution balance | No skew | Statistical analysis |

---

## 📅 PART 3: DATE/ENTITY RESOLUTION ACCURACY

### 3.1 Date Resolution Accuracy Measurement

#### Test Cases for Date Resolution

```python
# tests/benchmark/test_date_resolution.py

DATE_RESOLUTION_TESTS = [
    # (input_text, current_date, expected_resolved_date)
    ("I went shopping today", "2026-02-26", "2026-02-26"),
    ("Yesterday I was at the mall", "2026-02-26", "2026-02-25"),
    ("Tomorrow I have a meeting", "2026-02-26", "2026-02-27"),
    ("Last Monday I coded", "2026-02-26", "2026-02-23"),  # Thu → last Mon
    ("Next Friday I'll deploy", "2026-02-26", "2026-03-06"),  # Thu → next Fri
    ("I worked on this 3 days ago", "2026-02-26", "2026-02-23"),
    ("The project started 2 weeks ago", "2026-02-26", "2026-02-12"),
    ("Meeting scheduled for next month", "2026-02-26", "2026-03-26"),
    ("I finished last year", "2026-02-26", "2025-12-31"),  # Approximate
    ("Born in 1990", "2026-02-26", "1990-01-01"),  # Year only
]

def test_date_resolution_accuracy() -> AccuracyReport:
    """
    Test date resolution against ground truth.
    """
    results = []
    
    for input_text, current_date, expected in DATE_RESOLUTION_TESTS:
        result = resolve_date(input_text, current_date)
        results.append({
            'input': input_text,
            'expected': expected,
            'actual': result.resolved_date,
            'correct': result.resolved_date == expected,
            'confidence': result.confidence
        })
    
    accuracy = sum(1 for r in results if r['correct']) / len(results)
    
    return AccuracyReport(
        total_tests=len(results),
        passed=sum(1 for r in results if r['correct']),
        accuracy=accuracy,
        details=results
    )
```

#### Date Resolution Edge Cases

```python
DATE_EDGE_CASES = [
    # Ambiguous cases that need special handling
    ("I'll do it next week", "2026-02-26", "2026-03-02"),  # Next Monday?
    ("See you in a few days", "2026-02-26", None),  # Too vague → None
    ("Sometime next month", "2026-02-26", None),  # Too vague → None
    ("I was there this morning", "2026-02-26", "2026-02-26"),  # Same day
    ("Last night I coded", "2026-02-26", "2026-02-25"),  # Previous day
    ("The other day", "2026-02-26", None),  # Too vague → None
    ("A while ago", "2026-02-26", None),  # Too vague → None
    ("Recently", "2026-02-26", None),  # Too vague → None
]
```

### 3.2 Entity Resolution Accuracy Measurement

#### Test Cases for Entity Resolution

```python
# tests/benchmark/test_entity_resolution.py

ENTITY_RESOLUTION_TESTS = [
    # (input_text, user_name, expected_entities)
    (
        "I am going shopping",
        "dat911zz",
        [
            {'type': 'person', 'value': 'I', 'resolved_value': 'dat911zz'},
            {'type': 'action', 'value': 'shopping', 'resolved_value': None}
        ]
    ),
    (
        "We decided to use SQLite",
        "dat911zz",
        [
            {'type': 'person', 'value': 'We', 'resolved_value': 'dat911zz + team'},
            {'type': 'object', 'value': 'SQLite', 'resolved_value': None}
        ]
    ),
    (
        "My laptop is broken",
        "dat911zz",
        [
            {'type': 'person', 'value': 'My', 'resolved_value': 'dat911zz'},
            {'type': 'object', 'value': 'laptop', 'resolved_value': None}
        ]
    ),
]

def test_entity_resolution_accuracy() -> AccuracyReport:
    """
    Test entity extraction and resolution.
    """
    results = []
    
    for input_text, user_name, expected_entities in ENTITY_RESOLUTION_TESTS:
        result = extract_entities(input_text, user_name)
        
        # Compare extracted vs expected
        correct = compare_entity_sets(result.entities, expected_entities)
        
        results.append({
            'input': input_text,
            'expected': expected_entities,
            'actual': result.entities,
            'correct': correct,
            'precision': calculate_precision(result.entities, expected_entities),
            'recall': calculate_recall(result.entities, expected_entities)
        })
    
    return AccuracyReport(
        total_tests=len(results),
        passed=sum(1 for r in results if r['correct']),
        accuracy=sum(1 for r in results if r['correct']) / len(results),
        avg_precision=mean(r['precision'] for r in results),
        avg_recall=mean(r['recall'] for r in results)
    )
```

### 3.3 Accuracy Measurement Framework

```python
# tests/benchmark/accuracy_framework.py

@dataclass
class AccuracyMetrics:
    # Date Resolution
    date_exact_match: float       # Exact date match
    date_approximate_match: float # Within acceptable range
    date_confidence_calibration: float  # Is confidence correlated with accuracy?
    
    # Entity Resolution
    entity_precision: float       # Correct entities / Total extracted
    entity_recall: float          # Correct entities / Total expected
    entity_f1: float              # Harmonic mean
    
    # Resolution Quality
    pronoun_resolution_rate: float    # % of pronouns resolved
    date_resolution_rate: float       # % of dates resolved
    location_resolution_rate: float   # % of locations resolved
    
    def overall_score(self) -> float:
        """Calculate overall accuracy score."""
        return (
            self.date_exact_match * 0.30 +
            self.entity_f1 * 0.40 +
            self.pronoun_resolution_rate * 0.15 +
            self.date_resolution_rate * 0.15
        )
```

---

## 🎯 PART 4: BENCHMARK - 20 TRICK QUESTIONS

### 4.1 Full Benchmark Design

**Purpose:** Test memory system's ability to answer questions that require:
- Date resolution
- Entity resolution
- Context understanding
- Quality filtering
- Persona separation

### 4.2 The 20 Trick Questions

```python
# tests/benchmark/20_trick_questions.py

BENCHMARK_QUESTIONS = [
    # ─────────────────────────────────────────────────────────────
    # DATE RESOLUTION (Questions 1-5)
    # ─────────────────────────────────────────────────────────────
    {
        'id': 'date_01',
        'category': 'date_resolution',
        'question': 'When did I say I was going shopping?',
        'context_messages': [
            '2026-02-26: I am going shopping at the mall today'
        ],
        'expected_answer': '2026-02-26',
        'wrong_answers': ['today', 'sometime this week', 'unknown'],
        'difficulty': 'easy'
    },
    {
        'id': 'date_02',
        'category': 'date_resolution',
        'question': 'When did I finish the project?',
        'context_messages': [
            '2026-02-24: I finished the project yesterday'
        ],
        'expected_answer': '2026-02-23',
        'wrong_answers': ['2026-02-24', 'yesterday', 'last week'],
        'difficulty': 'medium'
    },
    {
        'id': 'date_03',
        'category': 'date_resolution',
        'question': 'When is my next meeting?',
        'context_messages': [
            '2026-02-26 (Wednesday): I have a meeting next Friday'
        ],
        'expected_answer': '2026-03-06',
        'wrong_answers': ['2026-02-28', 'next week', 'Friday'],
        'difficulty': 'hard'
    },
    {
        'id': 'date_04',
        'category': 'date_resolution',
        'question': 'How long ago did I start learning Rust?',
        'context_messages': [
            '2026-02-19: I started learning Rust a week ago'
        ],
        'expected_answer': '2026-02-12 (approximately)',
        'wrong_answers': ['a week ago', '2026-02-19', 'unknown'],
        'difficulty': 'medium'
    },
    {
        'id': 'date_05',
        'category': 'date_resolution',
        'question': 'When did I visit the mall?',
        'context_messages': [
            '2026-02-25: I went to the mall yesterday',
            '2026-02-26: I went shopping at the mall today'
        ],
        'expected_answer': '2026-02-24 and 2026-02-26 (twice)',
        'wrong_answers': ['yesterday', '2026-02-25', 'once'],
        'difficulty': 'hard'
    },
    
    # ─────────────────────────────────────────────────────────────
    # ENTITY RESOLUTION (Questions 6-10)
    # ─────────────────────────────────────────────────────────────
    {
        'id': 'entity_01',
        'category': 'entity_resolution',
        'question': 'Who is going shopping?',
        'context_messages': [
            '2026-02-26: I am going shopping at the mall'
        ],
        'expected_answer': 'dat911zz',
        'wrong_answers': ['I', 'unknown', 'the user'],
        'difficulty': 'easy'
    },
    {
        'id': 'entity_02',
        'category': 'entity_resolution',
        'question': 'Who decided to use SQLite?',
        'context_messages': [
            '2026-02-25: We decided to use SQLite for the project'
        ],
        'expected_answer': 'dat911zz and team',
        'wrong_answers': ['We', 'the team', 'unknown'],
        'difficulty': 'medium'
    },
    {
        'id': 'entity_03',
        'category': 'entity_resolution',
        'question': 'What laptop am I considering?',
        'context_messages': [
            '2026-02-26: Need to buy a new laptop for work',
            '2026-02-26: Maybe MacBook Pro or Dell XPS'
        ],
        'expected_answer': 'MacBook Pro or Dell XPS',
        'wrong_answers': ['a laptop', 'MacBook', 'Dell'],
        'difficulty': 'easy'
    },
    {
        'id': 'entity_04',
        'category': 'entity_resolution',
        'question': 'Where am I working?',
        'context_messages': [
            '2026-02-26: Working at the coffee shop downtown'
        ],
        'expected_answer': 'coffee shop downtown',
        'wrong_answers': ['downtown', 'a shop', 'unknown'],
        'difficulty': 'medium'
    },
    {
        'id': 'entity_05',
        'category': 'entity_resolution',
        'question': 'Which API endpoint did I mention?',
        'context_messages': [
            '2026-02-25: The API endpoint is https://api.example.com/v2'
        ],
        'expected_answer': 'https://api.example.com/v2',
        'wrong_answers': ['api.example.com', 'https://api.example.com', 'unknown'],
        'difficulty': 'easy'
    },
    
    # ─────────────────────────────────────────────────────────────
    # CONTEXT UNDERSTANDING (Questions 11-15)
    # ─────────────────────────────────────────────────────────────
    {
        'id': 'context_01',
        'category': 'context_understanding',
        'question': 'Why did I choose SQLite?',
        'context_messages': [
            '2026-02-25: Using SQLite because it is lightweight and portable'
        ],
        'expected_answer': 'lightweight and portable',
        'wrong_answers': ['because it is fast', 'unknown', 'no reason given'],
        'difficulty': 'easy'
    },
    {
        'id': 'context_02',
        'category': 'context_understanding',
        'question': 'What is my plan for the weekend?',
        'context_messages': [
            '2026-02-26 (Wednesday): This weekend I will finish the project',
            '2026-02-26 (Wednesday): Then relax on Sunday'
        ],
        'expected_answer': 'Finish project, then relax on Sunday',
        'wrong_answers': ['work', 'relax', 'unknown'],
        'difficulty': 'medium'
    },
    {
        'id': 'context_03',
        'category': 'context_understanding',
        'question': 'What problem am I trying to solve?',
        'context_messages': [
            '2026-02-26: The current memory system cannot resolve dates',
            '2026-02-26: Need to add an understanding layer'
        ],
        'expected_answer': 'Memory system cannot resolve dates',
        'wrong_answers': ['add understanding layer', 'unknown', 'no problem'],
        'difficulty': 'medium'
    },
    {
        'id': 'context_04',
        'category': 'context_understanding',
        'question': 'What tools am I using for this project?',
        'context_messages': [
            '2026-02-25: Using Python for the backend',
            '2026-02-26: And React for the frontend'
        ],
        'expected_answer': 'Python and React',
        'wrong_answers': ['Python', 'React', 'unknown'],
        'difficulty': 'easy'
    },
    {
        'id': 'context_05',
        'category': 'context_understanding',
        'question': 'What is blocking my progress?',
        'context_messages': [
            '2026-02-26: Waiting for API access approval',
            '2026-02-26: Cannot proceed without it'
        ],
        'expected_answer': 'Waiting for API access approval',
        'wrong_answers': ['no blocker', 'unknown', 'technical issue'],
        'difficulty': 'medium'
    },
    
    # ─────────────────────────────────────────────────────────────
    # QUALITY FILTERING (Questions 16-17)
    # ─────────────────────────────────────────────────────────────
    {
        'id': 'quality_01',
        'category': 'quality_filtering',
        'question': 'Show me high-confidence facts about my plans',
        'context_messages': [
            '2026-02-26: I will definitely meet with Bro tomorrow (quality: 5)',
            '2026-02-26: Maybe I will go to the gym (quality: 2)',
            '2026-02-26: I might visit the mall (quality: 3)'
        ],
        'expected_answer': 'Meet with Bro tomorrow',
        'wrong_answers': ['go to the gym', 'visit the mall', 'all plans'],
        'filter': {'min_quality': 4},
        'difficulty': 'medium'
    },
    {
        'id': 'quality_02',
        'category': 'quality_filtering',
        'question': 'What decisions have I verified?',
        'context_messages': [
            '2026-02-25: Using SQLite (verified: true)',
            '2026-02-26: Using PostgreSQL (verified: false)',
            '2026-02-26: Using MongoDB (verified: true)'
        ],
        'expected_answer': 'Using SQLite and MongoDB',
        'wrong_answers': ['Using PostgreSQL', 'all decisions', 'none'],
        'filter': {'verified': True},
        'difficulty': 'easy'
    },
    
    # ─────────────────────────────────────────────────────────────
    # PERSONA SEPARATION (Questions 18-19)
    # ─────────────────────────────────────────────────────────────
    {
        'id': 'persona_01',
        'category': 'persona_separation',
        'question': 'What technical decisions did I make?',
        'context_messages': [
            '2026-02-25 [technical]: Using SQLite for storage',
            '2026-02-26 [technical]: Deploying to AWS',
            '2026-02-26 [personal]: Going shopping today'
        ],
        'expected_answer': 'Using SQLite, Deploying to AWS',
        'wrong_answers': ['Going shopping', 'all decisions', 'none'],
        'filter': {'persona': 'technical'},
        'difficulty': 'easy'
    },
    {
        'id': 'persona_02',
        'category': 'persona_separation',
        'question': 'What are my personal plans?',
        'context_messages': [
            '2026-02-26 [personal]: Shopping at the mall',
            '2026-02-26 [personal]: Dinner with friends',
            '2026-02-26 [technical]: Code review meeting'
        ],
        'expected_answer': 'Shopping at the mall, Dinner with friends',
        'wrong_answers': ['Code review meeting', 'all plans', 'none'],
        'filter': {'persona': 'personal'},
        'difficulty': 'easy'
    },
    
    # ─────────────────────────────────────────────────────────────
    # COMPLEX REASONING (Question 20)
    # ─────────────────────────────────────────────────────────────
    {
        'id': 'complex_01',
        'category': 'complex_reasoning',
        'question': 'When did I first mention the mall, and what was my plan?',
        'context_messages': [
            '2026-02-24: Thinking about going to the mall',
            '2026-02-25: I went to the mall yesterday',
            '2026-02-26: Going to the mall again today'
        ],
        'expected_answer': 'First mentioned on 2026-02-24, plan was to think about going',
        'wrong_answers': ['2026-02-25', '2026-02-26', 'unknown'],
        'difficulty': 'hard'
    }
]
```

### 4.3 Benchmark Scoring System

```python
# tests/benchmark/scoring.py

@dataclass
class BenchmarkResult:
    question_id: str
    category: str
    expected: str
    actual: str
    is_correct: bool
    confidence: float
    time_ms: float

def calculate_benchmark_score(results: List[BenchmarkResult]) -> BenchmarkReport:
    """
    Calculate comprehensive benchmark score.
    """
    by_category = defaultdict(list)
    for r in results:
        by_category[r.category].append(r)
    
    report = BenchmarkReport(
        total_questions=len(results),
        correct=sum(1 for r in results if r.is_correct),
        overall_accuracy=sum(1 for r in results if r.is_correct) / len(results),
        
        # By category
        date_resolution_accuracy=category_accuracy(by_category['date_resolution']),
        entity_resolution_accuracy=category_accuracy(by_category['entity_resolution']),
        context_understanding_accuracy=category_accuracy(by_category['context_understanding']),
        quality_filtering_accuracy=category_accuracy(by_category['quality_filtering']),
        persona_separation_accuracy=category_accuracy(by_category['persona_separation']),
        complex_reasoning_accuracy=category_accuracy(by_category['complex_reasoning']),
        
        # By difficulty
        easy_accuracy=difficulty_accuracy(results, 'easy'),
        medium_accuracy=difficulty_accuracy(results, 'medium'),
        hard_accuracy=difficulty_accuracy(results, 'hard'),
        
        # Performance
        avg_response_time_ms=mean(r.time_ms for r in results),
        
        # Confidence calibration
        confidence_correlation=calculate_confidence_calibration(results)
    )
    
    return report
```

### 4.4 Success Criteria for Benchmark

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Overall Accuracy | ≥80% | <70% = Fail |
| Date Resolution | ≥90% | <80% = Fail |
| Entity Resolution | ≥85% | <75% = Fail |
| Context Understanding | ≥80% | <70% = Fail |
| Quality Filtering | ≥85% | <75% = Fail |
| Persona Separation | ≥90% | <80% = Fail |
| Complex Reasoning | ≥70% | <60% = Fail |
| Response Time | <5s avg | >10s = Warning |

---

## 🛡️ PART 5: STRICT HONESTY CHECK

### 5.1 Potential Hallucination Risks

#### Risk Categories

```python
# src/understanding/hallucination_detection.py

HALLUCINATION_RISKS = [
    {
        'risk_id': 'H001',
        'category': 'date_fabrication',
        'description': 'LLM invents specific dates when input is vague',
        'example': {
            'input': 'I went shopping recently',
            'hallucinated_output': {'resolved_date': '2026-02-20'},
            'correct_output': {'resolved_date': None, 'confidence': 0.3}
        },
        'detection': 'Check if input contains vague temporal markers',
        'mitigation': 'Return None for vague dates, low confidence'
    },
    {
        'risk_id': 'H002',
        'category': 'entity_invention',
        'description': 'LLM invents entities not mentioned in text',
        'example': {
            'input': 'I bought a laptop',
            'hallucinated_output': {'entities': [{'type': 'object', 'value': 'MacBook Pro'}]},
            'correct_output': {'entities': [{'type': 'object', 'value': 'laptop'}]}
        },
        'detection': 'Cross-check entities against input text',
        'mitigation': 'Only extract explicitly mentioned entities'
    },
    {
        'risk_id': 'H003',
        'category': 'confidence_inflation',
        'description': 'LLM assigns high confidence to uncertain extractions',
        'example': {
            'input': 'Maybe I will go shopping',
            'hallucinated_output': {'confidence': 0.95},
            'correct_output': {'confidence': 0.4}
        },
        'detection': 'Check for uncertainty markers in input',
        'mitigation': 'Reduce confidence for uncertain language'
    },
    {
        'risk_id': 'H004',
        'category': 'context_mixing',
        'description': 'LLM mixes information from different sessions',
        'example': {
            'input': 'Session A: I like coffee',
            'hallucinated_output': {'persona': 'technical', 'content': 'I like coffee'},
            'correct_output': {'persona': 'personal', 'content': 'I like coffee'}
        },
        'detection': 'Verify session context matches persona',
        'mitigation': 'Pass explicit session context to LLM'
    },
    {
        'risk_id': 'H005',
        'category': 'false_verification',
        'description': 'LLM marks unverified info as verified',
        'example': {
            'input': 'I think SQLite is good',
            'hallucinated_output': {'verified': True},
            'correct_output': {'verified': False}
        },
        'detection': 'Check for uncertainty markers',
        'mitigation': 'Default verified=False unless explicit confirmation'
    }
]
```

### 5.2 Hallucination Detection Procedures

#### Procedure 1: Input-Output Consistency Check

```python
def detect_hallucination_input_output(
    input_text: str,
    output_memory: EnhancedMemory
) -> HallucinationReport:
    """
    Check if output is consistent with input.
    """
    issues = []
    
    # Check 1: All extracted entities must appear in input
    for entity in output_memory.entities:
        if entity.value.lower() not in input_text.lower():
            issues.append({
                'type': 'entity_not_in_input',
                'entity': entity.value,
                'severity': 'high'
            })
    
    # Check 2: Resolved dates must be justified
    if output_memory.resolved_date:
        date_markers = extract_date_markers(input_text)
        if not date_markers and output_memory.confidence > 0.5:
            issues.append({
                'type': 'unjustified_date_resolution',
                'resolved_date': output_memory.resolved_date,
                'severity': 'high'
            })
    
    # Check 3: Confidence should match uncertainty markers
    uncertainty_markers = ['maybe', 'possibly', 'might', 'could', 'think', 'believe']
    has_uncertainty = any(m in input_text.lower() for m in uncertainty_markers)
    if has_uncertainty and output_memory.confidence > 0.7:
        issues.append({
            'type': 'confidence_inflation',
            'confidence': output_memory.confidence,
            'severity': 'medium'
        })
    
    return HallucinationReport(
        has_hallucination=len(issues) > 0,
        issues=issues,
        severity=max([i['severity'] for i in issues], default='none')
    )
```

#### Procedure 2: Cross-Validation with Multiple LLMs

```python
def cross_validate_with_multiple_llms(
    input_text: str,
    primary_output: EnhancedMemory
) -> CrossValidationReport:
    """
    Run same input through multiple LLMs and compare outputs.
    """
    models = [
        'qwen-3b-coder',
        'ollama/qwen3-coder-next',
        'bailian-api/qwen-flash'
    ]
    
    outputs = []
    for model in models:
        output = extract_with_model(input_text, model)
        outputs.append(output)
    
    # Compare entity extraction
    entity_agreement = calculate_entity_agreement(outputs)
    
    # Compare date resolution
    date_agreement = calculate_date_agreement(outputs)
    
    # Flag disagreements
    disagreements = []
    if entity_agreement < 0.8:
        disagreements.append('entity_extraction_disagreement')
    if date_agreement < 0.9:
        disagreements.append('date_resolution_disagreement')
    
    return CrossValidationReport(
        models_used=models,
        entity_agreement=entity_agreement,
        date_agreement=date_agreement,
        has_disagreement=len(disagreements) > 0,
        disagreements=disagreements,
        recommendation='review' if len(disagreements) > 0 else 'accept'
    )
```

#### Procedure 3: Human-in-the-Loop Verification

```python
# For low-confidence or flagged memories

def flag_for_human_review(memory: EnhancedMemory) -> ReviewRequest:
    """
    Flag memory for human verification.
    """
    review_reasons = []
    
    if memory.quality_score < 3:
        review_reasons.append('low_quality_score')
    
    if memory.confidence < 0.5:
        review_reasons.append('low_confidence')
    
    if has_hallucination_risk(memory):
        review_reasons.append('potential_hallucination')
    
    if has_contradiction_with_history(memory):
        review_reasons.append('contradicts_history')
    
    return ReviewRequest(
        memory_id=memory.id,
        reasons=review_reasons,
        priority='high' if 'potential_hallucination' in review_reasons else 'normal',
        suggested_action='verify_or_reject'
    )
```

### 5.3 Honesty Verification Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Hallucination Detection Rate | ≥95% | Test suite |
| False Positive Rate | <10% | Human review |
| Cross-Validation Agreement | ≥85% | Multi-LLM test |
| Human Review Queue Size | <20/day | Operational metric |
| Time to Resolution | <24h | Operational metric |

---

## ✅ PART 6: SUCCESS CRITERIA DEFINITION

### 6.1 Phase 1 Success Criteria (Detailed)

```python
# tests/success_criteria/phase1_criteria.py

@dataclass
class Phase1SuccessCriteria:
    """
    Strict success criteria for Phase 1 completion.
    All criteria must be met to pass.
    """
    
    # ─────────────────────────────────────────────────────────────
    # FUNCTIONAL CRITERIA (Must have)
    # ─────────────────────────────────────────────────────────────
    
    understanding_layer_implemented: bool = False
    date_resolution_working: bool = False
    entity_resolution_working: bool = False
    quality_scoring_implemented: bool = False
    persona_categorization_working: bool = False
    
    # ─────────────────────────────────────────────────────────────
    # ACCURACY CRITERIA (Must meet thresholds)
    # ─────────────────────────────────────────────────────────────
    
    date_resolution_accuracy: float = 0.0  # Target: ≥0.90
    entity_resolution_accuracy: float = 0.0  # Target: ≥0.85
    quality_score_correlation: float = 0.0  # Target: ≥0.80
    benchmark_overall_accuracy: float = 0.0  # Target: ≥0.80
    
    # ─────────────────────────────────────────────────────────────
    # PERFORMANCE CRITERIA (Must meet thresholds)
    # ─────────────────────────────────────────────────────────────
    
    processing_latency_ms: float = float('inf')  # Target: <5000
    memory_overhead_mb: float = float('inf')  # Target: <100
    token_efficiency_improvement: float = 0.0  # Target: ≥0.15
    
    # ─────────────────────────────────────────────────────────────
    # QUALITY CRITERIA (Must pass)
    # ─────────────────────────────────────────────────────────────
    
    hallucination_detection_rate: float = 0.0  # Target: ≥0.95
    schema_validation_pass_rate: float = 0.0  # Target: 1.0
    consistency_check_pass_rate: float = 0.0  # Target: ≥0.95
    
    # ─────────────────────────────────────────────────────────────
    # DOCUMENTATION CRITERIA (Must have)
    # ─────────────────────────────────────────────────────────────
    
    api_documentation_complete: bool = False
    user_guide_complete: bool = False
    benchmark_documented: bool = False
    test_coverage: float = 0.0  # Target: ≥0.90
    
    def is_phase1_complete(self) -> Tuple[bool, List[str]]:
        """
        Check if all Phase 1 success criteria are met.
        Returns (is_complete, list_of_failed_criteria)
        """
        failed = []
        
        # Functional criteria
        if not self.understanding_layer_implemented:
            failed.append('Understanding layer not implemented')
        if not self.date_resolution_working:
            failed.append('Date resolution not working')
        if not self.entity_resolution_working:
            failed.append('Entity resolution not working')
        if not self.quality_scoring_implemented:
            failed.append('Quality scoring not implemented')
        if not self.persona_categorization_working:
            failed.append('Persona categorization not working')
        
        # Accuracy criteria
        if self.date_resolution_accuracy < 0.90:
            failed.append(f'Date resolution accuracy {self.date_resolution_accuracy:.2f} < 0.90')
        if self.entity_resolution_accuracy < 0.85:
            failed.append(f'Entity resolution accuracy {self.entity_resolution_accuracy:.2f} < 0.85')
        if self.quality_score_correlation < 0.80:
            failed.append(f'Quality score correlation {self.quality_score_correlation:.2f} < 0.80')
        if self.benchmark_overall_accuracy < 0.80:
            failed.append(f'Benchmark accuracy {self.benchmark_overall_accuracy:.2f} < 0.80')
        
        # Performance criteria
        if self.processing_latency_ms >= 5000:
            failed.append(f'Processing latency {self.processing_latency_ms:.0f}ms >= 5000ms')
        if self.token_efficiency_improvement < 0.15:
            failed.append(f'Token efficiency improvement {self.token_efficiency_improvement:.2f} < 0.15')
        
        # Quality criteria
        if self.hallucination_detection_rate < 0.95:
            failed.append(f'Hallucination detection {self.hallucination_detection_rate:.2f} < 0.95')
        if self.schema_validation_pass_rate < 1.0:
            failed.append(f'Schema validation pass rate {self.schema_validation_pass_rate:.2f} < 1.0')
        
        # Documentation criteria
        if not self.api_documentation_complete:
            failed.append('API documentation incomplete')
        if self.test_coverage < 0.90:
            failed.append(f'Test coverage {self.test_coverage:.2f} < 0.90')
        
        return (len(failed) == 0, failed)
```

### 6.2 Statistical Confidence Requirements

```python
# tests/success_criteria/statistical_requirements.py

def calculate_required_sample_size(
    expected_accuracy: float,
    margin_of_error: float,
    confidence_level: float = 0.95
) -> int:
    """
    Calculate minimum sample size for benchmark statistical significance.
    """
    from scipy.stats import norm
    
    z_score = norm.ppf((1 + confidence_level) / 2)
    p = expected_accuracy
    
    n = (z_score ** 2 * p * (1 - p)) / (margin_of_error ** 2)
    return int(math.ceil(n))

# For 20 trick questions benchmark:
# - Expected accuracy: 0.80
# - Margin of error: 0.15 (wide due to small sample)
# - Confidence level: 0.95
# → Required sample size: ~28 test runs

BENCHMARK_REQUIREMENTS = {
    'minimum_test_runs': 30,
    'confidence_level': 0.95,
    'margin_of_error': 0.15,
    'statistical_significance': 'Report confidence intervals for all accuracy metrics'
}
```

### 6.3 Final Success Criteria Summary

| Category | Criterion | Target | Status Check |
|----------|-----------|--------|--------------|
| **Functional** | Understanding Layer | Implemented | ✅/❌ |
| **Functional** | Date Resolution | Working | ✅/❌ |
| **Functional** | Entity Resolution | Working | ✅/❌ |
| **Functional** | Quality Scoring | Implemented | ✅/❌ |
| **Functional** | Persona Categorization | Working | ✅/❌ |
| **Accuracy** | Date Resolution | ≥90% | 📊 |
| **Accuracy** | Entity Resolution | ≥85% | 📊 |
| **Accuracy** | Quality Correlation | ≥0.80 | 📊 |
| **Accuracy** | Benchmark Overall | ≥80% | 📊 |
| **Performance** | Processing Latency | <5s | ⏱️ |
| **Performance** | Token Efficiency | +15% | 📊 |
| **Quality** | Hallucination Detection | ≥95% | 📊 |
| **Quality** | Schema Validation | 100% | ✅/❌ |
| **Documentation** | API Docs | Complete | ✅/❌ |
| **Documentation** | Test Coverage | ≥90% | 📊 |

**ALL criteria must pass for Phase 1 to be considered complete.**

---

## 🗳️ PART 7: HỘI NGHỊ BIỂU QUYẾT

### 7.1 Voting Agenda

**Chủ tọa:** @Auditor-General

**Nội dung biểu quyết:**

1. **Thông qua Audit Plan này**
   - Có / Không / Abstain
   
2. **Thông qua 20 Trick Questions Benchmark**
   - Có / Không / Abstain
   
3. **Thông qua Success Criteria cho Phase 1**
   - Có / Không / Abstain
   
4. **Yêu cầu bổ sung Verification Layer trước khi implement**
   - Có / Không / Abstain
   
5. **Yêu cầu Human-in-the-Loop cho memories quality < 3**
   - Có / Không / Abstain

### 7.2 Voting Rules

- **Quorum:** ≥3 members present
- **Pass threshold:** Simple majority (>50%)
- **Veto power:** @Project-Director-Linda (for critical decisions)
- **Voting period:** 24 hours from announcement

### 7.3 Voting Template

```markdown
## 🗳️ BIỂU QUYẾT HỘI NGHỊ DIÊN HỒNG

**Date:** 2026-02-26
**Chair:** @Auditor-General

### Motion 1: Thông qua Audit Plan
- [ ] ✅ Có
- [ ] ❌ Không
- [ ] ⚪ Abstain

**Lý do:** ...

---

### Motion 2: Thông qua 20 Trick Questions Benchmark
- [ ] ✅ Có
- [ ] ❌ Không  
- [ ] ⚪ Abstain

**Lý do:** ...

---

[Continue for all motions...]
```

---

## 📊 APPENDIX A: VERIFICATION CHECKLIST

### Pre-Implementation Checklist

- [ ] Audit plan reviewed by all stakeholders
- [ ] 20 trick questions finalized
- [ ] Success criteria agreed upon
- [ ] Verification layer design approved
- [ ] Hallucination detection procedures documented
- [ ] Human review workflow defined

### Post-Implementation Checklist

- [ ] All 20 trick questions pass (≥80% accuracy)
- [ ] Date resolution accuracy ≥90%
- [ ] Entity resolution accuracy ≥85%
- [ ] Quality score correlation ≥0.80
- [ ] Hallucination detection rate ≥95%
- [ ] Schema validation pass rate 100%
- [ ] Test coverage ≥90%
- [ ] Documentation complete
- [ ] Performance benchmarks met
- [ ] Human review workflow tested

---

## 📚 APPENDIX B: REFERENCES

1. Reddit Architecture: https://www.reddit.com/r/openclaw/comments/1raymjw/architecture_of_unlimited_quality_memory/
2. NeuralOpenClaw Repo: https://github.com/linda-agi/neural-openclaw
3. Statistical Significance: Cochran, W.G. (1977). Sampling Techniques
4. Hallucination Detection: Ji, Z. et al. (2023). "Survey of Hallucination in Natural Language Generation"

---

**Document Status:** ✅ Complete  
**Prepared by:** @Auditor-General  
**Review Deadline:** 2026-02-26 15:45 UTC  
**Voting Deadline:** 2026-02-27 15:45 UTC
