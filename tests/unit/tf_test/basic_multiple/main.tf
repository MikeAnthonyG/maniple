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

resource "aws_lambda_function" "fn_one" {
    function_name = "fn_one"
    s3_bucket = "aws-lambda-project-code"
    s3_key = "maniple/test/${var.version}/fn_one.zip"
    role = "${data.aws_iam_role.lambda_role.arn}"
    handler = "fn_one.handler"
    runtime = "python3.6"
    timeout = 1
    memory_size = 128    
}

resource "aws_lambda_function" "fn_two" {
    function_name = "fn_two"
    s3_bucket = "aws-lambda-project-code"
    s3_key = "maniple/test/${var.version}/fn_two.zip"
    role = "${data.aws_iam_role.lambda_role.arn}"
    handler = "fn_two.handler"
    runtime = "python3.6"
    timeout = 1
    memory_size = 128    
}
