### Task 4: Add mock_llm fixture to conftest.py

**Files:**
- Modify: `tests/conftest.py`

**Interfaces:**
- Consumes: existing `create_sales_agent` from `src.agents.graph`
- Produces: `mock_llm` fixture for agent tests

- [ ] **Step 1: Update conftest.py with mock_llm fixture**

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.agents.graph import create_sales_agent


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session_id(client):
    response = client.post("/session", json={"customer_name": "Test Customer"})
    return response.json()["session_id"]


@pytest.fixture
def mock_llm():
    """Fixture to mock LLM with scripted responses."""
    def _make_agent(responses):
        """
        Create agent with mocked LLM.
        
        Args:
            responses: List of AIMessage objects the mock LLM will return in sequence.
        """
        with patch("src.agents.nodes.create_llm") as mock_create:
            mock_instance = MagicMock()
            mock_instance.invoke.side_effect = responses
            mock_create.return_value = mock_instance
            agent = create_sales_agent()
            yield agent
    return _make_agent
```

- [ ] **Step 2: Verify fixture loads**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/conftest.py -v`

Expected: No import errors

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add mock_llm fixture for agent tests"
```
