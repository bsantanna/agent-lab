# Agent-Lab Helm Chart

```bash
helm upgrade --install agent-lab agent-lab \
  --namespace agent-lab --create-namespace \
  --repo "https://bsantanna.github.io/agent-lab" \
  --set config.ollama_endpoint="http://<ollama_endpoint>:11434" \
  --set config.telemetry_endpoint="http://<otel_collector_endpoint>:4318"
```
