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

module "module_one_to_many" {
  source = "../modules_one_to_many"
  function_method_name_one = "fn_one"
  function_method_name_two = "fn_two"
  arn_role = "${data.aws_iam_role.lambda_role.arn}"  
}
