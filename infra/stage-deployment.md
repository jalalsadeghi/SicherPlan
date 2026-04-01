# SicherPlan Stage Deployment

This staging setup deploys only the FastAPI backend, the `web-antd` frontend, and PostgreSQL on a single Docker Compose host. The web container is the only public entrypoint. It serves the SPA and reverse-proxies `/api/` to the internal backend container.

## Server Directories

Create these directories on the staging droplet:

```bash
sudo mkdir -p /opt/sicherplan-stage/config
sudo mkdir -p /opt/sicherplan-stage/deploy
sudo chown -R "$USER":"$USER" /opt/sicherplan-stage
```

Use them like this:

- `/opt/sicherplan-stage/deploy`
  - checked-in deployment artifacts copied from this repo
  - `docker-compose.stage.yml`
  - `deploy_stage_remote.sh`
- `/opt/sicherplan-stage/config`
  - server-only env files with real secrets
  - never commit these files

## Files That Stay On The Server

These files must exist on the server and must not be committed with real values:

- `/opt/sicherplan-stage/config/stage.env`
- `/opt/sicherplan-stage/config/backend.stage.env`

Create them from:

- [stage.env.example](/home/jey/Projects/SicherPlan/infra/env/stage.env.example)
- [backend.stage.env.example](/home/jey/Projects/SicherPlan/infra/env/backend.stage.env.example)

The server-side files should contain real image tags, database credentials, and application secrets.

For automated GitHub Actions deploys, keep the stage image references pinned to the rolling `main` tags:

```env
BACKEND_IMAGE=ghcr.io/your-org/sicherplan-backend:main
WEB_IMAGE=ghcr.io/your-org/sicherplan-web:main
```

## First-Time Deploy

1. Copy the deployment artifacts to the server:

```bash
scp /home/jey/Projects/SicherPlan/infra/docker-compose.stage.yml your-user@your-server:/opt/sicherplan-stage/deploy/
scp /home/jey/Projects/SicherPlan/infra/scripts/deploy_stage_remote.sh your-user@your-server:/opt/sicherplan-stage/deploy/
scp /home/jey/Projects/SicherPlan/infra/env/stage.env.example your-user@your-server:/opt/sicherplan-stage/deploy/stage.env.example
scp /home/jey/Projects/SicherPlan/infra/env/backend.stage.env.example your-user@your-server:/opt/sicherplan-stage/deploy/backend.stage.env.example
```

2. On the server, create the real env files:

```bash
cp /opt/sicherplan-stage/deploy/stage.env.example /opt/sicherplan-stage/config/stage.env
cp /opt/sicherplan-stage/deploy/backend.stage.env.example /opt/sicherplan-stage/config/backend.stage.env
```

3. Export the required deployment variables and run the deploy script:

```bash
export DEPLOY_ROOT=/opt/sicherplan-stage
export STAGE_ENV_FILE=/opt/sicherplan-stage/config/stage.env
export BACKEND_ENV_FILE=/opt/sicherplan-stage/config/backend.stage.env
export GHCR_USERNAME=your-ghcr-username
export GHCR_TOKEN=your-ghcr-token

bash /opt/sicherplan-stage/deploy/deploy_stage_remote.sh
```

The script will:

- log in to `ghcr.io`
- pull the backend and web images
- start PostgreSQL first
- run `alembic upgrade head`
- bring the full stack up
- prune dangling images

## GitHub Actions Automated Deploy

The workflow file is [stage-deploy.yml](/home/jey/Projects/SicherPlan/.github/workflows/stage-deploy.yml). It builds the backend and web stage images on every push to `main` and on `workflow_dispatch`, pushes them to GHCR, copies the latest compose/script files to the server, and then runs the remote deploy script over SSH.

For preexisting tenants that were created before HR baseline onboarding was introduced, code deploy alone is not enough. The workflow now supports an explicit optional post-deploy HR catalog backfill on `workflow_dispatch` only:

- `run_hr_baseline_backfill=true`
- then either:
  - `hr_baseline_tenant_id=<tenant_uuid>`
  - or `hr_baseline_all_tenants=true` plus `hr_baseline_confirmation=RUN_ALL_TENANTS`

This backfill is not enabled on normal `push` deploys.

### Required GitHub Secrets

- `STAGE_HOST`
- `STAGE_PORT`
- `STAGE_USER`
- `STAGE_SSH_KEY`
- `STAGE_KNOWN_HOSTS`
- `GHCR_USERNAME`
- `GHCR_TOKEN`

### Server-Side Files Required Before The First Automated Deploy

These files must already exist on the server before the workflow can succeed:

- `/opt/sicherplan-stage/config/stage.env`
- `/opt/sicherplan-stage/config/backend.stage.env`

These directories must also already exist:

- `/opt/sicherplan-stage/config`
- `/opt/sicherplan-stage/deploy`

The workflow does not copy secret env files from GitHub to the server. It only updates:

- `/opt/sicherplan-stage/deploy/docker-compose.stage.yml`
- `/opt/sicherplan-stage/deploy/deploy_stage_remote.sh`

## Building And Publishing Images

Build from the repo root so both stage Dockerfiles can see the correct monorepo files:

```bash
docker build -f /home/jey/Projects/SicherPlan/backend/Dockerfile.stage -t ghcr.io/your-org/sicherplan-backend:main /home/jey/Projects/SicherPlan
docker build -f /home/jey/Projects/SicherPlan/web/Dockerfile.stage -t ghcr.io/your-org/sicherplan-web:main /home/jey/Projects/SicherPlan
docker push ghcr.io/your-org/sicherplan-backend:main
docker push ghcr.io/your-org/sicherplan-web:main
```

Update `/opt/sicherplan-stage/config/stage.env` whenever you roll to a new image tag.

## Bootstrap Commands

After the first successful deploy and migration run, bootstrap the initial stage data with one-off backend containers:

```bash
export BACKEND_ENV_FILE=/opt/sicherplan-stage/config/backend.stage.env
set -a
. /opt/sicherplan-stage/config/stage.env
set +a

docker-compose -f /opt/sicherplan-stage/deploy/docker-compose.stage.yml \
  run --rm backend python scripts/bootstrap_system_admin.py

docker-compose -f /opt/sicherplan-stage/deploy/docker-compose.stage.yml \
  run --rm backend python scripts/seed_go_live_configuration.py
```

Both commands use the backend env file already referenced by `docker-compose.stage.yml`, so they will run against the stage database and stage filesystem object-storage volume.

### Explicit HR baseline backfill after deploy

Single tenant:

```bash
docker-compose -f /opt/sicherplan-stage/deploy/docker-compose.stage.yml \
  run --rm backend python scripts/seed_go_live_configuration.py --tenant-id <tenant_uuid>
```

All active tenants, explicit confirmation required:

```bash
docker-compose -f /opt/sicherplan-stage/deploy/docker-compose.stage.yml \
  run --rm backend python scripts/seed_go_live_configuration.py --all-tenants --confirm-all-tenants RUN_ALL_TENANTS
```

## Notes

- PostgreSQL is internal only in this setup. Do not publish it on the host.
- The backend object storage remains filesystem-based and is persisted in the named Docker volume mounted at `/var/lib/sicherplan/object-storage`.
- If you put Nginx, Caddy, or a load balancer in front of this host later, keep `/api/` routed to the same web container so the reverse-proxy contract stays unchanged.
