# --- IAM Role for Lambdas ---
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem"]
        Resource = aws_dynamodb_table.tokens.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${aws_s3_bucket.data.arn}/*"
      }
    ]
  })
}

# --- Lambda: validate_token ---
data "archive_file" "validate_token" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/validate_token/handler.py"
  output_path = "${path.module}/.build/validate_token.zip"
}

resource "aws_lambda_function" "validate_token" {
  function_name    = "${var.project_name}-validate-token"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.validate_token.output_path
  source_code_hash = data.archive_file.validate_token.output_base64sha256

  environment {
    variables = {
      TOKENS_TABLE = aws_dynamodb_table.tokens.name
    }
  }
}

# --- Lambda: get_template ---
data "archive_file" "get_template" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/get_template/handler.py"
  output_path = "${path.module}/.build/get_template.zip"
}

resource "aws_lambda_function" "get_template" {
  function_name    = "${var.project_name}-get-template"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.get_template.output_path
  source_code_hash = data.archive_file.get_template.output_base64sha256

  environment {
    variables = {
      TOKENS_TABLE    = aws_dynamodb_table.tokens.name
      TEMPLATE_BUCKET = aws_s3_bucket.data.id
      TEMPLATE_KEY    = var.template_key
    }
  }
}

# --- Lambda: get_upload_url ---
data "archive_file" "get_upload_url" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/get_upload_url/handler.py"
  output_path = "${path.module}/.build/get_upload_url.zip"
}

resource "aws_lambda_function" "get_upload_url" {
  function_name    = "${var.project_name}-get-upload-url"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.get_upload_url.output_path
  source_code_hash = data.archive_file.get_upload_url.output_base64sha256

  environment {
    variables = {
      TOKENS_TABLE  = aws_dynamodb_table.tokens.name
      UPLOAD_BUCKET = aws_s3_bucket.data.id
    }
  }
}

# --- API Gateway HTTP API ---
resource "aws_apigatewayv2_api" "api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "OPTIONS"]
    allow_headers = ["Content-Type"]
    max_age       = 3600
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true
}

# --- Integrations ---
resource "aws_apigatewayv2_integration" "validate_token" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.validate_token.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "get_template" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.get_template.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "get_upload_url" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.get_upload_url.invoke_arn
  payload_format_version = "2.0"
}

# --- Routes ---
resource "aws_apigatewayv2_route" "validate" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /validate"
  target    = "integrations/${aws_apigatewayv2_integration.validate_token.id}"
}

resource "aws_apigatewayv2_route" "template" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /template"
  target    = "integrations/${aws_apigatewayv2_integration.get_template.id}"
}

resource "aws_apigatewayv2_route" "upload_url" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /upload-url"
  target    = "integrations/${aws_apigatewayv2_integration.get_upload_url.id}"
}

# --- Lambda Permissions for API Gateway ---
resource "aws_lambda_permission" "validate_token" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.validate_token.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "get_template" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_template.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "get_upload_url" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_upload_url.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# --- Outputs ---
output "api_endpoint" {
  value = aws_apigatewayv2_api.api.api_endpoint
}

output "data_bucket" {
  value = aws_s3_bucket.data.id
}
