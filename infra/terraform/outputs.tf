output "alb_dns_name" {
  description = "Public URL for OpsPilot Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "ecs_cluster_name" {
  description = "Name of the ECS Cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS Service"
  value       = aws_ecs_service.main.name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL connection endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for container logs"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "backend_ecr_url" {
  description = "ECR Repository URL for Backend"
  value       = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_url" {
  description = "ECR Repository URL for Frontend"
  value       = aws_ecr_repository.frontend.repository_url
}
