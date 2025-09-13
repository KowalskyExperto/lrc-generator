resource "google_artifact_registry_repository" "repo" {
  repository_id = var.repo_name
  location      = var.gcp_region
  format        = "DOCKER"
  labels        = local.common_labels
}

# Grant the CI/CD service account specific permission to write to this repository
resource "google_artifact_registry_repository_iam_member" "deployer_writer" {
  project    = google_artifact_registry_repository.repo.project
  location   = google_artifact_registry_repository.repo.location
  repository = google_artifact_registry_repository.repo.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${module.github_cicd.google_service_account.github_actions_deployer_sa.email}"
}
