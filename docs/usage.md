# Use this template

## Prerequisites

Install Git and Copier 9.18.2. To pin Copier itself when using uv, run it
through `uvx --from copier==9.18.2 copier ...` (or install that exact Copier
version in your environment). Generated Python projects use Mise to select
Python and uv; install Mise to run their development tasks. Docker is needed
only if you select container files or Compose.

## Generate a project

Use the released template version `v1.0.0`, or another reviewed release.
Keep the project answers in a temporary file outside the destination:

```sh
uvx --from copier==9.18.2 copier copy \
  --vcs-ref v1.0.0 \
  --data-file /tmp/answers.yml \
  gh:merlrwx/devops-template my-project
```

Review the selected revision and `answers.yml` before generating. Avoid an
unqualified `HEAD` or a moving branch when reproducibility matters. Copier
records the source revision and answers in `.copier-answers.yml` in the
generated project.

Example `answers.yml`:

```yaml
project_name: inventory-service
project_type: python-api
include_containers: true
include_compose: true
include_devcontainer: true
include_github_actions: true
api_port: 8000
ui_port: 8501
```

`project_name` must start with a lowercase letter and contain lowercase
letters, digits, and single hyphens. `project_type` is `python-api`,
`python-api-with-ui`, or `generic`. Container files and DevContainers are available only to the
two Python project types. Compose requires containers. A DevContainer uses the
project-pinned Mise toolchain for an isolated editor environment. Ports are asked only
when containers are selected; `ui_port` applies to the API-with-UI type.

## Choose features and understand limits

The project type controls application files: `python-api` generates a FastAPI
API, `python-api-with-ui` adds a Streamlit UI, and `generic` omits the Python
application and Python tests. Container packaging is optional for either
Python type. Compose is an optional local configuration and depends on
container packaging. Pick only the capabilities your project needs.

Generation creates repository files only. It does not provision infrastructure,
create cloud or Git hosting resources, deploy the project, or configure
production secrets.

GitHub Actions CI is available as an optional feature for Python project types.
Kustomize manifests are optional for Python projects and require containers. An
optional Flux bundle requires Kubernetes plus an explicit Git repository URL; it
assumes an existing Flux controller and reconciliation root. Neither module
creates clusters, installs controllers, or applies resources. K3d setup, release
automation, security scanning, production promotion, and infrastructure
provisioning are not generated. See the [component catalog](component-catalog.md)
for source patterns and boundaries.

## Validate the generated project

For Python project types, enter the generated directory and run:

```sh
mise install --locked
mise run lint
mise run test
```

For `generic`, there are no language-specific test or lint tasks in the current
template. Review the generated files and use the checks appropriate to the
project's language. If containers are included, Docker is required to build or
run them; Compose is available only when selected. For Kubernetes manifests,
check the rendered resources with `kubectl kustomize kubernetes/base`. Make sure
images are available to your chosen cluster before applying them. Flux resources
are only configuration input for an existing Flux reconciliation root.

## Update an existing project

Update from a clean working tree on a dedicated branch so the template changes
are easy to inspect and revert:

```sh
cd my-project
git status --short
git switch -c template-update
copier update
```

If the tree is not clean, commit or otherwise preserve the work before starting
the update. Review the resulting diff, resolve any conflicts, rerun the
project's validation commands, then commit the reviewed update. Copier uses the
recorded answers and prior template revision to calculate the update.
