resource "aws_lambda_function" "module_name" {
    function_name   = "${var.function_method_name}"
    role            = "${var.arn_role}"
    handler         = "${var.handler_function}" 
    runtime         = "${var.program_runtime}"
    timeout         = "${var.timeout_in_seconds}"
    s3_key          = "${var.key}"  
    s3_bucket       = "aws-lambda-project-code"
}
