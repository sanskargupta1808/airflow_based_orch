from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensorAsync
from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import json

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def process_metadata(**context):
    ti = context['ti']
    s3_key = ti.xcom_pull(task_ids='wait_for_file')
    print(f"Processing file: {s3_key}")
    ti.xcom_push(key='file_path', value=s3_key)
    return s3_key

def validate_load(**context):
    ti = context['ti']
    lambda_response = ti.xcom_pull(task_ids='transform_data')
    print(f"Validation result: {lambda_response}")
    return "success"

with DAG(
    'etl_s3_redshift_pipeline',
    default_args=default_args,
    description='Automated ETL pipeline with event-driven processing',
    schedule_interval='@daily',
    catchup=False,
    tags=['etl', 'production']
) as dag:

    wait_for_file = S3KeySensorAsync(
        task_id='wait_for_file',
        bucket_name='raw-data-bucket',
        bucket_key='incoming/data_*.csv',
        wildcard_match=True,
        aws_conn_id='aws_default',
        timeout=3600,
        poke_interval=60,
    )

    process_file_metadata = PythonOperator(
        task_id='process_metadata',
        python_callable=process_metadata,
        provide_context=True,
    )

    load_to_redshift = S3ToRedshiftOperator(
        task_id='load_to_redshift',
        s3_bucket='raw-data-bucket',
        s3_key='incoming/{{ ti.xcom_pull(task_ids="process_metadata", key="file_path") }}',
        schema='public',
        table='raw_events',
        copy_options=['csv', 'IGNOREHEADER 1'],
        redshift_conn_id='redshift_default',
        aws_conn_id='aws_default',
    )

    transform_data = LambdaInvokeFunctionOperator(
        task_id='transform_data',
        function_name='etl-transform-function',
        payload=json.dumps({
            'bucket': 'raw-data-bucket',
            'key': '{{ ti.xcom_pull(task_ids="process_metadata", key="file_path") }}'
        }),
        aws_conn_id='aws_default',
    )

    validate_pipeline = PythonOperator(
        task_id='validate_load',
        python_callable=validate_load,
        provide_context=True,
    )

    wait_for_file >> process_file_metadata >> load_to_redshift >> transform_data >> validate_pipeline
