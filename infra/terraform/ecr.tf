resource "aws_ecr_repository" "demo_app" {
  name                 = "demo-service"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "demo-service-repo"
  }
}

resource "aws_ecr_repository" "ml_detector" {
  name                 = "ml-anomaly-detector"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "ml-anomaly-detector-repo"
  }
}
