variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "airflow-health-dashboard"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for the VPC"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "backend_cpu" {
  description = "CPU units for backend task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Memory for backend task in MB"
  type        = number
  default     = 1024
}

variable "frontend_cpu" {
  description = "CPU units for frontend task"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Memory for frontend task in MB"
  type        = number
  default     = 512
}

variable "scheduler_cpu" {
  description = "CPU units for scheduler task"
  type        = number
  default     = 256
}

variable "scheduler_memory" {
  description = "Memory for scheduler task in MB"
  type        = number
  default     = 512
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "domain_name" {
  description = "Domain name for the dashboard (optional)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS (optional)"
  type        = string
  default     = ""
}

variable "airflow_url" {
  description = "Airflow base URL"
  type        = string
}

variable "airflow_username" {
  description = "Airflow username (stored in Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "airflow_password" {
  description = "Airflow password (stored in Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint"
  type        = string
  sensitive   = true
}

variable "azure_openai_key" {
  description = "Azure OpenAI API key"
  type        = string
  sensitive   = true
}

variable "azure_openai_deployment" {
  description = "Azure OpenAI deployment name"
  type        = string
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  sensitive   = true
  default     = ""
}

variable "dashboard_url" {
  description = "Public URL of the dashboard"
  type        = string
  default     = ""
}

variable "morning_report_hour" {
  description = "Hour for morning report (0-23, UTC)"
  type        = number
  default     = 10
}

variable "morning_report_minute" {
  description = "Minute for morning report (0-59)"
  type        = number
  default     = 0
}

variable "evening_report_hour" {
  description = "Hour for evening report (0-23, UTC)"
  type        = number
  default     = 19
}

variable "evening_report_minute" {
  description = "Minute for evening report (0-59)"
  type        = number
  default     = 0
}
