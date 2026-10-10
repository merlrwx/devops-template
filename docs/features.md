# Feature selection and delivery

Pin new projects to `v1.1.0`. Every `include_*` feature remains opt-in; generation with defaults creates a small API. A DevContainer is generated only with `include_devcontainer: true`. The template repository's own `.devcontainer` is independent of that switch.

## Inputs and dependencies

| Input | Default | Behaviour/dependency |
| --- | --- | --- |
| `project_type` | `python-api` | API, API + Streamlit UI, or `generic` |
| `separate_packages` | false | API/UI uv workspace under `services/api` and `services/ui`; requires API-with-UI |
| `include_coverage` | false | pytest-cov, XML/HTML/terminal reports and a failure threshold |
| `coverage_threshold` | 80 | Measured percentage, validated from 0 to 100 |
| `include_pre_commit` | false | Ruff lint/format and Commitizen commit-msg hooks |
| `include_persistence` | false | SQLite key/value starter, Compose data volume and Kubernetes PVC when selected |
| `include_containers` | false | Non-root API/UI images, pinned uv and Python, lockfile consumption |
| `include_compose` | false | Local services; requires containers |
| `include_devcontainer` | false | Mise/Python setup, forwarded application ports; Docker-in-Docker when containers are selected |
| `include_github_actions` | false | Lint, formatting, tests and selected container builds |
| `include_security_scanning` | false | Requires GitHub Actions; pip-audit, Bandit, Gitleaks and selected image scans |
| `include_release_automation` | false | Requires GitHub Actions; Release Please per-package versions/changelogs |
| `include_image_publishing` | false | Requires containers and GitHub Actions; release-tagged GHCR images |
| `image_registry_namespace` | empty | Explicit lowercase GitHub owner; required for publication |
| `include_kubernetes` | false | Requires containers; bases, probes/resources, dev/prod overlays |
| `kubernetes_namespace` | project name | Base namespace; overlays use `<namespace>-dev` / `-prod` |
| `include_flux` | false | Requires Kubernetes and `git_repository_url`; existing Flux installation |
| `git_repository_url` | empty | Explicit source URL for reconciliation |
| `include_gitops_promotion` | false | Requires image publishing and Flux; external dev updates and prod PRs |
| `gitops_repository` | empty | Explicit `owner/name` GitOps repository |
| `include_k3d` | false | Requires Kubernetes; local cluster tasks and E2E CI when Actions is selected |
| `api_port`, `ui_port` | 8000, 8501 | Selected container/service/forwarded ports |

Python-specific features are rejected for `generic`. Separate packaging is opt-in so an update does not silently move an existing project's source files. If changing layouts in an existing project, generate a comparison project and migrate imports, package names, application changes and lockfiles deliberately.

## Full Python API/UI profile

Save this outside the generated repository, replacing the example owner and repositories:

```yaml
project_name: my-app
project_type: python-api-with-ui
separate_packages: true
include_containers: true
include_compose: true
include_devcontainer: true
include_github_actions: true
include_coverage: true
coverage_threshold: 80
include_pre_commit: true
include_persistence: true
include_security_scanning: true
include_release_automation: true
include_image_publishing: true
image_registry_namespace: example
include_kubernetes: true
include_k3d: true
include_flux: true
git_repository_url: https://github.com/example/my-app-gitops.git
include_gitops_promotion: true
gitops_repository: example/my-app-gitops
```

Generate with `copier copy --vcs-ref v1.1.0 --defaults --data-file /tmp/answers.yml gh:merlrwx/devops-template my-app`. Inspect the output, initialize Git, run `mise install --locked`, then `mise run setup`, `mise run lint`, `mise run format-check`, and `mise run test`. Commit the generated `uv.lock`; neither generation nor the template's generic starter runs dependency resolution or installs hooks. CI resolves a lock only when missing so initial scaffolds work; commit it for repeatable dependencies. The DevContainer setup installs dependencies but hooks are installed explicitly via `mise run setup` after Git initialization.

