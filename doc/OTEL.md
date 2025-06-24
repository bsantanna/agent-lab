<h2 align="center"><a href="https://github.com/bsantanna/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">OpenTelemetry Integration</h3>

---

Observability is a key aspect of Agent-Lab, and we leverage on top of [OpenTelemetry](https://opentelemetry.io/) and [OpenLLMetry](https://github.com/traceloop/openllmetry) to provide comprehensive insights into the system's performance and behavior. This integration allows for detailed monitoring, logging, and tracing of interactions within the Agent-Lab environment.

## Setting Up OpenTelemetry

For local development, you can run OpenTelemetry with provided Docker Compose files, which will set up a otel-collector-contrib server with a development configuration. This is suitable for testing and development purposes.

Please refer to [Developing Guide reference](DEV_GUIDE.md) for more details on how execute the Docker Compose files.

If you intend to use OpenTelemetry in production, we recommend following the [OpenTelemetry documentation](https://opentelemetry.io/docs/) for best practices and configurations.

### Grafana reference implementation

For development purposes, we provide [a reference implementation of Grafana](otel/GRAFANA.md) to visualize the metrics and traces collected by OpenTelemetry.


### OpenSearch Dashboards reference implementation

For development purposes, we provide [a reference implementation of OpenSearch Dashboards](otel/OPENSEARCH.md) to visualize the metrics and traces collected by OpenTelemetry.
