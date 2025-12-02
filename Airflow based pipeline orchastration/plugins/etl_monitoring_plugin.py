from airflow.plugins_manager import AirflowPlugin
from airflow.hooks.base import BaseHook
import boto3

class ETLMonitoringHook(BaseHook):
    def __init__(self, aws_conn_id='aws_default'):
        self.aws_conn_id = aws_conn_id
        self.cloudwatch = boto3.client('cloudwatch')
    
    def send_metric(self, metric_name, value, unit='Count'):
        self.cloudwatch.put_metric_data(
            Namespace='ETL/Pipeline',
            MetricData=[{
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }]
        )
    
    def log_pipeline_success(self, dag_id, task_id):
        self.send_metric(f'{dag_id}.{task_id}.success', 1)
    
    def log_pipeline_failure(self, dag_id, task_id):
        self.send_metric(f'{dag_id}.{task_id}.failure', 1)

class ETLMonitoringPlugin(AirflowPlugin):
    name = "etl_monitoring_plugin"
    hooks = [ETLMonitoringHook]