Coverage measures application packages and UI helper functions. It omits the Streamlit `ui.py` entry script and API launcher; Kubernetes E2E checks service health and API persistence, not browser interactions. Add application-specific tests as the project grows. Frontend/backend packages have separate dependency declarations and release versions, with one shared uv workspace lock.

## Security policy

Security CI fails on dependency audit findings, medium/high-severity Bandit results, leaked secrets and HIGH/CRITICAL image vulnerabilities, including unfixed findings. It reads the checked-out history for secrets with redacted output. Review actual findings, update dependencies or document narrow suppressions; do not switch the workflow to report-only mode. Scanning requires upstream vulnerability databases and registry access. Pip-audit uses an exported production dependency set; it excludes workspace packages themselves. Development dependencies are outside that default audit scope.

Source and dependency scanning are separate from GitHub-managed code/secret scanning settings. The template creates repository workflows and does not configure account-level security services.

## Release, publication and promotion configuration

Configure secrets in the adopting repository; no secret values are generated:

- `RELEASE_TOKEN`: a repository-scoped GitHub App installation token or PAT with contents, issues and pull-request write access. Release Please uses it to create release PRs/tags. An ordinary `GITHUB_TOKEN` can suppress subsequent tag-triggered workflows, so supply a suitable dedicated credential.
- `GITHUB_TOKEN`: automatically supplied by GitHub; the publishing job requests packages write permission. `image_registry_namespace` must match the repository owner's lowercase name. Publishing only runs for version tags or an explicitly dispatched existing tag. Single-package tags are `vX.Y.Z`; workspace component tags are `api-vX.Y.Z` and `ui-vX.Y.Z`.
- `GITOPS_TOKEN`: a credential scoped to the named GitOps repository with contents and pull-request write permission. Promotion commits development image changes to that repository's `main` and opens a production PR. Branch protection and the adopting project's review model must permit those operations.

Review and copy the generated **contents of `gitops/`** into the explicitly named GitOps repository. The bundle provides `apps/base`, `apps/dev`, and `apps/prod`. The application source, publishing owner and GitOps image names must agree. Configure the Flux source URL to point at that same GitOps repository when promotion is enabled. Install Flux and add the generated reconciliation objects through your existing cluster root; generation does not bootstrap controllers or configure credentials. The generated reconciliation selects development; production needs a separately reviewed root. `prune` stays disabled by default.

Promotion only changes the selected component for component tags, or both components for a shared tag. Concurrent promotions are serialized. Production PRs use a reusable branch and show the current desired release; merging them is an explicit production approval.

## Kubernetes development and durability

Install Docker, kubectl and k3d 5.9.0. `mise run k8s-setup-local` creates the project's local cluster when absent, builds/imports selected images and applies the development overlay. `k8s-sync-local` rebuilds and restarts workloads. Both use an explicit context and refuse local sync when `flux-system` exists. `k8s-status` and `k8s-logs` inspect the project namespace. Run `python scripts/cluster.py down --yes` to acknowledge deletion of the cluster and all its data.

`mise run e2e-test` creates a uniquely named disposable cluster, checks API/UI health, verifies SQLite data survives an API rollout when persistence is selected, and deletes that cluster in a `finally` block. E2E CI runs the same script. It does not touch an existing development cluster.

Persistence supplies a single-replica API with a Recreate strategy and 1Gi ReadWriteOnce PVC using the cluster's default StorageClass. SQLite is a starter for small single-instance applications. It is not a high-availability database design. Persistent volumes survive Pod restarts; deleting a local cluster deletes its storage. Production requires a reviewed StorageClass, retention/backup strategy and capacity policy.

## Updating existing generated projects

Version 1.0.0 wrote incomplete `.copier-answers.yml` metadata. Recover that version's source, revision and original selected options from your generation command/history before an update; do not assume omitted options were false. Generate into a temporary directory and selectively adopt changes when the metadata cannot be recovered reliably. Version 1.1.0 preserves all selections and the template revision.

For projects with complete answers, commit current work, create an update branch, run `copier update --vcs-ref v1.1.0 --defaults`, inspect conflicts and run the selected validation. Keep user-owned code and credentials. Changing package layout is a migration, not an automatic update default.
