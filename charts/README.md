# Agent-Lab - Helm Charts


```bash
helm upgrade --install agent-lab agent-lab \
  --repo https://bsantanna.github.io/agent-lab \
  --namespace agent-lab --create-namespace \
  --set config.ollama_endpoint="http://moon.btech.software:11434" \
  --set config.telemetry_endpoint="http://saturn.btech.software:4318" \
  --set ingress.enabled=true \
  --set ingres.hosts[0].host="agentlab.btech.software"

```
