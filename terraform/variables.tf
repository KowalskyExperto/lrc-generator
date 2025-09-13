variable "gcp_project_id" {
  description = "The GCP project ID to deploy to."
  type        = string
}

variable "gcp_region" {
  description = "The GCP region to deploy resources in."
  type        = string
  default     = "northamerica-south1"
}

variable "repo_name" {
  description = "The name of the Artifact Registry repository."
  type        = string
  default     = "lrc-generator-repo"
}

variable "github_repository" {
  description = "The GitHub repository in the format 'owner/repo-name'."
  type        = string
}
