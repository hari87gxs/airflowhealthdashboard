# Secrets Manager for sensitive configuration
resource "aws_secretsmanager_secret" "airflow_credentials" {
  name                    = "${var.project_name}-airflow-credentials"
  description             = "Airflow API credentials"
  recovery_window_in_days = 7
  
  tags = {
    Name = "${var.project_name}-airflow-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "airflow_credentials" {
  secret_id = aws_secretsmanager_secret.airflow_credentials.id
  secret_string = jsonencode({
    username = var.airflow_username
    password = var.airflow_password
  })
}

resource "aws_secretsmanager_secret" "azure_openai" {
  name                    = "${var.project_name}-azure-openai"
  description             = "Azure OpenAI credentials"
  recovery_window_in_days = 7
  
  tags = {
    Name = "${var.project_name}-azure-openai"
  }
}

resource "aws_secretsmanager_secret_version" "azure_openai" {
  secret_id = aws_secretsmanager_secret.azure_openai.id
  secret_string = jsonencode({
    endpoint   = var.azure_openai_endpoint
    api_key    = var.azure_openai_key
    deployment = var.azure_openai_deployment
  })
}

resource "aws_secretsmanager_secret" "slack_config" {
  count                   = var.slack_webhook_url != "" ? 1 : 0
  name                    = "${var.project_name}-slack-config"
  description             = "Slack integration configuration"
  recovery_window_in_days = 7
  
  tags = {
    Name = "${var.project_name}-slack-config"
  }
}

resource "aws_secretsmanager_secret_version" "slack_config" {
  count     = var.slack_webhook_url != "" ? 1 : 0
  secret_id = aws_secretsmanager_secret.slack_config[0].id
  secret_string = jsonencode({
    webhook_url = var.slack_webhook_url
  })
}
