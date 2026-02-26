# OpenClaw-Native LLM Routing

**Version:** 1.0  
**Date:** 2026-02-26  
**Status:** Approved (Hội Nghị Diên Hồng Motion #3)

---

## Overview

Fetch LLM models from OpenClaw gateway configuration instead of duplicate config. Auto-select optimal model based on resources and cost.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         OpenClaw-Native LLM Router                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Understanding Request]                                    │
│         │                                                   │
│         ▼                                                   │
│  [Fetch OpenClaw Providers] ← gateway config              │
│         │                                                   │
│         ├─→ Categorize (local vs cloud)                    │
│         ├─→ Check RAM availability                         │
│         └─→ Select optimal model                           │
│                                                             │
│         ▼                                                   │
│  [Call LLM via OpenClaw sessions_spawn]                    │
│                                                             │
│         ▼                                                   │
│  [Parse & Validate Output]                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation

### Step 1: Fetch OpenClaw Providers

```python
import requests
import json
from pathlib import Path

class OpenClawModelRouter:
    def __init__(self, gateway_url: str = "http://localhost:18789"):
        self.gateway_url = gateway_url
        self.gateway_token = self.load_gateway_token()
    
    def load_gateway_token(self) -> str:
        """Load token from openclaw.json"""
        config_path = Path.home() / ".openclaw" / "openclaw.json"
        config = json.loads(config_path.read_text())
        return config["gateway"]["auth"]["token"]
    
    def fetch_available_models(self) -> dict:
        """Fetch models from OpenClaw gateway"""
        response = requests.get(
            f"{self.gateway_url}/api/models",
            headers={"Authorization": f"Bearer {self.gateway_token}"}
        )
        
        providers = response.json()
        
        # Categorize by resource requirement
        categorized = {
            "local": [],      # lms-local, ollama
            "cloud": [],      # bailian-api, bailian-coder
        }
        
        for provider_id, provider_data in providers.items():
            for model in provider_data["models"]:
                model_info = {
                    "provider": provider_id,
                    "model": model["id"],
                    "context_length": model.get("contextWindow", 4096),
                    "is_local": self.is_local_provider(provider_id)
                }
                
                if model_info["is_local"]:
                    categorized["local"].append(model_info)
                else:
                    categorized["cloud"].append(model_info)
        
        return categorized
    
    def is_local_provider(self, provider_id: str) -> bool:
        """Check if provider is local (runs on machine)"""
        local_providers = ["ollama", "lms-local", "qwen-local"]
        return any(local in provider_id.lower() for local in local_providers)
```

---

### Step 2: Auto-Select Model

```python
def select_understanding_model(self) -> dict:
    """Select optimal model for understanding task"""
    models = self.fetch_available_models()
    
    # Priority 1: Local models (free, fast)
    if models["local"]:
        # Check RAM
        ram = self.get_available_ram()
        
        if ram > 6 * 1024**3:  # 6GB
            # Prefer larger local models
            return models["local"][0]  # e.g., qwen3-4b-instruct
        else:
            # Smaller local models
            return models["local"][-1]  # e.g., qwen3-coder-next
    
    # Priority 2: Cloud models (paid, reliable)
    if models["cloud"]:
        # Prefer cheap models for understanding task
        cheap_models = [
            m for m in models["cloud"]
            if "flash" in m["model"].lower() or "coder" in m["model"].lower()
        ]
        
        if cheap_models:
            return cheap_models[0]  # e.g., qwen-flash
    
    # Fallback: Any available model
    all_models = models["local"] + models["cloud"]
    return all_models[0] if all_models else None

def get_available_ram(self) -> int:
    """Get available RAM in bytes"""
    import psutil
    return psutil.virtual_memory().available
```

---

### Step 3: Call LLM via OpenClaw

```python
async def call_understanding_llm(self, messages: list, prompt: str) -> dict:
    """Call LLM via OpenClaw sessions_spawn"""
    model = self.select_understanding_model()
    
    # Use OpenClaw sessions_spawn
    result = await sessions_spawn(
        agentId="main",
        task=f"""
        Analyze these messages and extract structured memory:
        
        Messages: {messages}
        
        Output JSON matching EnhancedMemory schema.
        """,
        model=f"{model['provider']}/{model['model']}",
        timeoutSeconds=30
    )
    
    return json.loads(result)
```

---

## Configuration (Optional Overrides)

```json
{
  "understanding": {
    "llm_routing": {
      "strategy": "openclaw-native",
      "auto_detect": true,
      
      "preferences": {
        "prefer_local": true,
        "prefer_cheaper": true,
        "max_cost_per_batch": "$0.01"
      },
      
      "fallback": {
        "enabled": true,
        "timeout_seconds": 30,
        "max_retries": 3
      }
    }
  }
}
```

---

## CLI Commands

```bash
# Show available models from OpenClaw
nocl.py models list

# Show recommended model for understanding
nocl.py models recommend --task understanding

# Test model selection
nocl.py models test --task understanding

# Override auto-selection
nocl.py config set understanding.model ollama/qwen3-coder-next
```

---

## Example: Bro's Current Setup

### OpenClaw Providers (from openclaw.json)

```json
{
  "models": {
    "providers": {
      "ollama": {
        "models": ["qwen3-coder-next"]
      },
      "lms-local": {
        "models": ["qwen3-4b-instruct-2507"]
      },
      "bailian-api": {
        "models": ["qwen3-coder-plus"]
      },
      "bailian-coder": {
        "models": [
          "qwen3.5-plus",
          "qwen3-coder-next",
          "qwen3-coder-plus"
        ]
      }
    }
  }
}
```

### Auto-Selection Logic

```
RAM > 6GB:
  → lms-local/qwen3-4b-instruct-2507 (local, 4GB RAM)

RAM 4-6GB:
  → ollama/qwen3-coder-next (local, smaller)

RAM < 4GB:
  → bailian-coder/qwen3-coder-next (cloud fallback)
```

---

## Benefits

| Benefit | Description |
|---------|-------------|
| ✅ No duplicate config | API keys already in openclaw.json |
| ✅ Auto-discovery | Detect providers automatically |
| ✅ Consistent auth | Use same auth as OpenClaw |
| ✅ Centralized management | Manage 1 place (openclaw.json) |
| ✅ No extra setup | User doesn't need to install anything |
| ✅ Leverage existing | 100% existing infrastructure |

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-26  
**Approved:** Hội Nghị Diên Hồng Motion #3
