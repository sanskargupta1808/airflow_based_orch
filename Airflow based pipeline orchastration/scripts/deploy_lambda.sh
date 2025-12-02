#!/bin/bash

cd ../lambda

# Create deployment package
mkdir -p package
pip3 install -r requirements.txt -t package/
cp transform_function.py package/

cd package
zip -r ../lambda_function.zip .
cd ..

# Deploy to AWS
aws lambda create-function \
    --function-name etl-transform-function \
    --runtime python3.11 \
    --role arn:aws:iam::ACCOUNT_ID:role/etl-lambda-role \
    --handler transform_function.lambda_handler \
    --zip-file fileb://lambda_function.zip \
    --timeout 300 \
    --memory-size 512

echo "Lambda function deployed!"
