# =============================================================================
# CyMed AWS baseline
# VPC (3 AZs) + EKS + RDS Postgres 16 Multi-AZ + ElastiCache Redis + ALB + S3
# All data classes get their own KMS CMK (defence in depth for HIPAA scope).
#
# This file wires named modules from the terraform-aws-modules registry — see
# each module's README for the full parameter surface.
# =============================================================================

# -----------------------------------------------------------------------------
# Local values
# -----------------------------------------------------------------------------
locals {
  name = "${var.cluster_name}-${var.environment}"

  artifacts_bucket = coalesce(
    var.artifacts_bucket_name,
    "${var.cluster_name}-artifacts-${var.environment}-${data.aws_caller_identity.current.account_id}"
  )

  common_tags = merge(var.tags, {
    Environment = var.environment
  })
}

data "aws_caller_identity" "current" {}
data "aws_partition"       "current" {}

# =============================================================================
# KMS — one CMK per data class
# =============================================================================
module "kms_rds" {
  source  = "terraform-aws-modules/kms/aws"
  version = "~> 3.0"

  aliases                 = ["cymed/${var.environment}/rds"]
  description             = "CyMed ${var.environment} — RDS encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  key_usage               = "ENCRYPT_DECRYPT"
  key_administrators      = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"]

  tags = merge(local.common_tags, { DataClass = "rds" })
}

module "kms_s3" {
  source  = "terraform-aws-modules/kms/aws"
  version = "~> 3.0"

  aliases                 = ["cymed/${var.environment}/s3"]
  description             = "CyMed ${var.environment} — S3 (artefacts, backups)"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  key_usage               = "ENCRYPT_DECRYPT"
  key_administrators      = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"]

  tags = merge(local.common_tags, { DataClass = "s3" })
}

module "kms_secrets" {
  source  = "terraform-aws-modules/kms/aws"
  version = "~> 3.0"

  aliases                 = ["cymed/${var.environment}/secrets"]
  description             = "CyMed ${var.environment} — Secrets Manager"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  key_usage               = "ENCRYPT_DECRYPT"
  key_administrators      = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"]

  tags = merge(local.common_tags, { DataClass = "secrets" })
}

# =============================================================================
# VPC — 3 AZs, public + private + isolated database subnets
# =============================================================================
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.5"

  name = "${local.name}-vpc"
  cidr = var.vpc_cidr

  azs              = var.azs
  public_subnets   = var.public_subnets
  private_subnets  = var.private_subnets
  database_subnets = var.database_subnets

  enable_nat_gateway     = true
  single_nat_gateway     = false     # one NAT per AZ — HA
  one_nat_gateway_per_az = true
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # Isolate DB subnets from the public route table.
  create_database_subnet_route_table     = true
  create_database_subnet_group            = true
  create_database_internet_gateway_route  = false
  create_database_nat_gateway_route       = false

  # Flow logs to CloudWatch — required for HIPAA network audit.
  enable_flow_log                     = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role  = true
  flow_log_max_aggregation_interval    = 60

  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${local.name}"       = "shared"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/${local.name}"       = "shared"
  }

  tags = local.common_tags
}

# =============================================================================
# EKS cluster + managed node group
# =============================================================================
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = local.name
  cluster_version = var.kubernetes_version

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true    # tighten via cluster_endpoint_public_access_cidrs

  enable_irsa                    = true
  cluster_encryption_config = {
    provider_key_arn = module.kms_secrets.key_arn
    resources        = ["secrets"]
  }

  cluster_addons = {
    coredns    = { most_recent = true }
    kube-proxy = { most_recent = true }
    vpc-cni    = { most_recent = true }
    aws-ebs-csi-driver = { most_recent = true }
  }

  eks_managed_node_groups = {
    default = {
      name           = "${local.name}-default"
      instance_types = var.node_instance_type
      min_size       = var.node_group_size.min
      desired_size   = var.node_group_size.desired
      max_size       = var.node_group_size.max

      capacity_type = "ON_DEMAND"

      # Spread across all three AZs — matches VPC subnet layout.
      subnet_ids = module.vpc.private_subnets

      labels = {
        role = "workload"
      }
    }
  }

  tags = local.common_tags
}

# =============================================================================
# Security groups for the data tier
# =============================================================================
resource "aws_security_group" "rds" {
  name        = "${local.name}-rds-sg"
  description = "Allow Postgres from EKS nodes only"
  vpc_id      = module.vpc.vpc_id

  tags = local.common_tags
}

resource "aws_security_group_rule" "rds_ingress_eks" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds.id
  source_security_group_id = module.eks.node_security_group_id
  description              = "Postgres 5432 from EKS node SG"
}

resource "aws_security_group_rule" "rds_egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.rds.id
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Egress to anywhere (default)"
}

