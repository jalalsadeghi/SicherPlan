Please make the minimum safe changes required to fix the current stage deployment pipeline failures in the SicherPlan repository.

Current errors:
1) GHCR push fails with:
   denied: permission_denied: The token provided does not match expected scopes.
2) Web image build fails with:
   failed to calculate checksum ... "/web/apps/web-antd/dist": not found

Important context:
- Build jobs should push images to GHCR from GitHub Actions.
- Remote stage deployment on the server should still use GHCR_USERNAME and GHCR_TOKEN for docker login and image pull.
- The current workflow incorrectly uses GHCR_TOKEN for image push in the build jobs.
- The repository snapshot used for stage currently expects a checked-in frontend dist at web/apps/web-antd/dist.
- We want the smallest reliable fix that gets the pipeline green.
- Do not redesign the whole frontend build system yet.
- Do not touch mobile.
- Do not change business logic.

Tasks:

1) Fix the GitHub Actions workflow that builds and deploys stage
- In the backend and web build jobs, use GITHUB_TOKEN for logging into ghcr.io
- Use:
  username: ${{ github.actor }}
  password: ${{ secrets.GITHUB_TOKEN }}
- Keep permissions:
  contents: read
  packages: write
- Do NOT use GHCR_TOKEN for build/push jobs
- Keep GHCR_USERNAME and GHCR_TOKEN only for the remote deploy step on the server, where docker login is needed for pulling images

2) Make the web image build fail earlier and more clearly if dist is missing from the checked-out repo
- Keep the current stage strategy of serving checked-in web/apps/web-antd/dist directly
- Update web/Dockerfile.stage so the failure message is explicit and easy to understand
- If useful, add a pre-copy check in the workflow before docker build:
  verify that web/apps/web-antd/dist/index.html exists
  if missing, fail with a clear message saying that the current stage strategy requires committed dist assets in the repository

3) Do not reintroduce pnpm install or a full workspace build in the stage image path

4) At the end, summarize:
- which workflow file you changed
- why GHCR push was failing
- why the web dist path was failing
- what the current operational expectation is for stage frontend builds