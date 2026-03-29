You are working in the SicherPlan backend.

Task:
Fix the backend startup failure caused by a Python function-signature syntax error in:

`backend/app/modules/customers/router.py`

Observed error:
When starting uvicorn, import fails with:

`SyntaxError: parameter without a default follows parameter with a default`

Location:
- `backend/app/modules/customers/router.py`
- around line 520
- introduced by the recent customer address-linking changes

Goal:
Make the router module importable again without changing the intended endpoint behavior.

Important:
- This is a Python syntax/signature-ordering bug.
- Do not change the feature scope unless necessary.
- Do not remove the new address-options/address-linking functionality.
- Keep FastAPI dependency injection behavior intact.
- Keep the endpoint contract intact unless a tiny signature cleanup is required.

Required work:
1. Inspect the exact function at/around line 520 in `backend/app/modules/customers/router.py`.
2. Identify which route function has parameters ordered incorrectly.
3. Reorder the parameters so all non-default parameters come before any parameters with defaults.
4. Follow the existing style already used elsewhere in the same router file for FastAPI routes with:
   - path params
   - query params
   - payload
   - context dependencies
   - service dependencies
5. Ensure the file is syntactically valid and imports cleanly.

Likely issue shape:
A parameter using `Query(default=...)` or another defaulted argument was placed before a dependency/payload/context parameter without a default.

Acceptance criteria:
- `uvicorn app.main:app ...` starts successfully
- `backend/app/modules/customers/router.py` imports cleanly
- no syntax error remains
- the newly added address-linking/address-options endpoints still exist and behave as intended

Verification:
After fixing, run at minimum:
- `python -m py_compile backend/app/modules/customers/router.py`
- start the backend import path again
- if possible, run the affected customer backend tests again

Output:
Provide a concise summary of:
- which route signature was broken
- how you reordered the parameters
- confirmation that backend startup works again