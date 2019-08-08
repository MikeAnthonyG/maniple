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

module "module_mult_folder_file" {
    source                  = "../modules"
    function_method_name    = "module_mult_folder_file"
    handler_function        = "module_mult_folder_file.handler"
    program_runtime         = "python3.6"
    timeout_in_seconds      = "900"
    arn_role                = "${data.aws_iam_role.lambda_role.arn}"
    key                     = "maniple/test/${var.version}/module_mult_folder_file.zip"
}

module "module_mult_folder_dir" {
    source                  = "../modules"
    function_method_name    = "module_mult_folder_dir"
    handler_function        = "mod_two.handler"
    program_runtime         = "python3.6"
    timeout_in_seconds      = "900"
    arn_role                = "${data.aws_iam_role.lambda_role.arn}"
    key                     = "maniple/test/${var.version}/module_mult_folder_dir.zip"
}
