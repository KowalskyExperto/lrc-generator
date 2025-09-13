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

resource "google_cloud_run_v2_service" "backend" {
  name     = "lrc-generator-backend"
  location = var.gcp_region
  labels   = var.common_labels

  template {
    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${var.repo_name}/lrc-generator-backend:latest"
      ports {
        container_port = 8000
      }

      env {
        name  = "FRONTEND_URL"
        value = "https://lrc-gen.${var.domain_name}"
      }

      env {
        name = "API_KEY_GENAI"
        value_source {
          secret_key_ref {
            secret  = "API_KEY_GENAI"
            version = "latest"
          }
        }
      }
    }

    service_account = "lrc-generator-backend-sa@${var.gcp_project_id}.iam.gserviceaccount.com"
  }
}

resource "google_cloud_run_v2_service" "frontend" {
  name     = "lrc-generator-frontend"
  location = var.gcp_region
  labels   = var.common_labels

  template {
    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${var.repo_name}/lrc-generator-frontend:latest"
      ports {
        container_port = 80
      }

      env {
        name  = "VITE_API_BASE_URL"
        value = "https://lrc-gen-api.${var.domain_name}"
      }
    }

    service_account = "lrc-generator-frontend-sa@${var.gcp_project_id}.iam.gserviceaccount.com"
  }
}

# --- IAM Bindings ---

resource "google_cloud_run_v2_service_iam_member" "frontend_public_access" {
  project  = google_cloud_run_v2_service.frontend.project
  location = google_cloud_run_v2_service.frontend.location
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "backend_private_access" {
  project  = google_cloud_run_v2_service.backend.project
  location = google_cloud_run_v2_service.backend.location
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:lrc-generator-frontend-sa@${var.gcp_project_id}.iam.gserviceaccount.com"
}

# --- Domain Mappings ---

resource "google_cloud_run_domain_mapping" "backend_domain" {
  location = var.gcp_region
  name     = "lrc-gen-api.${var.domain_name}"

  metadata {
    namespace = var.gcp_project_id
    labels    = var.common_labels
  }

  spec {
    route_name = google_cloud_run_v2_service.backend.name
  }
}

resource "google_cloud_run_domain_mapping" "frontend_domain" {
  location = var.gcp_region
  name     = "lrc-gen.${var.domain_name}"

  metadata {
    namespace = var.gcp_project_id
    labels    = var.common_labels
  }

  spec {
    route_name = google_cloud_run_v2_service.frontend.name
  }
}
