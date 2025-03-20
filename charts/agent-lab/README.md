# Agent-Lab Helm Chart


```bash
helm upgrade --install agent-lab agent-lab \
  --namespace agent-lab --create-namespace \
  --repo "https://bsantanna.github.io/agent-lab" \
  --set config.ollama_endpoint="http://moon.btech.software:11434" \
  --set config.telemetry_endpoint="http://saturn.btech.software:4318" \
  --set ingress.enabled="true" \
  --set ingress.hosts[0].host="agentlab.btech.software" \
  --set ingress.hosts[0].paths[0].path="/" \
  --set ingress.hosts[0].paths[0].pathType="Prefix"
```
