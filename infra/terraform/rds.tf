# ==============================================================================
# AWS RDS PostgreSQL Instance (Encrypted at rest, private subnets)
# ==============================================================================

resource "aws_db_subnet_group" "postgres" {
  name        = "${var.project_name}-${var.environment}-db-subnet-group"
  description = "Subnet group for OpsPilot RDS PostgreSQL"
  subnet_ids  = aws_subnet.private_db[*].id

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  }
}

resource "aws_db_parameter_group" "postgres" {
  name   = "${var.project_name}-${var.environment}-pg15-params"
  family = "postgres15"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-pg15-params"
  }
}

resource "aws_db_instance" "postgres" {
  identifier                  = "${var.project_name}-${var.environment}-postgres"
  engine                      = "postgres"
  engine_version              = "15.7"
  instance_class              = var.db_instance_class
  allocated_storage           = var.db_allocated_storage
  max_allocated_storage       = 200 # Storage auto-scaling
  storage_type                = "gp3"
  storage_encrypted           = true
  multi_az                    = var.environment == "production" ? true : false
  publicly_accessible         = false

  db_name                     = var.db_name
  username                    = var.db_username
  password                    = random_password.db_password.result

  db_subnet_group_name        = aws_db_subnet_group.postgres.name
  vpc_security_group_ids      = [aws_security_group.rds.id]
  parameter_group_name        = aws_db_parameter_group.postgres.name

  backup_retention_period     = 7
  backup_window               = "03:00-04:00"
  maintenance_window          = "Sun:04:30-Sun:05:30"
  auto_minor_version_upgrade  = true
  deletion_protection         = var.environment == "production" ? true : false
  skip_final_snapshot         = var.environment == "production" ? false : true
  final_snapshot_identifier   = "${var.project_name}-${var.environment}-final-snapshot"

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres"
  }
}
