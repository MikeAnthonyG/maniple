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

resource "aws_lambda_function" "basic" {
    function_name = "basic"
    s3_bucket = "aws-lambda-project-code"
    s3_key = "maniple/test/${var.version}/basic.zip"
    role = "${data.aws_iam_role.lambda_role.arn}"
    handler = "basic.handler"
    runtime = "python3.6"
    timeout = 1
    memory_size = 128
    environment {
      variables = {
        "foo" = "bar"
      }
    }
}
