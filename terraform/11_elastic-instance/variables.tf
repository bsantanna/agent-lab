variable "elasticsearch_fqdn" {
  type        = string
  description = "FQDN for Elasticsearch access (e.g., elasticsearch.local or a public domain)"
}

variable "kibana_fqdn" {
  type        = string
  description = "FQDN for Kibana access (e.g., kibana.local or a public domain)"
}
