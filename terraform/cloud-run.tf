resource "google_cloud_run_v2_service" "backend" {
  name     = "lrc-generator-backend"
  location = var.gcp_region
  labels   = local.common_labels

  # Ensure the service account and its permissions are created first
  depends_on = [module.github_cicd]

  template {
    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${var.repo_name}/lrc-generator-backend:latest"
      ports {
        container_port = 8000
      }

      env {
        name  = "FRONTEND_URL"
        # Using a safe default. This will be updated later.
        value = "http://localhost:8080"
      }

      env {
        name = "API_KEY_GENAI"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }
    }

    service_account = google_service_account.backend_sa.email
  }
}

resource "google_cloud_run_v2_service" "frontend" {
  name     = "lrc-generator-frontend"
  location = var.gcp_region
  labels   = local.common_labels

  # Ensure the backend service and its permissions are created first
  depends_on = [google_cloud_run_v2_service_iam_member.backend_private_access]

  template {
    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${var.repo_name}/lrc-generator-frontend:latest"
      ports {
        container_port = 80
      }

      env {
        name  = "VITE_API_BASE_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
    }

    service_account = google_service_account.frontend_sa.email
  }
}

# Allow unauthenticated access to the frontend service so users can visit the website
resource "google_cloud_run_v2_service_iam_member" "frontend_public_access" {
  project  = google_cloud_run_v2_service.frontend.project
  location = google_cloud_run_v2_service.frontend.location
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow ONLY the frontend service to access the backend service
resource "google_cloud_run_v2_service_iam_member" "backend_private_access" {
  project  = google_cloud_run_v2_service.backend.project
  location = google_cloud_run_v2_service.backend.location
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.frontend_sa.email}"
}