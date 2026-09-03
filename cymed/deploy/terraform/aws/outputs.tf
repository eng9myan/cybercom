output "region" {
  description = "AWS region for this stack."
  value       = var.region
}

output "cluster_name" {
  description = "EKS cluster name."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS API server endpoint."
  value       = module.eks.cluster_endpoint
}

output "cluster_ca" {
  description = "EKS API server CA data (base64) — feed into kubeconfig."
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_oidc_issuer_url" {
  description = "OIDC issuer URL for IRSA setups."
  value       = module.eks.cluster_oidc_issuer_url
}

output "vpc_id" {
  description = "VPC id."
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet ids — deploy workloads here."
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "Public subnet ids — for the ALB."
  value       = module.vpc.public_subnets
}

output "rds_endpoint" {
  description = "RDS writer endpoint (host:port)."
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "rds_reader_endpoint" {
  description = "RDS reader endpoint (present when read replicas exist)."
  value       = try(module.rds.db_instance_reader_endpoint, null)
  sensitive   = true
}

output "redis_primary_endpoint" {
  description = "Redis primary endpoint address."
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive   = true
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint address (Multi-AZ)."
  value       = aws_elasticache_replication_group.redis.reader_endpoint_address
  sensitive   = true
}

output "alb_dns_name" {
  description = "ALB DNS name — point Route53 records here."
  value       = module.alb.dns_name
}

output "alb_zone_id" {
  description = "ALB hosted zone id — for Route53 alias records."
  value       = module.alb.zone_id
}

output "artifacts_bucket_name" {
  description = "S3 bucket for application artefacts."
  value       = module.s3_artifacts.s3_bucket_id
}

output "kms_key_arns" {
  description = "ARNs of the per-data-class KMS keys."
  value = {
    rds     = module.kms_rds.key_arn
    s3      = module.kms_s3.key_arn
    secrets = module.kms_secrets.key_arn
  }
}
