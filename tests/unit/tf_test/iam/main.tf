resource "aws_iam_role" "maniple_test_lambda_role" {
    name = "maniple_test_lambda_role"
    assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement":[
        {
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Effect": "Allow"
        }
    ]
}
EOF
}

resource "aws_iam_policy" "maniple_test_policy" {
    name        = "maniple_test_policy"
    description = "List files from fake S3 bucket."
    policy      = "${file("policy.json")}"
}

resource "aws_iam_policy_attachment" "maniple_test_policy_attachment" {
    name    = "maniple_test_policy_attachment"
    roles    = ["${aws_iam_role.maniple_test_lambda_role.name}"]
    policy_arn = "${aws_iam_policy.maniple_test_policy.arn}"
}
