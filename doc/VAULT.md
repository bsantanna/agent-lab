<h2 align="center"><a href="https://github.com/bsantanna/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">Vault Integration</h3>

---

## Hashicorp Vault

Agent-Lab makes use of [HashiCorp Vault](https://www.hashicorp.com/en/products/vault) for secure secret management. This integration allows you to store and retrieve sensitive information such as API keys, database credentials, and other secrets securely.

During application startup, Agent-Lab will automatically connect to Vault and retrieve the necessary secrets.

Vault is also used to manage secrets for configured Integrations, please check out the [Entity Domain Model reference](DOMAIN.md) for more details.

---

## Setting Up Vault

For local development, you can run Vault with provided Docker Compose files, which will set up a Vault server with a development configuration. This is suitable for testing and development purposes.

Please refer to [Developing Guide reference](DEVELOPING.md) for more details on how execute the Docker Compose files.

If you intend to use Vault in production, following our principles we recommend the usage of [Vault Kubernetes HA setup](https://developer.hashicorp.com/vault/docs/deploy/kubernetes).

--

## User Interface

After Vault is up, you can access the Vault UI at [http://localhost:8200](http://localhost:8200) and use the following credentials to log in;

- `dev-only-token`

