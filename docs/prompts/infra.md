Now add GitHub Actions based automatic staging deployment for the SicherPlan repository.

Requirements:
- Deployment target is a single Linux server reachable via SSH.
- On every push to main, build and push stage images to GHCR, then deploy to the server.
- Also support workflow_dispatch.
- The server should not need a git clone of the full repository for deployment.
- The workflow should copy the current docker-compose.stage.yml and remote deploy script to the server on each deployment.
- Use GitHub secrets for all sensitive data.
- Do not use password-based SSH login. Assume SSH private key secret is provided.
- Keep backend and web as separate images.

Implement:

1) .github/workflows/stage-deploy.yml
- Trigger on:
  - push to main
  - workflow_dispatch
- Job build_backend:
  - checkout
  - login to ghcr.io
  - build and push backend/Dockerfile.stage
  - push tags:
    - ghcr.io/<owner-or-org>/sicherplan-backend:main
    - ghcr.io/<owner-or-org>/sicherplan-backend:${{ github.sha }}
- Job build_web:
  - checkout
  - login to ghcr.io
  - build and push web/Dockerfile.stage
  - push tags:
    - ghcr.io/<owner-or-org>/sicherplan-web:main
    - ghcr.io/<owner-or-org>/sicherplan-web:${{ github.sha }}
- Job deploy_stage:
  - needs build_backend and build_web
  - checkout
  - create /tmp deployment bundle if useful
  - copy these files to the server:
    - infra/docker-compose.stage.yml -> /opt/sicherplan-stage/deploy/docker-compose.stage.yml
    - infra/scripts/deploy_stage_remote.sh -> /opt/sicherplan-stage/deploy/deploy_stage_remote.sh
  - ssh into server and run deploy_stage_remote.sh

2) The workflow must use these secret names:
- STAGE_HOST
- STAGE_PORT
- STAGE_USER
- STAGE_SSH_KEY
- STAGE_KNOWN_HOSTS
- GHCR_USERNAME
- GHCR_TOKEN

3) Pass these environment values to the remote script:
- DEPLOY_ROOT=/opt/sicherplan-stage
- STAGE_ENV_FILE=/opt/sicherplan-stage/config/stage.env
- BACKEND_ENV_FILE=/opt/sicherplan-stage/config/backend.stage.env
- GHCR_USERNAME from secrets
- GHCR_TOKEN from secrets

4) Add clear comments in the workflow so it is easy to maintain.

5) Add a short section to infra/stage-deployment.md listing the GitHub secrets and the exact server-side files expected before the first automated deployment.

Rules:
- Do not add any production workflow.
- Do not deploy mobile.
- Do not add registry credentials into committed files.
- Do not require the server to have the repo checked out.
- Keep the workflow simple and deterministic.
- At the end, summarize the workflow logic and the expected first-run sequence.