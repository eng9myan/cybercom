provider "aws" {
  region = "us-east-1"
}

# AWS Security Group configuration for secure B2B access
resource "aws_security_group" "cycom_sg" {
  name        = "cycom-erp-security-group"
  description = "Allow inbound SSH, web, and micro-kernel API traffic"

  ingress {
    description = "SSH Access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restrict to corporate CIDR in production
  }

  ingress {
    description = "Next.js Web Frontend"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "FastAPI Micro-Kernel"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "CycomSecurityGroup"
  }
}

# Provision AWS EC2 Instance running standard Ubuntu
resource "aws_instance" "cycom_server" {
  ami           = "ami-0c7217cdde317cfec" # Standard Ubuntu 22.04 LTS AMI in us-east-1
  instance_type = "t3.medium"
  key_name      = "cycom-deploy-key"

  vpc_security_group_ids = [aws_security_group.cycom_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update -y
              sudo apt-get install -y docker.io docker-compose git
              sudo systemctl start docker
              sudo systemctl enable docker
              EOF

  tags = {
    Name = "Cycom-ERP-Autonomous-Host"
  }
}

output "server_public_ip" {
  description = "Public IP Address of the EC2 Server"
  value       = aws_instance.cycom_server.public_ip
}
