terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Remote state — configure per environment (see README).
  # backend "s3" {
  #   bucket         = "cymed-tfstate-<account-id>"
  #   key            = "aws/<env>/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "cymed-tf-locks"
  #   encrypt        = true
  #   kms_key_id     = "alias/cymed-tfstate"
  # }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = var.tags
  }
}
