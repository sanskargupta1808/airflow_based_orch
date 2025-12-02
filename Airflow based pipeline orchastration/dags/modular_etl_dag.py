from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensorAsync
from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-engineering',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

def extract_data(**context):
    ti = context['ti']
    s3_key = ti.xcom_pull(task_ids='ingestion.sensor_s3_file')
    ti.xcom_push(key='extracted_key', value=s3_key)
    return {'status': 'extracted', 'records': 1000}

def transform_data(**context):
    ti = context['ti']
    extracted = ti.xcom_pull(task_ids='processing.extract')
    ti.xcom_push(key='transformed_records', value=extracted['records'])
    return {'status': 'transformed', 'records': extracted['records']}

def load_data(**context):
    ti = context['ti']
    transformed = ti.xcom_pull(task_ids='processing.transform')
    print(f"Loading {transformed['records']} records")
    return {'status': 'loaded', 'records': transformed['records']}

with DAG(
    'modular_etl_pipeline',
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval='@hourly',
    catchup=False,
    tags=['etl', 'modular']
) as dag:

    with TaskGroup('ingestion') as ingestion:
        sensor_s3_file = S3KeySensorAsync(
            task_id='sensor_s3_file',
            bucket_name='raw-data-bucket',
            bucket_key='incoming/*.csv',
            wildcard_match=True,
            aws_conn_id='aws_default',
        )

    with TaskGroup('processing') as processing:
        extract = PythonOperator(
            task_id='extract',
            python_callable=extract_data,
        )

        transform = PythonOperator(
            task_id='transform',
            python_callable=transform_data,
        )

        load = PythonOperator(
            task_id='load',
            python_callable=load_data,
        )

        extract >> transform >> load

    with TaskGroup('post_processing') as post_processing:
        trigger_lambda = LambdaInvokeFunctionOperator(
            task_id='trigger_analytics',
            function_name='post-etl-analytics',
            aws_conn_id='aws_default',
        )

    ingestion >> processing >> post_processing
