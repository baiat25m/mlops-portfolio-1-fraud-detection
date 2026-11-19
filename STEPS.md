# Steps

What this repo gets each week, from plan v3. Tick a box only when it works and is committed.
Weeks 9-12 and 25-27 build the LLMOps project in its own repo.

## Weeks 1-8: a tested, containerized, monitored service

### Week 1 · Nov 16-22 · Data quality pipeline on real data
- [x] Repo on GitHub, pre-commit installed
- [x] Pipeline runs on `fraudTrain.csv`: 1,296,675 rows, 0 dropped, all checks pass
- [ ] Fraud-rate check (0.1%-5%, limits in `schema.py`) with two tests
- [ ] Every number in `reports/data_quality.md` explained out loud

### Week 2 · Nov 23-29 · Model v1
- [ ] Time-based train/test split; features use nothing from after the transaction
- [ ] Personal columns (name, street, card number, birth date) kept out of the features
- [ ] Dummy and logistic baselines, LightGBM champion, compared on PR-AUC
- [ ] `train.py` runs with one command from a clean clone; saves the model and `metrics.json`
- [ ] `predict.py` loads the saved model and scores new rows
- [ ] Decision threshold based on cost, stored in config

### Week 3 · Nov 30-Dec 6 · PyTorch challenger, API and tests
- [ ] Small PyTorch model, saved and exported to ONNX, compared in the README
- [ ] Written error analysis: which fraud does the model miss?
- [ ] FastAPI `/predict`, `/health`, `/ready`; input validated with Pydantic
- [ ] Tests: valid, invalid, missing fields, wrong types, model fails to load

### Week 4 · Dec 7-13 · Docker and Compose
- [ ] Multi-stage Dockerfile, non-root user, image size before and after in the README
- [ ] Compose: API plus Postgres logging every prediction
- [ ] Integration tests run against the Compose services

### Week 5 · Dec 14-20 · Monitoring and load testing
- [ ] Metrics: requests, latency histogram, score distribution, model version
- [ ] Prometheus and Grafana in Compose, one dashboard, three alerts
- [ ] Load test; p95 latency and requests per second in the README

### Week 6 · Dec 21-27 · MLflow tracking and registry
- [ ] MLflow server with a Postgres backend; every training run logged
- [ ] The API loads the model with the `champion` alias; rollback shown live
- [ ] Makefile: `data`, `train`, `evaluate`, `serve`

### Week 7 · Dec 28-Jan 3 · Buffer

### Week 8 · Jan 4-10 · CI/CD with ML quality gates
- [ ] CI fails on bad schema, bad data, a low metric, or a model worse than the champion
- [ ] Image tagged with git SHA and model version, scanned with Trivy, pushed
- [ ] The same core pipeline in GitLab CI

## Weeks 13-16: Kubernetes

### Week 13 · Feb 8-14 · Kubernetes core
- [ ] Deployed to kind with plain manifests, dev and prod namespaces
- [ ] Probes tested by breaking the service; live rollback

### Week 14 · Feb 15-21 · Helm, Gateway API, autoscaling
- [ ] Helm chart: install, upgrade, roll back
- [ ] Traffic through Gateway API; load test scales the replicas

### Week 15 · Feb 22-28 · GitOps
- [ ] Argo CD deploys from Git; a Git revert rolls back
- [ ] Prometheus and Grafana on the cluster, latency per pod

### Week 16 · Mar 1-7 · Safe rollout and security
- [ ] Argo Rollouts canary: a bad version is aborted, a good one promoted
- [ ] RBAC and one network policy

## Weeks 17-24: AWS, retraining and drift

### Week 17 · Mar 8-14 · AWS foundations
- [ ] Billing alarm first; model in S3, image in ECR, scoped IAM roles

### Week 18 · Mar 15-21 · Terraform
- [ ] VPC, ECR, S3 and IAM as modules; environment rebuilt from zero twice

### Week 19 · Mar 22-28 · Buffer and half-way review

### Week 20 · Mar 29-Apr 4 · EKS and keyless CI/CD
- [ ] EKS from Terraform; the same Helm chart deployed by Argo CD
- [ ] GitHub-to-AWS OIDC: zero static keys; a merge deploys

### Week 21 · Apr 5-11 · EKS in production
- [ ] Secrets from AWS Secrets Manager; bad deploys roll back by themselves

### Week 22 · Apr 12-18 · Airflow
- [ ] DAG: ingest, validate, train; retries and a three-month backfill work

### Week 23 · Apr 19-25 · Retraining and drift
- [ ] A new model is registered only if it beats the champion
- [ ] Evidently drift reports by month; injected drift triggers retraining

### Week 24 · Apr 26-May 2 · Polish
- [ ] SageMaker one-day lab and a decision record
- [ ] Final README, architecture diagram, demo video

## Later
- [ ] Week 28: SLOs, threat model, two failure drills
- [ ] Week 32: five-minute demo from commit to retraining
