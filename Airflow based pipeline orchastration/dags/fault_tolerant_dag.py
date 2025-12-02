from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensorAsync
from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email': ['data-team@company.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
}

def process_with_logging(**context):
    import logging
    logger = logging.getLogger(__name__)
    
    ti = context['ti']
    dag_run = context['dag_run']
    
    logger.info(f"Processing DAG run: {dag_run.run_id}")
    logger.info(f"Execution date: {context['execution_date']}")
    
    try:
        data = ti.xcom_pull(task_ids='wait_for_data')
        logger.info(f"Retrieved data: {data}")
        ti.xcom_push(key='processed_data', value={'status': 'success', 'records': 1000})
        return 'success'
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise

def cleanup_on_failure(**context):
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Pipeline failed, running cleanup...")
    return 'cleanup_complete'

with DAG(
    'fault_tolerant_etl_pipeline',
    default_args=default_args,
    description='ETL pipeline with advanced fault tolerance',
    schedule_interval='0 */6 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['etl', 'fault-tolerant']
) as dag:

    wait_for_data = S3KeySensorAsync(
        task_id='wait_for_data',
        bucket_name='raw-data-bucket',
        bucket_key='incoming/batch_*.csv',
        wildcard_match=True,
        aws_conn_id='aws_default',
        timeout=7200,
        poke_interval=300,
    )

    process_data = PythonOperator(
        task_id='process_data',
        python_callable=process_with_logging,
        provide_context=True,
    )

    transform_lambda = LambdaInvokeFunctionOperator(
        task_id='transform_lambda',
        function_name='etl-transform-function',
        aws_conn_id='aws_default',
        retries=5,
    )

    send_success_email = EmailOperator(
        task_id='send_success_email',
        to='data-team@company.com',
        subject='ETL Pipeline Success - {{ ds }}',
        html_content='Pipeline completed successfully for {{ ds }}',
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    cleanup_task = PythonOperator(
        task_id='cleanup_on_failure',
        python_callable=cleanup_on_failure,
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    wait_for_data >> process_data >> transform_lambda >> send_success_email
    [process_data, transform_lambda] >> cleanup_task
