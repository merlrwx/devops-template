# DevOps Template

A Copier template for creating small, maintainable application repositories with an agent choosing only the development and delivery features that fit the project.

The template is being developed from the working `devops-app` reference. See [the implementation plan](plans/initial-plan-draft.md) for the confirmed scope, phases, and acceptance criteria.

See the [usage guide](docs/usage.md) for prerequisites, safe project generation, feature selection, validation, and template updates.

## Status

This repository is under active development. It supports `python-api`, `python-api-with-ui`, and `generic` project types, with optional container/Compose, DevContainer, and GitHub Actions CI features. The root GitHub Actions workflow validates template rendering. A versioned template release is not published yet.
