variable "cluster_name" {
  description = "EKS cluster name; also used as the prefix for related resources."
  type        = string
  default     = "cymed"
}

variable "region" {
  description = "AWS region for the cluster and all regional resources."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod). Feeds tags and workspace-scoped resource names."
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC. Should not overlap with any peered VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "azs" {
  description = "Availability zones to spread subnets across (3 for HA)."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets — one per AZ."
  type        = list(string)
  default     = ["10.42.0.0/20", "10.42.16.0/20", "10.42.32.0/20"]
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets — one per AZ."
  type        = list(string)
  default     = ["10.42.48.0/20", "10.42.64.0/20", "10.42.80.0/20"]
}

variable "database_subnets" {
  description = "CIDR blocks for isolated database subnets — one per AZ."
  type        = list(string)
  default     = ["10.42.96.0/22", "10.42.100.0/22", "10.42.104.0/22"]
}

variable "kubernetes_version" {
  description = "EKS control-plane version."
  type        = string
  default     = "1.30"
}

variable "node_instance_type" {
  description = "Instance type(s) for the managed node group."
  type        = list(string)
  default     = ["m5.large"]
}

variable "node_group_size" {
  description = "Managed node group scaling bounds."
  type = object({
    min     = number
    desired = number
    max     = number
  })
  default = {
    min     = 2
    desired = 3
    max     = 10
  }
}

variable "db_instance_class" {
  description = "RDS instance class for the primary."
  type        = string
  default     = "db.m6g.large"
}

variable "db_allocated_storage" {
  description = "Initial storage in GB. Storage autoscaling is enabled up to db_max_allocated_storage."
  type        = number
  default     = 100
}

variable "db_max_allocated_storage" {
  description = "Ceiling for RDS storage autoscaling."
  type        = number
  default     = 1000
}

variable "db_username" {
  description = "Master username for RDS."
  type        = string
  default     = "cymed"
}

variable "db_password" {
  description = "Master password for RDS. Prefer sourcing from AWS Secrets Manager in production."
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Initial database name to create."
  type        = string
  default     = "cymed"
}

variable "redis_node_type" {
  description = "ElastiCache node type."
  type        = string
  default     = "cache.m6g.large"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis replication group nodes (primary + replicas)."
  type        = number
  default     = 2
}

variable "artifacts_bucket_name" {
  description = "S3 bucket for application artefacts (uploads, exports, reports)."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags applied to every resource that supports tagging."
  type        = map(string)
  default = {
    Project     = "cymed"
    ManagedBy   = "terraform"
    Owner       = "platform"
    CostCenter  = "cymed-platform"
    Compliance  = "hipaa"
  }
}
