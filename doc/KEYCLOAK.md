<h2 align="center"><a href="https://github.com/bsantanna/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">Keycloak</h3>

---
### Get Admin JWT

```bash
export ADMIN_USER=<admin_username>
export ADMIN_PASS=<admin_password>
export ADMIN_TOKEN=$(curl -s -X POST "https://<auth_fqdn>/realms/master/protocol/openid-connect/token" \
    -d "username=${ADMIN_USER}&password=${ADMIN_PASS}&grant_type=password&client_id=admin-cli" | jq -r '.access_token')
```
### Create a Realm

- Replace <realm_name> by a proper value

```bash
curl -X POST https://<auth_fqdn>/admin/realms \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -d '{"realm": "<realm_name>", "enabled": true}'
```

### Create a Client

```bash
curl -X POST https://<auth_fqdn>/admin/realms/<realm_name>/clients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -d '{
    "clientId": "<client_name>",
    "enabled": true,
    "protocol": "openid-connect",
    "publicClient": false,
    "redirectUris": ["https://<agent_lab_fqdn>/*"],
    "standardFlowEnabled": true,
    "clientAuthenticatorType": "client-secret"
  }'
```

#### Obtain client id:

```bash
export CLIENT_ID=$(curl -X GET "https://<auth_fqdn>/admin/realms/<realm_name>/clients?clientId=<client_name>" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" | jq -r '.[0].id')
```

#### Obtain client secret:

```bash
export CLIENT_SECRET=$(curl -X GET "https://<auth_fqdn>/admin/realms/<realm_name>/clients/${CLIENT_ID}/client-secret" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" | jq -r '.value')
```

### Create service account user

```bash
curl -X POST https://<auth_fqdn>/admin/realms/<realm_name>/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -d '{
    "username": "<username>",
    "enabled": true,
    "email": "<username>@example.com",
    "credentials": [{"type": "password", "value": "<user_password>", "temporary": false}]
  }'
```

- Edit details in UI

### Get User JWT

```bash
export USER_TOKEN=$(curl -s -X POST https://<auth_fqdn>/realms/<realm_name>/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=<client_name>" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "username=<username>" \
  -d "password=<user_password>" | jq -r '.access_token')
```

