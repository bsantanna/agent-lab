# Agent-Lab - Helm Charts

```bash
helm repo add agent-lab https://bsantanna.github.io/agent-lab/
helm repo update
```

```bash
helm install agent-lab agent-lab/agent-lab \
  --create-namespace --namespace agent-lab
```

```
