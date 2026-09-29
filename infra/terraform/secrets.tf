# ==============================================================================
# AWS Secrets Manager: Sensitive Configurations
# ==============================================================================

# Database Master Password Secret
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${var.project_name}/${var.environment}/database"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-db-secret"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    engine   = "postgres"
    host     = aws_db_instance.postgres.address
    port     = 5432
    username = var.db_username
    password = random_password.db_password.result
    database = var.db_name
  })
}

# Application Secrets (JWT, Gemini, Pinecone)
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${var.project_name}/${var.environment}/app-secrets"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-app-secrets"
  }
}
