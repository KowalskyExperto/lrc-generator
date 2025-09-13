variable "gcp_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "gcp_region" {
  description = "The GCP region."
  type        = string
}

variable "repo_name" {
  description = "The name of the Artifact Registry repository."
  type        = string
}

variable "common_labels" {
  description = "Common labels to apply to all resources."
  type        = map(string)
}

variable "domain_name" {
  description = "The custom domain name for the application."
  type        = string
}
