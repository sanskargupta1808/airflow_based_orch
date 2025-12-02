from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from datetime import datetime, timedelta
import boto3

default_args = {
    'owner': 'data-engineering',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

def check_pipeline_health(**context):
    cloudwatch = boto3.client('cloudwatch')
    
    response = cloudwatch.get_metric_statistics(
        Namespace='ETL/Pipeline',
        MetricName='pipeline.success',
        StartTime=datetime.utcnow() - timedelta(hours=24),
        EndTime=datetime.utcnow(),
        Period=3600,
        Statistics=['Sum']
    )
    
    success_count = sum([dp['Sum'] for dp in response['Datapoints']])
    print(f"Successful pipeline runs in last 24h: {success_count}")
    
    return {'success_count': success_count}

def check_s3_data_freshness(**context):
    s3_hook = S3Hook(aws_conn_id='aws_default')
    
    keys = s3_hook.list_keys(bucket_name='raw-data-bucket', prefix='incoming/')
    
    if not keys:
        print("Warning: No files in incoming bucket")
        return {'status': 'warning', 'file_count': 0}
    
    print(f"Files in incoming bucket: {len(keys)}")
    return {'status': 'ok', 'file_count': len(keys)}

def check_redshift_load(**context):
    redshift_data = boto3.client('redshift-data')
    
    response = redshift_data.execute_statement(
        ClusterIdentifier='etl-cluster',
        Database='analytics',
        Sql='SELECT COUNT(*) FROM raw_events WHERE created_at > NOW() - INTERVAL \'1 day\''
    )
    
    print(f"Query ID: {response['Id']}")
    return {'query_id': response['Id']}

with DAG(
    'pipeline_monitoring',
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval='@hourly',
    catchup=False,
    tags=['monitoring']
) as dag:

    health_check = PythonOperator(
        task_id='check_pipeline_health',
        python_callable=check_pipeline_health,
    )

    s3_check = PythonOperator(
        task_id='check_s3_freshness',
        python_callable=check_s3_data_freshness,
    )

    redshift_check = PythonOperator(
        task_id='check_redshift_load',
        python_callable=check_redshift_load,
    )

    [health_check, s3_check, redshift_check]
