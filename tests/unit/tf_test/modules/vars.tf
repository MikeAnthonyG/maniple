variable "function_method_name" {
    description = "A unique name for you Lambda Function."
    type        = "string"
}

variable "handler_function" {
    description = "The function entrypoint in your code. (ie the name of the handler in your code) "
    type        = "string"
}

variable "program_runtime" {
    description = "The runtime environment of your function eg. python3.6 or nodejs8.10"
    type        = "string"
}


variable "timeout_in_seconds" {
    description = "The amount of time your Lambda Function has to run in seconds. Defaults to 3."
    type        = "string"
}

variable "arn_role" {
    description = "IAM role attached to the lambda function."
    type        = "string"
}

variable "key" {
  description = "S3 key"
  type = "string"
}
