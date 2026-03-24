Please inspect the current SicherPlan repository carefully and fix the two failing GitHub Actions stage image builds with the smallest safe changes necessary.

Current failures:
1) backend image build fails on:
   pip install --no-cache-dir . uvicorn
   because setuptools discovers multiple top-level packages in backend: app and alembic

2) web image build fails on:
   pnpm install --frozen-lockfile
   because the current repo snapshot does not contain web/pnpm-lock.yaml

Important repository facts you must respect:
- The backend lives in /backend and runs from app.main:app
- Alembic exists in /backend/alembic but it must NOT be treated as an installable package
- The backend runtime should still support Alembic migrations from the container
- The deployed frontend for stage is /web/apps/web-antd
- In the current repository snapshot, /web/apps/web-antd/dist already exists and contains a built frontend
- We want the fastest reliable path to get stage deployment green
- Do not redesign the monorepo
- Do not add Kubernetes
- Do not touch mobile
- Do not change business logic
- Keep the result compatible with the existing GitHub Actions stage-deploy workflow

Please implement the following:

1) Fix backend packaging so `pip install .` succeeds
- Update backend/pyproject.toml
- Add an explicit [build-system]
- Configure setuptools package discovery so only the Python package under backend/app is installable
- Exclude alembic, tests, scripts, and any other non-runtime folders from package discovery
- Keep dependencies intact
- Make the backend buildable in Docker with pip install .

2) Fix backend/Dockerfile.stage if needed
- Keep it minimal and stable
- Use Python 3.12 slim
- Install the backend package and uvicorn
- Ensure the final container can run:
  uvicorn app.main:app --host 0.0.0.0 --port 8000
- Ensure Alembic files remain available in the image for migration commands

3) Fix the web stage image build in the most reliable way for the current repository snapshot
- Since pnpm-lock.yaml is currently absent, do NOT rely on `pnpm install --frozen-lockfile`
- Since web/apps/web-antd/dist already exists in the repo, change the stage web image to serve the committed dist directly with nginx
- The web stage image should:
  - copy web/apps/web-antd/dist into nginx html root
  - use the existing stage nginx config
  - not run pnpm install
  - not run a frontend build step
- Add a clear comment in the Dockerfile explaining that this temporary stage strategy intentionally serves the checked-in dist because the current repo snapshot lacks a lockfile for deterministic workspace builds

4) Add a lightweight safety check
- In the web Dockerfile, fail clearly if web/apps/web-antd/dist/index.html is missing
- The error message should explain that either dist must be committed or the stage build strategy must be changed later to a full workspace build once a lockfile is committed

5) Do not modify the GitHub Actions workflow unless absolutely necessary
- The goal is that the existing workflow works after these repo fixes

6) At the end, summarize:
- exactly which files you changed
- why backend packaging was failing
- why the web frozen-lockfile build was failing
- why serving checked-in dist is the safest current stage approach

Make only the minimum necessary changes to get both stage image builds green.