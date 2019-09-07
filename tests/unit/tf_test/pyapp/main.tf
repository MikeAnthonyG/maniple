
provider "aws" {
  region = "us-east-1"
}


data "aws_iam_role" "app_role" {
  name = "app_role"
}

variable "version" {
  type = "string"
  default = "1.0.0"
}


resource "aws_lambda_function" "app" {
  description = "<<description>>"
  function_name = "app"
  s3_bucket = "<<s3-bucket-name>>"
  s3_key = "<<s3-key-name>>"
  role = "${data.aws_iam_role.app_role.arn}"
  handler = "app.handler"
  runtime = "python3.6"
  timeout = 1
  memory_size = 128
}
