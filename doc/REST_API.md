<h2 align="center"><a href="https://github.com/bsantanna/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">REST API</h3>

---

| Section | Method | Endpoint | Description |
|---|---|---|---|
| auth | POST | /auth/login | Create a new bearer token |
| auth | POST | /auth/renew | Renew an existing bearer token |
| agents | GET | /agents/list | Get all agents |
| agents | GET | /agents/{agent_id} | Get agent by ID |
| agents | POST | /agents/create | Create a new agent |
| agents | DELETE | /agents/delete/{agent_id} | Delete an agent |
| agents | POST | /agents/update | Update agent basic information |
| agents | POST | /agents/update_setting | Update agent setting |
| attachments | POST | /attachments/upload | Upload a file attachment |
| attachments | GET | /attachments/download/{attachment_id} | Download an attachment by ID |
| attachments | POST | /attachments/embeddings | Generate embeddings for an attachment |
| integrations | GET | / Integrations/list | List all integrations |
| integrations | GET | /integrations/{integration_id} | Get integration details |
| integrations | POST | /integrations/create | Create a new integration |
| integrations | DELETE | /integrations/delete/{integration_id} | Delete an integration |
| llms | GET | /llms/list | List all language models |
| llms | POST | /llms/create | Create a new language model |
| llms | GET | /llms/{language_model_id} | Get language model details |
| llms | DELETE | /llms/delete/{language_model_id} | Delete a language model |
| llms | POST | /llms/update | Update language model configuration |
| llms | POST | /llms/update_setting | Update language model setting |
| messages | POST | /messages/list | Retrieve messages for an agent |
| messages | POST | /messages/post | Send a message to an agent |
| messages | GET | /messages/{message_id} | Get expanded message details |
| messages | DELETE | /messages/delete/{message_id} | Delete a message |