resource "aws_security_group" "redis" {
  name        = "${local.name}-redis-sg"
  description = "Allow Redis from EKS nodes only"
  vpc_id      = module.vpc.vpc_id

  tags = local.common_tags
}

resource "aws_security_group_rule" "redis_ingress_eks" {
  type                     = "ingress"
  from_port                = 6379
  to_port                  = 6379
  protocol                 = "tcp"
  security_group_id        = aws_security_group.redis.id
  source_security_group_id = module.eks.node_security_group_id
  description              = "Redis 6379 from EKS node SG"
}

# =============================================================================
# RDS Postgres 16 — Multi-AZ, encrypted, PITR
# =============================================================================
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.5"

  identifier = "${local.name}-pg"

  engine               = "postgres"
  engine_version       = "16"
  family               = "postgres16"
  major_engine_version = "16"
  instance_class       = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = module.kms_rds.key_arn

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # 30-day PITR + weekly-window maintenance.
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "Sun:03:30-Sun:05:00"
  copy_tags_to_snapshot   = true
  deletion_protection     = true
  skip_final_snapshot     = false
  final_snapshot_identifier = "${local.name}-pg-final"

  # Observability
  performance_insights_enabled          = true
  performance_insights_kms_key_id       = module.kms_rds.key_arn
  performance_insights_retention_period = 7
  monitoring_interval                   = 30
  create_monitoring_role                = true
  monitoring_role_name                  = "${local.name}-rds-monitoring"
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]

  tags = merge(local.common_tags, { DataClass = "phi" })
}

# =============================================================================
# ElastiCache Redis — 2 nodes, encryption at rest + in transit
# =============================================================================
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name}-redis-subnets"
  subnet_ids = module.vpc.private_subnets
  tags       = local.common_tags
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${local.name}-redis"
  description                = "CyMed ${var.environment} — Redis (cache + Celery broker)"
  engine                     = "redis"
  engine_version             = "7.1"
  node_type                  = var.redis_node_type
  num_cache_clusters         = var.redis_num_cache_nodes
  parameter_group_name       = "default.redis7"
  port                       = 6379
  automatic_failover_enabled = var.redis_num_cache_nodes > 1
  multi_az_enabled           = var.redis_num_cache_nodes > 1

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id                 = module.kms_secrets.key_arn

  snapshot_retention_limit = 7
  snapshot_window          = "01:00-02:00"
  maintenance_window       = "sun:04:00-sun:05:00"

  tags = local.common_tags
}

# =============================================================================
# ALB — placeholder for external ingress if not using nginx-ingress
# =============================================================================
module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.0"

  name    = "${local.name}-alb"
  vpc_id  = module.vpc.vpc_id
  subnets = module.vpc.public_subnets

  enable_deletion_protection = true

  security_group_ingress_rules = {
    all_https = {
      from_port   = 443
      to_port     = 443
      ip_protocol = "tcp"
      cidr_ipv4   = "0.0.0.0/0"
      description = "HTTPS from the internet"
    }
    all_http = {
      from_port   = 80
      to_port     = 80
      ip_protocol = "tcp"
      cidr_ipv4   = "0.0.0.0/0"
      description = "HTTP (redirect to HTTPS)"
    }
  }
  security_group_egress_rules = {
    all = {
      ip_protocol = "-1"
      cidr_ipv4   = "0.0.0.0/0"
    }
  }

  listeners = {
    http_redirect = {
      port     = 80
      protocol = "HTTP"
      redirect = {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
    # https listener + target groups wired in by app team after ACM cert exists.
  }

  tags = local.common_tags
}

# =============================================================================
# S3 — artefact bucket, versioned, SSE-KMS, public access blocked
# =============================================================================
module "s3_artifacts" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 4.1"

  bucket = local.artifacts_bucket

  force_destroy       = false
  object_ownership    = "BucketOwnerEnforced"
  block_public_acls   = true
  block_public_policy = true
  ignore_public_acls  = true
  restrict_public_buckets = true

  versioning = {
    enabled    = true
    mfa_delete = false
  }

  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        kms_master_key_id = module.kms_s3.key_arn
        sse_algorithm     = "aws:kms"
      }
      bucket_key_enabled = true
    }
  }

  lifecycle_rule = [
    {
      id      = "abort-incomplete-multipart"
      enabled = true
      abort_incomplete_multipart_upload = {
        days_after_initiation = 7
      }
    },
    {
      id      = "expire-old-versions"
      enabled = true
      noncurrent_version_expiration = {
        noncurrent_days = 365
      }
    }
  ]

  logging = {
    target_bucket = local.artifacts_bucket
    target_prefix = "logs/"
  }

  tags = merge(local.common_tags, { DataClass = "s3" })
}
