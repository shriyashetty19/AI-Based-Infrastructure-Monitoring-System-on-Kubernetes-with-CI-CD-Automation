variable "aws_region" {
  description = "AWS region for cluster deployment"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the AWS EKS Cluster"
  type        = string
  default     = "ai-monitoring-eks-cluster"
}

variable "environment" {
  description = "Deployment environment tag"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "node_group_desired_capacity" {
  description = "Desired number of worker nodes"
  type        = int
  default     = 2
}

variable "node_group_instance_types" {
  description = "EC2 instance types for EKS worker nodes"
  type        = list(string)
  default     = ["t3.medium"]
}
