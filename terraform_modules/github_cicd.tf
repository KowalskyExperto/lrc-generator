variable "gcp_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "github_repository" {
  description = "The GitHub repository in the format 'owner/repo-name'."
  type        = string
}

resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Pool for authenticating GitHub Actions workflows."
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC Provider"
  attribute_mapping = {
    "google.subject"     = "assertion.sub"
    "attribute.actor"    = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  # This condition allows us to filter access by repository
  attribute_condition = "assertion.repository.startsWith('KowalskyExperto/')"
}

resource "google_service_account" "github_actions_deployer_sa" {
  account_id   = "github-actions-deployer-sa"
  display_name = "GitHub Actions Deployer SA"
  description  = "Service account for CI/CD pipelines to deploy applications."
}

# Grant the SA the necessary roles to manage the application resources
resource "google_project_iam_member" "deployer_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/iam.serviceAccountAdmin",
    "roles/secretmanager.admin",
    "roles/iam.serviceAccountUser"
  ])

  project = var.gcp_project_id
  role    = each.key
  member  = google_service_account.github_actions_deployer_sa.member
}

# Allow the GitHub identity to impersonate the GCP service account
resource "google_service_account_iam_member" "github_impersonation" {
  service_account_id = google_service_account.github_actions_deployer_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repository}"

  depends_on = [google_iam_workload_identity_pool_provider.github_provider]
}
