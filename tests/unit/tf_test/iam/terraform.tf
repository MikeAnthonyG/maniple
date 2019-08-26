terraform {
  backend "s3" {
    bucket  = "project-tf-state-files"
    key     = "maniple/iam/terraform.tfstate"
    region  = "us-east-1"
    encrypt = "true"
  }
}
