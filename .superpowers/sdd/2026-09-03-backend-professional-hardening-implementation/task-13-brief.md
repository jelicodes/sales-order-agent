### Task 13: Run all tests and verify

**Files:**
- None (verification only)

- [ ] **Step 1: Run all tests (excluding integration)**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/ -v --ignore=tests/test_integration.py`

Expected: All tests pass

- [ ] **Step 2: Run integration tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_integration.py -v`

Expected: All tests pass in < 5 seconds

- [ ] **Step 3: Run syntax check on all modified files**

```powershell
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/data/database.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/api/chat.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/api/session.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/api/health.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/agents/nodes.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/config/settings.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/main.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/tools/calculate_price.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/data/seed/seed.py
```

- [ ] **Step 4: Final commit with all changes (if any)**

```bash
git add -A
git commit -m "feat: complete backend professional hardening (performance, tests, caching, security)"
```

- [ ] **Step 5: Push to GitHub**

```bash
git push origin main
```
