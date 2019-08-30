provider "aws" {
  region = "us-east-1"
}

data "aws_iam_role" "lambda_role" {
  name = "maniple_test_lambda_role"
}

variable "version" {
    type = "string"
    default = "1.0.0"
}

resource "aws_s3_bucket" "maniple-test-bucket" {
    bucket = "maniple-test-bucket"
    acl = "private"
    region = "us-east-1"
}

module "mod_basic" {
    source                  = "../modules"
    function_method_name    = "mod_basic"
    handler_function        = "mod_basic.handler"
    program_runtime         = "python3.6"
    timeout_in_seconds      = "900"
    arn_role                = "${data.aws_iam_role.lambda_role.arn}"
    key                     = "maniple/test/${var.version}/mod_basic2.zip"
}
