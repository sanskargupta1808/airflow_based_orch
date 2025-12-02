import json
import boto3
import pandas as pd
from io import StringIO

s3 = boto3.client('s3')
redshift_data = boto3.client('redshift-data')

def lambda_handler(event, context):
    bucket = event['bucket']
    key = event['key']
    
    # Read from S3
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))
    
    # Transform
    df['processed_at'] = pd.Timestamp.now()
    df['record_count'] = len(df)
    df = df.dropna()
    
    # Write transformed data
    output_key = key.replace('incoming/', 'processed/')
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    s3.put_object(
        Bucket=bucket,
        Key=output_key,
        Body=csv_buffer.getvalue()
    )
    
    # Execute Redshift query
    response = redshift_data.execute_statement(
        ClusterIdentifier='etl-cluster',
        Database='analytics',
        Sql=f"COPY processed_events FROM 's3://{bucket}/{output_key}' IAM_ROLE 'arn:aws:iam::ACCOUNT:role/RedshiftRole' CSV IGNOREHEADER 1;"
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'records_processed': len(df),
            'output_key': output_key,
            'query_id': response['Id']
        })
    }
