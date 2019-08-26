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

module "module_mult_one" {
    source                  = "../modules"
    function_method_name    = "module_mult_one"
    handler_function        = "module_mult_one.handler"
    program_runtime         = "python3.6"
    timeout_in_seconds      = "900"
    arn_role                = "${data.aws_iam_role.lambda_role.arn}"
    key                     = "maniple/test/${var.version}/module_mult_one.zip"
}

module "module_mult_two" {
    source                  = "../modules"
    function_method_name    = "module_mult_two"
    handler_function        = "mod_two.handler"
    program_runtime         = "python3.6"
    timeout_in_seconds      = "900"
    arn_role                = "${data.aws_iam_role.lambda_role.arn}"
    key                     = "maniple/test/${var.version}/module_mult_two.zip"
}
