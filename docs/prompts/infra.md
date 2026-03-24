Please adjust the GitHub Actions triggers in the SicherPlan repository to avoid duplicate workflow runs on every push to main.

Current situation:
- There are two workflows running on every push to main:
  1) CI
  2) Stage Deploy
- We want:
  - CI to run on pull_request to main and workflow_dispatch
  - Stage Deploy to run on push to main and workflow_dispatch

Tasks:
1) Find the workflow file that defines the CI workflow.
2) Change its trigger from push-to-main to:
   - pull_request on main
   - workflow_dispatch
3) Keep the Stage Deploy workflow triggered by:
   - push on main
   - workflow_dispatch
4) Do not change the jobs themselves, only the workflow triggers.
5) Summarize which workflow files were changed and the new trigger behavior.