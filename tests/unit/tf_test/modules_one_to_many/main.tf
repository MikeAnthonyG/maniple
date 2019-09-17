resource "aws_lambda_function" "module_name_one" {
    function_name   = "${var.function_method_name_one}"
    role            = "${var.arn_role}"
    handler         = "${var.function_method_name_one}" 
    runtime         = "python3.6"
    timeout         = 900
    s3_key          = "maniple/test/${var.function_method_name_one}.zip"
    s3_bucket       = "aws-lambda-project-code"
}

resource "aws_lambda_function" "module_name_two" {
    function_name   = "${var.function_method_name_two}"
    role            = "${var.arn_role}"
    handler         = "${var.function_method_name_two}.handler" 
    runtime         = "python3.6"
    timeout         = 900
    s3_key          = "maniple/test/${var.function_method_name_two}.zip"
    s3_bucket       = "aws-lambda-project-code"
}
