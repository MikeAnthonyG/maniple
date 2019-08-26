terraform {
  backend "s3" {
    bucket  = "project-tf-state-files"
    key     = "maniple/basic_dir/terraform.tfstate"
    region  = "us-east-1"
    encrypt = "true"
  }
}
