# GitLab

## Requirements

### 2 vCPU + 4 GB Memory

Disable Registry, Grafana (OOM)

## Quick Start

```shell
pipenv install
pipenv run cdk deploy --profile vj
```

## Manual

### Disable new sign ups

1. Go to `Admin Area > Settings > General`
2. Expand `Sign-up restrictions`
3. Uncheck `Sign-up enabled`
4. Save changes

### Disable Auto DevOps

1. Go to `Admin Area > Settings > CI/CD`
2. Expand `Continuous Integration and Deployment`
3. Uncheck `Default to Auto DevOps pipeline for all projects`
4. Save changes

### Register Runner

```python
docker exec gitlab-runner-<VERSION> gitlab-runner register \
    --non-interactive \
    --url "https://gitlab.example.com/" \
    --registration-token "<PROJECT_REGISTRATION_TOKEN>" \
    --executor "docker" \
    --docker-image alpine:latest \
    --description "docker-runner-<VERSION>" \
```
