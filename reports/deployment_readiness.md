# Deployment Readiness

Source evidence used: `app.py`, `config.py`, `requirements.txt`, the verified import smoke tests, and the existing production-verification / release-readiness reports.

## Local Windows

- **Ready / Not Ready:** Ready
- **Missing requirements:** None for local execution.
- **Blocking issues:** None for the verified active path. The app entrypoint exists, dependencies are declared, and the runtime imports passed smoke tests.
- **Recommended deployment target:** Local Windows

## Streamlit Cloud

- **Ready / Not Ready:** Not Ready
- **Missing requirements:** Cloud secret management for API keys, explicit cloud runtime configuration, and durable storage strategy for generated files.
- **Blocking issues:** The app depends on environment variables for provider access and writes to local `data/` directories for exports, history, and evidence cache. The repository does not provide Streamlit Cloud-specific config or persistence handling.
- **Recommended deployment target:** Local Windows until cloud secrets and storage behavior are formalized

## Docker

- **Ready / Not Ready:** Not Ready
- **Missing requirements:** `Dockerfile`, container entrypoint, and container-oriented runtime instructions.
- **Blocking issues:** No container build definition is present, so the app cannot be packaged or reproduced as a container image from the repository alone.
- **Recommended deployment target:** Local Windows for now; Docker after container scaffolding is added

## Cloud Run

- **Ready / Not Ready:** Not Ready
- **Missing requirements:** Container image definition, `PORT`-aware startup contract, and an externalized storage plan.
- **Blocking issues:** Cloud Run requires a containerized deployment path, but the repository has no Dockerfile or deployment manifest. The app also persists outputs into local filesystem paths, which need a cloud storage strategy.
- **Recommended deployment target:** Docker first, then Cloud Run

## Railway

- **Ready / Not Ready:** Not Ready
- **Missing requirements:** Railway service configuration, container or buildpack instructions, and secrets/provisioning setup.
- **Blocking issues:** There is no Railway manifest or equivalent startup configuration in the repository, and the app still assumes local filesystem writes for generated artifacts and caches.
- **Recommended deployment target:** Docker first, then Railway

## Render

- **Ready / Not Ready:** Not Ready
- **Missing requirements:** Render service definition, build/start instructions, and a persistence plan for generated artifacts.
- **Blocking issues:** There is no Render config in the repo, and the app writes generated monographs, caches, and history to local directories that are not yet mapped to managed storage.
- **Recommended deployment target:** Docker first, then Render

## Overall Recommendation

Use **Local Windows** as the current deployment target.

The repository is verified for local execution, but it does not yet include the deployment scaffolding required for Docker-based cloud targets or the secrets/storage handling needed for managed cloud hosting.
