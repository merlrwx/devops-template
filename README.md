# DevOps Template

A Copier template for creating small, maintainable application repositories with an agent choosing only the development and delivery features that fit the project.

The template is being developed from the working `devops-app` reference. See [the implementation plan](plans/initial-plan-draft.md) for the confirmed scope, phases, and acceptance criteria.

See the [usage guide](docs/usage.md) for prerequisites, safe project generation, feature selection, validation, and template updates.

## Status

The initial `v1.1.0` release is available on [GitHub](https://github.com/merlrwx/devops-template/releases/tag/v1.1.0). It supports `python-api`, `python-api-with-ui`, and `generic` project types, with optional container/Compose, DevContainer, GitHub Actions CI, Kubernetes, and Flux features. The root GitHub Actions workflow validates template rendering and generated-project behavior.

See [feature selection and delivery](docs/features.md) for the full profile, security gates, releases, GitOps promotion, persistence and Kubernetes E2E.
