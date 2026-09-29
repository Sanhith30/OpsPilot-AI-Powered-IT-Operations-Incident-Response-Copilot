variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name (e.g. production, staging)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "opspilot"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for high availability"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "backend_cpu" {
  description = "Fargate CPU units for backend container (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "backend_memory" {
  description = "Fargate Memory (MB) for backend container"
  type        = number
  default     = 2048
}

variable "backend_desired_count" {
  description = "Number of active backend ECS tasks"
  type        = number
  default     = 2
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 50
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "opspilot"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "opspilot_admin"
}
