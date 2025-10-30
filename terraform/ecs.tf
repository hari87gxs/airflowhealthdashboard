# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = 7
  
  tags = {
    Name = "${var.project_name}-logs"
  }
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-ecs-task-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
  
  tags = {
    Name = "${var.project_name}-ecs-task-execution-role"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Policy for Secrets Access
resource "aws_iam_role_policy" "secrets_access" {
  name = "${var.project_name}-secrets-access"
  role = aws_iam_role.ecs_task_execution.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = [
        aws_secretsmanager_secret.airflow_credentials.arn,
        aws_secretsmanager_secret.azure_openai.arn
      ]
    }]
  })
}

# IAM Policy for Slack Secrets (if enabled)
resource "aws_iam_role_policy" "slack_secrets_access" {
  count = var.slack_webhook_url != "" ? 1 : 0
  name  = "${var.project_name}-slack-secrets-access"
  role  = aws_iam_role.ecs_task_execution.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = [
        aws_secretsmanager_secret.slack_config[0].arn
      ]
    }]
  })
}

# ECS Task Role (for application permissions)
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-ecs-task-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
  
  tags = {
    Name = "${var.project_name}-ecs-task-role"
  }
}

# Backend Task Definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([{
    name  = "backend"
    image = "${aws_ecr_repository.backend.repository_url}:latest"
    
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    
    environment = [
      {
        name  = "AIRFLOW_BASE_URL"
        value = var.airflow_url
      },
      {
        name  = "REDIS_HOST"
        value = aws_elasticache_cluster.redis.cache_nodes[0].address
      },
      {
        name  = "REDIS_PORT"
        value = "6379"
      },
      {
        name  = "DASHBOARD_URL"
        value = var.dashboard_url != "" ? var.dashboard_url : "http://${aws_lb.main.dns_name}"
      },
      {
        name  = "SLACK_ENABLED"
        value = var.slack_webhook_url != "" ? "true" : "false"
      },
      {
        name  = "SCHEDULED_REPORTS_ENABLED"
        value = "false"  # Disabled for backend, enabled only in scheduler
      }
    ]
    
    secrets = concat([
      {
        name      = "AIRFLOW_USERNAME"
        valueFrom = "${aws_secretsmanager_secret.airflow_credentials.arn}:username::"
      },
      {
        name      = "AIRFLOW_PASSWORD"
        valueFrom = "${aws_secretsmanager_secret.airflow_credentials.arn}:password::"
      },
      {
        name      = "AZURE_OPENAI_ENDPOINT"
        valueFrom = "${aws_secretsmanager_secret.azure_openai.arn}:endpoint::"
      },
      {
        name      = "AZURE_OPENAI_API_KEY"
        valueFrom = "${aws_secretsmanager_secret.azure_openai.arn}:api_key::"
      },
      {
        name      = "AZURE_OPENAI_DEPLOYMENT_NAME"
        valueFrom = "${aws_secretsmanager_secret.azure_openai.arn}:deployment::"
      }
    ], var.slack_webhook_url != "" ? [{
      name      = "SLACK_WEBHOOK_URL"
      valueFrom = "${aws_secretsmanager_secret.slack_config[0].arn}:webhook_url::"
    }] : [])
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "backend"
      }
    }
    
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
  
  tags = {
    Name = "${var.project_name}-backend-task"
  }
}

# Frontend Task Definition
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.project_name}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([{
    name  = "frontend"
    image = "${aws_ecr_repository.frontend.repository_url}:latest"
    
    portMappings = [{
      containerPort = 80
      protocol      = "tcp"
    }]
    
    environment = [
      {
        name  = "VITE_API_BASE_URL"
        value = "http://${aws_lb.main.dns_name}/api"
      }
    ]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "frontend"
      }
    }
  }])
  
  tags = {
    Name = "${var.project_name}-frontend-task"
  }
}

# Scheduler Task Definition
resource "aws_ecs_task_definition" "scheduler" {
  family                   = "${var.project_name}-scheduler"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.scheduler_cpu
  memory                   = var.scheduler_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([{
    name  = "scheduler"
    image = "${aws_ecr_repository.scheduler.repository_url}:latest"
    
    environment = [
      {
        name  = "AIRFLOW_BASE_URL"
        value = var.airflow_url
      },
      {
        name  = "REDIS_HOST"
        value = aws_elasticache_cluster.redis.cache_nodes[0].address
      },
      {
        name  = "REDIS_PORT"
        value = "6379"
      },
      {
        name  = "DASHBOARD_URL"
        value = var.dashboard_url != "" ? var.dashboard_url : "http://${aws_lb.main.dns_name}"
      },
      {
        name  = "SLACK_ENABLED"
        value = var.slack_webhook_url != "" ? "true" : "false"
      },
      {
        name  = "SCHEDULED_REPORTS_ENABLED"
        value = var.slack_webhook_url != "" ? "true" : "false"
      },
      {
        name  = "MORNING_REPORT_HOUR"
        value = tostring(var.morning_report_hour)
      },
      {
        name  = "MORNING_REPORT_MINUTE"
        value = tostring(var.morning_report_minute)
      },
      {
        name  = "EVENING_REPORT_HOUR"
        value = tostring(var.evening_report_hour)
      },
      {
        name  = "EVENING_REPORT_MINUTE"
        value = tostring(var.evening_report_minute)
      }
    ]
    
    secrets = concat([
      {
        name      = "AIRFLOW_USERNAME"
        valueFrom = "${aws_secretsmanager_secret.airflow_credentials.arn}:username::"
      },
      {
        name      = "AIRFLOW_PASSWORD"
        valueFrom = "${aws_secretsmanager_secret.airflow_credentials.arn}:password::"
      },
      {
        name      = "AZURE_OPENAI_ENDPOINT"
        valueFrom = "${aws_secretsmanager_secret.azure_openai.arn}:endpoint::"
      },
      {
        name      = "AZURE_OPENAI_API_KEY"
        valueFrom = "${aws_secretsmanager_secret.azure_openai.arn}:api_key::"
      },
      {
        name      = "AZURE_OPENAI_DEPLOYMENT_NAME"
        valueFrom = "${aws_secretsmanager_secret.azure_openai.arn}:deployment::"
      }
    ], var.slack_webhook_url != "" ? [{
      name      = "SLACK_WEBHOOK_URL"
      valueFrom = "${aws_secretsmanager_secret.slack_config[0].arn}:webhook_url::"
    }] : [])
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "scheduler"
      }
    }
  }])
  
  tags = {
    Name = "${var.project_name}-scheduler-task"
  }
}

# Backend ECS Service
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }
  
  depends_on = [aws_lb_listener.http]
  
  tags = {
    Name = "${var.project_name}-backend-service"
  }
}

# Frontend ECS Service
resource "aws_ecs_service" "frontend" {
  name            = "${var.project_name}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 80
  }
  
  depends_on = [aws_lb_listener.http]
  
  tags = {
    Name = "${var.project_name}-frontend-service"
  }
}

# Scheduler ECS Service
resource "aws_ecs_service" "scheduler" {
  count           = var.slack_webhook_url != "" ? 1 : 0
  name            = "${var.project_name}-scheduler"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.scheduler.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.scheduler.id]
    assign_public_ip = false
  }
  
  tags = {
    Name = "${var.project_name}-scheduler-service"
  }
}
