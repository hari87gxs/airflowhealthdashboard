output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "ecr_backend_repository_url" {
  description = "URL of the backend ECR repository"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repository_url" {
  description = "URL of the frontend ECR repository"
  value       = aws_ecr_repository.frontend.repository_url
}

output "ecr_scheduler_repository_url" {
  description = "URL of the scheduler ECR repository"
  value       = aws_ecr_repository.scheduler.repository_url
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis cluster port"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].port
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "backend_service_name" {
  description = "Name of the backend ECS service"
  value       = aws_ecs_service.backend.name
}

output "frontend_service_name" {
  description = "Name of the frontend ECS service"
  value       = aws_ecs_service.frontend.name
}

output "scheduler_service_name" {
  description = "Name of the scheduler ECS service"
  value       = var.slack_webhook_url != "" ? aws_ecs_service.scheduler[0].name : "Not created (Slack not configured)"
}

output "dashboard_url" {
  description = "URL to access the dashboard"
  value       = var.certificate_arn != "" ? "https://${var.domain_name != "" ? var.domain_name : aws_lb.main.dns_name}" : "http://${aws_lb.main.dns_name}"
}

output "api_url" {
  description = "URL to access the API"
  value       = var.certificate_arn != "" ? "https://${var.domain_name != "" ? var.domain_name : aws_lb.main.dns_name}/api" : "http://${aws_lb.main.dns_name}/api"
}
