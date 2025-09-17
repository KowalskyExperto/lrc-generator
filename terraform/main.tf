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

resource "google_service_account_iam_member" "github_sa_backend_user" {
  service_account_id = google_service_account.backend_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${module.github_cicd.deployer_sa_email}"
}

resource "google_service_account_iam_member" "github_sa_frontend_user" {
  service_account_id = google_service_account.frontend_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${module.github_cicd.deployer_sa_email}"
}