# Implementation plan: Copier + agent-driven project scaffolding

Goal: Turn your existing [`devops-app`](https://github.com/merlrwx/devops-app) into a reusable DevOps foundation that Codex or Pi can intelligently apply to new projects.

I recommend one Copier template repository, one shared agent skill, and a small change to your dotfiles. No new MCP server, orchestration service, or special Herdr integration is necessary.

The important distinction is that Copier generates the files, while the AI agent decides which files and configurations the project actually needs.

## 1. Target architecture

Herdr → Codex / Pi

You describe the project and its requirements

project-scaffold skill

New

Agent examines the repository, chooses appropriate components, determines configuration values

Copier template

New

Reusable foundation extracted from devops-app

Mise + uv

DevContainer

Docker / Compose

GitHub Actions

Kubernetes

Flux integration

Release Please

Security tooling

Generated application repository

Only the required components, followed by agent configuration and validation

Your existing repositories would have these responsibilities:

| Repository                   | Responsibility                                                              |
| ---------------------------- | --------------------------------------------------------------------------- |
| `merlrwx/devops-app`         | Working reference implementation; keep it intact                            |
| `merlrwx/devops-template`    | New Copier template and its tests                                           |
| `merlrwx/dotfiles`           | Install Copier through your existing mise setup; distribute the agent skill |
| New application repositories | Generated, project-specific configuration                                   |

This matches your current architecture: Chezmoi manages dotfiles, mise provides shared tools, Herdr manages agent sessions, and DevPod is optional when a project needs an isolated development environment.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

merlrwx/dotfiles · GitHub



## 2. What should Codex be allowed to decide?

I'd use a small set of explicitly supported features rather than asking Copier itself to understand project requirements.

| Component                       | Agent selection rule                                        |
| ------------------------------- | ----------------------------------------------------------- |
| Mise                            | Always include                                              |
| Testing, linting and pre-commit | Always include appropriate tooling                          |
| Python + uv                     | Python projects only                                        |
| DevContainer                    | When reproducible isolated development is useful            |
| Docker                          | Applications that need container packaging                  |
| Compose                         | Local multi-service development                             |
| Kubernetes + Kustomize          | When Kubernetes deployment is required                      |
| GitHub Actions                  | When using GitHub; tailor to the actual project             |
| Release Please                  | When automated versioning/releases are valuable             |
| Flux integration                | Only for GitOps-managed Kubernetes deployments              |
| Terraform                       | Later extension, when infrastructure provisioning is needed |

The agent should make these selections based on actual requirements, not install everything because it is available.

For example, an Astro website deployed to Cloudflare Pages shouldn't inherit k3d, Flux, Python or container image publishing simply because they're present in `devops-app`.

## 3. Implementation phases

9 PHASES · IN IMPLEMENTATION ORDER

### Phase 0 — Confirm scope and prove the first path

Repository: `merlrwx/devops-template`

Decisions confirmed before implementation:

- The first release targets **new repositories**. Codex/Pi will inspect a project request and choose among supported Copier features.
- The initial project types are `python-api`, `python-api-with-ui` (FastAPI + Streamlit as the reference), and `generic`.
- The first reliable path includes local development, tests, CI and containers. Kubernetes and Flux are optional follow-on modules.
- The first milestone includes the shared `project-scaffold` skill and its dotfiles distribution, so the agent workflow is usable with the template.
- Adapting existing repositories is a later phase, after new-repository generation is reliable.

Tasks:

- Audit the working `devops-app`, its separate `devops-app-gitops` repository, and current dotfiles conventions before extracting files.
- Define a minimal valid generated repository and a small representative set of configurations before expanding modules.
- Keep generation deterministic and free of infrastructure provisioning or external side effects.

Acceptance: A default project and each initial project type can be generated and validated; containers and CI work for the relevant types; unsupported deployment modules are absent unless selected.

### Phase 1 — Audit and extract reusable components

Repository: `merlrwx/devops-app`

Your `devops-app` is a working application, not yet a generic template. It contains project-specific variables and automation, including `APP_REPO`, `GITOPS_REPO`, `GITUSER`, hardcoded k3d contexts and deployment scripts.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://raw.githubusercontent.com\&sz=32)

GitHub



Tasks:

- Inventory all reusable configuration across `mise.toml`, `.devcontainer`, `scripts`, `.github/workflows`, `compose.yaml`, and `kubernetes`.
- Classify components as always included, optional, project-specific, or unsuitable for reuse.
- Identify hardcoded repository names, namespaces, image names, ports, GitHub secrets and deployment environments.
- Identify which components depend on others, such as Flux requiring Kubernetes.
- Document the extraction mapping in `docs/component-catalog.md`.
- Leave the original `devops-app` operational and unchanged during initial extraction.

Acceptance: Every component being extracted has a clear purpose, dependencies, and configurable inputs.

### Phase 2 — Create the Copier template

Repository: `merlrwx/devops-template` (new)

Start with one versioned Copier template rather than separate templates for every technology.

Proposed structure:

devops-template/ ├── copier.yml ├── template/ │   ├── .copier-answers.yml.jinja │   ├── README.md.jinja │   ├── AGENTS.md.jinja │   ├── mise.toml.jinja │   ├── .pre-commit-config.yaml │   ├── .devcontainer/ │   ├── .github/workflows/ │   ├── compose.yaml.jinja │   ├── kubernetes/ │   ├── scripts/ │   └── src/ ├── tests/ ├── examples/ └── docs/     └── component-catalog.md

Tasks:

- Configure `copier.yml` with project metadata and optional feature questions.
- Support three initial project types: `python-api`, `python-api-with-ui`, and `generic`.
- Parameterise application names, container images, namespaces, service ports and workflow paths.
- Generate `mise.toml` with only the required dependencies and tasks.
- Include a project-specific `AGENTS.md` that documents how to build, test and develop the generated repository.
- Include `.copier-answers.yml` so generated repositories retain their template origin.
- Use Copier's conditional exclusions to avoid generating disabled features.
- Keep generation free of infrastructure provisioning and external side effects.

Copier already supports conditional questions, validation, file exclusions, non-interactive inputs and recorded answers. You don't need a custom template-rendering engine.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://copier.readthedocs.io\&sz=32)

copier



Acceptance: Running Copier with only the default foundation generates a valid, minimal repository without unnecessary application or deployment files.

### Phase 3 — Implement conditional DevOps modules

Repository: `merlrwx/devops-template`

Build out the optional features in dependency order.

| Module      | Files generated                                                  |
| ----------- | ---------------------------------------------------------------- |
| Python      | `pyproject.toml`, uv configuration, Ruff, pytest                 |
| Containers  | Dockerfile, `.dockerignore`, optional Compose                    |
| Development | DevContainer configuration, mise setup tasks                     |
| CI          | Relevant GitHub Actions workflows                                |
| Releases    | Release Please configuration                                     |
| Kubernetes  | Kustomize base, deployment, service, probes                      |
| GitOps      | Flux-compatible application manifests and deployment integration |
| Security    | Trivy, dependency checks, pre-commit hooks                       |

For example, a simplified selection in `copier.yml`:

```
project_name:
  type: str

project_type:
  type: str
  choices:
    - python-api
    - python-api-with-ui
    - generic
  default: python-api

include_containers:
  type: bool
  default: true

include_kubernetes:
  type: bool
  default: false
  validator: >-
    {% if include_kubernetes and not include_containers %}
    Kubernetes requires container packaging.
    {% endif %}

include_flux:
  type: bool
  default: false
  when: "{{ include_kubernetes }}"
```

Tasks:

- Implement each feature independently where possible.
- Add conditional inclusion/exclusion rules.
- Prevent invalid feature combinations.
- Generate working scripts, not placeholder commands.
- Do not copy your existing app-specific Flux bootstrap or GitHub secret configuration unchanged.
- Avoid introducing Terraform or additional cloud providers until a real project requires them.

Acceptance: A Python API without Kubernetes does not contain Kubernetes tooling or workflows. A Kubernetes-enabled project receives a working, consistent deployment configuration.

### Phase 4 — Create a shared Codex/Pi skill

Most important for agent autonomy

Repository: `merlrwx/dotfiles`

Create a reusable `project-scaffold` skill following your existing skill deployment conventions.

A possible skill structure:

```
project-scaffold/
├── SKILL.md
└── references/
    └── selection-rules.md
```

The `SKILL.md` should tell Codex when to consider Copier, when to avoid it, and how to evaluate the project before selecting features. Codex's skills model supports agent-discovered instructions and supporting files, so this doesn't require a separate MCP server.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://developers.openai.com\&sz=32)

OpenAI API



Agent decision process

1. Inspect repository files, application architecture, intended runtime, target deployment and existing conventions.
2. Decide whether Copier adds value. Avoid scaffolding when an existing project is already sufficiently configured.
3. Select the smallest valid feature combination, using the documented component dependencies.
4. Prepare a temporary Copier answers YAML file and invoke Copier non-interactively at a pinned template version.
5. Validate generated configuration, resolve project-specific requirements and run appropriate checks.
6. Report what was included, excluded, changed manually and what still requires credentials or deployment configuration.

The skill should also implement these rules:

- Prefer existing project conventions over replacing working configuration.
- For an existing repository, generate into a temporary directory and selectively merge reviewed changes instead of overwriting files.
- Never automatically create cloud resources, configure production secrets, or deploy infrastructure just because a module is selected.
- Do not modify `.copier-answers.yml` manually.
- If unsupported technology is requested, generate the reusable foundation and implement the technology-specific integration separately.
- Explain meaningful deviations from the standard template.

Acceptance: Codex can create a new project from a natural-language request without asking you to manually select each Copier option.

### Phase 5 — Integrate with dotfiles and mise

Repository: `merlrwx/dotfiles`

Your existing dotfiles manage a pinned global mise toolset and provide the same core tooling on the host and in DevPod. That's the right place for the Copier executable and skill.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

merlrwx/dotfiles · GitHub



Tasks:

- Add Copier to the existing global mise configuration and update the committed lockfile.
- Deploy `project-scaffold` through the current agent-skill installation mechanism.
- Verify Codex and Pi can discover the skill.
- Ensure the lightweight DevPod dotfiles setup also makes Copier and the skill available.
- Add a short instruction to shared agent guidance to consider `project-scaffold` for new repositories.
- Keep Herdr untouched; it only needs to launch the agent as it already does.

Acceptance: A freshly provisioned agentbox or DevPod environment has the skill and can run Copier without manual installation.

### Phase 6 — Automated validation

Repository: `merlrwx/devops-template`

The risk with configurable templates is that one selection works and another silently generates broken configuration.

Use `pytest` and a Copier testing tool such as `pytest-copie`. It provides fixtures for rendering templates and testing generated projects.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://pytest-copie.readthedocs.io\&sz=32)

pytest-copie



Test at least these combinations:

| Test scenario      | Expected result                                                      |
| ------------------ | -------------------------------------------------------------------- |
| Basic Python API   | uv, linting and tests work                                           |
| Python API + UI    | Both services build and test                                         |
| Generic project    | No forced Python application                                         |
| Containers enabled | Image build succeeds                                                 |
| Kubernetes enabled | Kustomize builds and manifests validate                              |
| Flux disabled      | No Flux-specific deployment logic                                    |
| Invalid dependency | Configuration is rejected                                            |
| Template upgrade   | Existing project changes are preserved or conflicts clearly reported |

Tasks:

- Add generation tests for all supported presets.
- Validate generated YAML, TOML and JSON.
- Run actual `mise` tasks and container builds where relevant.
- Verify excluded modules leave no broken references.
- Run tests through GitHub Actions.
- Add an update test using an older template tag.
- Verify the new agent skill works on at least two realistically different projects.

Acceptance: Template changes cannot be merged unless the supported configurations generate successfully and pass their relevant checks.

### Phase 7 — Template lifecycle and adoption

Repositories: `devops-template`, `dotfiles`, and generated projects

Copier supports updating generated projects from newer template versions, using their recorded answers and versioned Git history. It can also add optional features later by updating the answers. Updates may produce conflicts, particularly where applications have heavily modified generated files.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://copier.readthedocs.io\&sz=32)

copier



Tasks:

- Publish the template's initial `v1.0.0` release.
- Pin new project generation to a release rather than an arbitrary branch.
- Document the generated project's ongoing relationship with the template.
- Add a skill path for evaluating and applying `copier update` on clean Git branches.
- Validate that project-specific customisations survive an update.
- Trial the workflow with a new Python application and a different technology stack.
- Add more presets only after a real use case demonstrates repeated value.

Acceptance: New projects can be generated autonomously, while existing generated projects can adopt template improvements without blindly losing their customisations.

### Phase 8 — Adapt existing applications

Repositories: `devops-template`, `dotfiles`, and existing application repositories

After the new-project workflow is stable, teach the agent skill to inspect an existing repository and select only suitable Copier components or updates. The agent must generate to a temporary directory, compare the result with the working tree, and selectively apply reviewed changes. Existing application conventions and working configuration take precedence.

Tasks:

- Define clear checks for when Copier adds value to an existing repository and when the agent should skip it.
- Trial selective adoption on the existing `devops-app` and a materially different project without replacing their working configuration.
- Validate template updates on clean branches and report conflicts for human review.

Acceptance: The agent can explain its component choices, preserve unrelated and working files, and validate a selective update without overwriting the application.

## 4. What using it would look like

For example, suppose you tell Codex:

> Create a FastAPI backend with PostgreSQL, Docker, GitHub Actions and deployment to Kubernetes using Flux. Reuse my existing DevOps standards where appropriate.

The agent might produce a temporary answers file:

```
project_name: knowledge-api
project_type: python-api
include_containers: true
include_github_actions: true
include_kubernetes: true
include_flux: true
git_repository_url: https://github.com/OWNER/knowledge-api.git
```

Then execute:

```
copier copy \
  --vcs-ref v1.0.0 \
  --data-file /tmp/knowledge-api-answers.yml \
  --defaults \
  gh:merlrwx/devops-template \
  knowledge-api
```

This is an example command for the template after it has been created and tagged, not a command that works against your repositories today. Copier documents both `--data-file` and `--vcs-ref` for this usage.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://copier.readthedocs.io\&sz=32)

copier

+1



Codex would then add the PostgreSQL-specific application configuration, validate the build and tests, and report what still needs configuration.

For a completely different request:

> Build an Astro marketing website deployed to Cloudflare Pages.

The agent should either reuse only the generic repository foundation or bypass Copier if the currently supported modules don't provide a meaningful advantage. It shouldn't force Docker, Kubernetes or Flux onto that project.

And for your existing `devops-app`, the agent should preserve the working implementation instead of trying to regenerate it from scratch.

## 5. Definition of done

Implementation checklist

- [x] Phase 0 scope confirmed; existing-app follow-up added
- [x] Reusable component catalog audited without changing `devops-app`
- [x] Conditional containers, DevContainer, GitHub Actions, Kubernetes, and Flux modules with dependency checks
- [x] Copier pinned through global Mise and skill deployed for Codex/Pi
- [x] Default and representative project configurations render and pass tests
- [x] Root and generated-project CI checks, module dependency tests, and an offline Copier update test
- [ ] Public versioned release, new-project trial, and final skill pin

## Final recommendation

I would make Phases 1–4 the initial milestone. Once those work, the remaining phases formalise distribution, testing and lifecycle management.

Don't introduce a separate agent-orchestration layer for this. You already have Herdr, Codex, Pi and reusable skills. The missing capability is a well-defined, versioned collection of reusable project configurations with clear selection rules.

Copier supplies the deterministic generation and updates. Your existing agent system supplies the project analysis and decisions. That separation gives you the flexibility you're after without adding unnecessary infrastructure.
