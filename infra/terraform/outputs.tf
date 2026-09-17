output "cluster_endpoint" {
  description = "Endpoint URL for EKS control plane"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_name" {
  description = "EKS Cluster Name"
  value       = aws_eks_cluster.main.name
}

output "ecr_demo_app_url" {
  description = "ECR Repository URL for demo app"
  value       = aws_ecr_repository.demo_app.repository_url
}

output "ecr_ml_detector_url" {
  description = "ECR Repository URL for ML detector"
  value       = aws_ecr_repository.ml_detector.repository_url
}
