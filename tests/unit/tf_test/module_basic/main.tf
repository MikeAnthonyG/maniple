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

module "module_basic" {
    source                  = "../modules/module_name"
    function_method_name    = "module_basic"
    handler_function        = "mod_basic.handler"
    program_runtime         = "python3.6"
    timeout_in_seconds      = "900"
    arn_role                = "{data.aws_iam_role.lambda_role.arn}"
    key                     = "maniple/test/${var.version}/module_basic.zip"
}
