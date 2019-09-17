terraform {
  backend "s3" {
    bucket  = "project-tf-state-files"
    key     = "maniple/one_module_many_resources/terraform.tfstate"
    region  = "us-east-1"
    encrypt = "true"
  }
}
