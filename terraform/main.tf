terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

module "github_cicd" {
  source            = "../terraform_modules"
  gcp_project_id    = var.gcp_project_id
  github_repository = var.github_repository
}
