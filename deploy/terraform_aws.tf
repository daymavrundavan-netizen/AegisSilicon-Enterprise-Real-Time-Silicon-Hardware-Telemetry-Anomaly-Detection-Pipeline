# ====================================================================
# AegisSilicon Infrastructure as Code (Terraform for AWS EC2 & S3)
# ====================================================================

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "instance_type" {
  default = "t3.xlarge"
}

# 1. Amazon S3 Archive Bucket
resource "aws_s3_bucket" "telemetry_bucket" {
  bucket        = "aegissilicon-telemetry-archive"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "telemetry_versioning" {
  bucket = aws_s3_bucket.telemetry_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 2. AWS Security Group
resource "aws_security_group" "aegis_sg" {
  name        = "aegis_silicon_sg"
  description = "Security group for AegisSilicon real-time telemetry stack"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "React Dashboard UI"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "FastAPI REST & WebSocket API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Streamlit Dashboard UI"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Apache Kafka Ingestion Bus"
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3. AWS EC2 Instance
resource "aws_instance" "aegis_node" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS AMI in us-east-1
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.aegis_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y docker.io docker-compose-v2 git
              systemctl enable docker
              systemctl start docker
              EOF

  tags = {
    Name = "AegisSilicon-SDC-Node"
  }
}

output "ec2_public_ip" {
  value = aws_instance.aegis_node.public_ip
}

output "s3_bucket_name" {
  value = aws_s3_bucket.telemetry_bucket.id
}
