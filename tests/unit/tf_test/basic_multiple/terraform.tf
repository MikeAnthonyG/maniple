terraform {
  backend "s3" {
    bucket  = "project-tf-state-files"
    key     = "maniple/basic_multiple/terraform.tfstate"
    region  = "us-east-1"
    encrypt = "true"
  }
}
