# Airflow-Based ETL Pipeline Orchestration

Automated, reliable, and event-driven ETL workflow management system using Apache Airflow.

## Architecture

```
S3 (Raw Data) → S3KeySensorAsync → Airflow DAG → Lambda Transform → Redshift → Output
                     ↓                    ↓              ↓
                Event-driven         XComs Pass      Monitoring
                No Polling          Task Data        & Logging
```

## Components

### 1. Apache Airflow
- **Orchestration**: Manages entire ETL workflow
- **Event-driven**: S3KeySensorAsync for file detection
- **Fault Tolerance**: Retry policies, dependencies, logging

### 2. AWS Services
- **S3**: Raw and processed data storage
- **Lambda**: Data transformation and processing
- **Redshift**: Data warehouse for analytics
- **CloudWatch**: Monitoring and alerting

### 3. Key Features
- ✅ Modular DAG design
- ✅ S3KeySensorAsync (no polling overhead)
- ✅ XComs for inter-task communication
- ✅ Retry policies with exponential backoff
- ✅ Task dependencies and groups
- ✅ Comprehensive logging
- ✅ Automated monitoring

## DAGs Included

### 1. `etl_pipeline_dag.py`
Main ETL pipeline with S3 → Redshift → Lambda flow

### 2. `modular_etl_dag.py`
Modular design with TaskGroups for better organization

### 3. `fault_tolerant_dag.py`
Advanced retry logic, email notifications, cleanup tasks

### 4. `monitoring_dag.py`
Pipeline health checks and data freshness monitoring

## Setup

### Prerequisites
```bash
# Install Airflow
pip3 install -r requirements.txt

# Configure AWS
aws configure
```

### 1. Initialize Airflow
```bash
cd scripts
chmod +x setup_airflow.sh
./setup_airflow.sh
```

### 2. Deploy Lambda Function
```bash
chmod +x deploy_lambda.sh
./deploy_lambda.sh
```

### 3. Deploy Infrastructure
```bash
cd config
terraform init
terraform apply
```

### 4. Start Airflow
```bash
# Terminal 1 - Scheduler
airflow scheduler

# Terminal 2 - Webserver
airflow webserver -p 8080
```

### 5. Access Airflow UI
```
http://localhost:8080
Username: admin
Password: admin
```

## DAG Configuration

### S3KeySensorAsync
```python
wait_for_file = S3KeySensorAsync(
    task_id='wait_for_file',
    bucket_name='raw-data-bucket',
    bucket_key='incoming/data_*.csv',
    wildcard_match=True,
    timeout=3600,
    poke_interval=60,
)
```

### XComs Usage
```python
# Push data
ti.xcom_push(key='file_path', value=s3_key)

# Pull data
file_path = ti.xcom_pull(task_ids='process_metadata', key='file_path')
```

### Retry Configuration
```python
default_args = {
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
}
```

## Task Dependencies

```python
# Linear
task1 >> task2 >> task3

# Parallel
task1 >> [task2, task3] >> task4

# Conditional
task1 >> task2
[task1, task2] >> cleanup_task  # Runs if any fails
```

## Monitoring

### CloudWatch Metrics
- Pipeline success/failure rates
- Task execution times
- Data processing volumes

### Airflow UI
- DAG run history
- Task logs
- Gantt charts
- Task duration

### Email Alerts
```python
EmailOperator(
    task_id='send_alert',
    to='team@company.com',
    subject='Pipeline Alert',
    trigger_rule=TriggerRule.ONE_FAILED,
)
```

## Performance Optimizations

1. **S3KeySensorAsync**: Non-blocking sensor (no worker slots wasted)
2. **Task Groups**: Better organization and parallel execution
3. **XComs**: Efficient data passing between tasks
4. **Retry Policies**: Automatic recovery from transient failures
5. **Execution Timeout**: Prevents hanging tasks

## Project Structure

```
Airflow based pipeline orchastration/
├── dags/
│   ├── etl_pipeline_dag.py
│   ├── modular_etl_dag.py
│   ├── fault_tolerant_dag.py
│   └── monitoring_dag.py
├── lambda/
│   ├── transform_function.py
│   └── requirements.txt
├── plugins/
│   └── etl_monitoring_plugin.py
├── config/
│   ├── airflow.cfg
│   └── terraform.tf
├── scripts/
│   ├── setup_airflow.sh
│   └── deploy_lambda.sh
└── README.md
```

## Key Achievements

✅ **Fully Automated**: No manual intervention required
✅ **Event-Driven**: S3KeySensorAsync triggers on file arrival
✅ **Fault Tolerant**: Retry policies, dependencies, cleanup tasks
✅ **Modular Design**: Reusable task groups and components
✅ **Comprehensive Logging**: Full audit trail of all operations
✅ **Monitoring**: Real-time pipeline health checks
✅ **Optimized**: Reduced execution time and resource usage

## Troubleshooting

### Airflow not starting
```bash
# Reset database
airflow db reset

# Check logs
tail -f logs/scheduler/latest/*.log
```

### DAG not appearing
```bash
# Check DAG syntax
python3 dags/etl_pipeline_dag.py

# Refresh DAGs
airflow dags list-import-errors
```

### Task failing
```bash
# View task logs in UI
# Or check logs directory
cat logs/dag_id/task_id/execution_date/*.log
```

## Best Practices

- Use S3KeySensorAsync instead of S3KeySensor
- Implement retry policies for all tasks
- Use XComs for small data, S3 for large data
- Add email notifications for failures
- Monitor DAG execution times
- Use task groups for modularity
- Implement cleanup tasks with TriggerRule.ONE_FAILED
