provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "raw_data" {
  bucket = "raw-data-bucket"
}

resource "aws_s3_bucket" "processed_data" {
  bucket = "processed-data-bucket"
}

resource "aws_iam_role" "lambda_role" {
  name = "etl-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3_redshift" {
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.raw_data.arn}/*",
          "${aws_s3_bucket.processed_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "redshift-data:ExecuteStatement",
          "redshift-data:DescribeStatement"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "etl_transform" {
  filename      = "lambda_function.zip"
  function_name = "etl-transform-function"
  role          = aws_iam_role.lambda_role.arn
  handler       = "transform_function.lambda_handler"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = 512

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.raw_data.id
    }
  }
}

resource "aws_redshift_cluster" "etl_cluster" {
  cluster_identifier = "etl-cluster"
  database_name      = "analytics"
  master_username    = "admin"
  master_password    = "TempPassword123!"
  node_type          = "dc2.large"
  cluster_type       = "single-node"
  skip_final_snapshot = true
}

resource "aws_iam_role" "redshift_role" {
  name = "redshift-s3-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "redshift.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "redshift_s3_access" {
  role = aws_iam_role.redshift_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = [
        "${aws_s3_bucket.raw_data.arn}/*",
        "${aws_s3_bucket.processed_data.arn}/*"
      ]
    }]
  })
}
