resource "google_service_account" "backend_sa" {
  account_id   = "lrc-generator-backend-sa"
  display_name = "LRC Generator Backend Service Account"
  description  = "Service account for the LRC Generator backend Cloud Run service."
}

resource "google_service_account" "frontend_sa" {
  account_id   = "lrc-generator-frontend-sa"
  display_name = "LRC Generator Frontend Service Account"
  description  = "Service account for the LRC Generator frontend Cloud Run service."
}

# Grant the backend service account permission to read from Artifact Registry
resource "google_project_iam_member" "backend_artifact_reader" {
  project = var.gcp_project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# Grant the frontend service account permission to read from Artifact Registry
resource "google_project_iam_member" "frontend_artifact_reader" {
  project = var.gcp_project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.frontend_sa.email}"
}
