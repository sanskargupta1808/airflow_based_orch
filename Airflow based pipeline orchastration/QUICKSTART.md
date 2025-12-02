# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
cd '/Users/sanskargupta/Desktop/work/ARK_Infosoft/Airflow based pipeline orchastration'
pip3 install -r requirements.txt
```

### Step 2: Initialize Airflow
```bash
export AIRFLOW_HOME=$(pwd)
airflow db init
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com
```

### Step 3: Start Airflow
```bash
# Terminal 1
airflow scheduler

# Terminal 2
airflow webserver -p 8080
```

### Step 4: Access UI
Open: http://localhost:8080
- Username: `admin`
- Password: `admin`

### Step 5: Enable DAGs
In the Airflow UI, toggle ON the DAGs:
- `etl_s3_redshift_pipeline`
- `modular_etl_pipeline`
- `fault_tolerant_etl_pipeline`
- `pipeline_monitoring`

## Test Locally (Without AWS)

### Create Test DAG
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def test_task():
    print("Pipeline working!")
    return "success"

with DAG('test_dag', start_date=datetime(2025, 1, 1), schedule_interval='@daily') as dag:
    test = PythonOperator(task_id='test', python_callable=test_task)
```

### Run Test
```bash
# Test DAG syntax
python3 dags/test_dag.py

# Run task manually
airflow tasks test test_dag test 2025-01-01
```

## Deploy to AWS

### 1. Configure AWS
```bash
aws configure
```

### 2. Deploy Infrastructure
```bash
cd config
terraform init
terraform apply
```

### 3. Deploy Lambda
```bash
cd scripts
./deploy_lambda.sh
```

### 4. Configure Airflow Connections

In Airflow UI → Admin → Connections:

**AWS Connection:**
- Conn Id: `aws_default`
- Conn Type: `Amazon Web Services`
- AWS Access Key ID: `YOUR_KEY`
- AWS Secret Access Key: `YOUR_SECRET`
- Region: `us-east-1`

**Redshift Connection:**
- Conn Id: `redshift_default`
- Conn Type: `Amazon Redshift`
- Host: `etl-cluster.XXXXX.us-east-1.redshift.amazonaws.com`
- Database: `analytics`
- Login: `admin`
- Password: `YOUR_PASSWORD`
- Port: `5439`

## Verify Everything Works

### 1. Check DAG Status
```bash
airflow dags list
```

### 2. Trigger DAG Manually
```bash
airflow dags trigger etl_s3_redshift_pipeline
```

### 3. Check Task Logs
```bash
airflow tasks logs etl_s3_redshift_pipeline wait_for_file 2025-01-01
```

### 4. Monitor in UI
- Go to http://localhost:8080
- Click on DAG name
- View Graph, Tree, or Gantt chart

## Common Commands

```bash
# List all DAGs
airflow dags list

# Trigger DAG
airflow dags trigger <dag_id>

# Pause/Unpause DAG
airflow dags pause <dag_id>
airflow dags unpause <dag_id>

# Test task
airflow tasks test <dag_id> <task_id> <execution_date>

# View logs
airflow tasks logs <dag_id> <task_id> <execution_date>

# Clear task state
airflow tasks clear <dag_id> -t <task_id>
```

## Troubleshooting

### DAG not showing up
```bash
# Check for import errors
airflow dags list-import-errors

# Verify DAG file syntax
python3 dags/your_dag.py
```

### Task stuck in "running"
```bash
# Clear task state
airflow tasks clear <dag_id> -t <task_id>
```

### Connection error
- Verify AWS credentials in Airflow UI
- Check IAM permissions
- Test connection: `aws s3 ls`

## Next Steps

1. ✅ Review DAG code in `dags/` directory
2. ✅ Customize for your use case
3. ✅ Set up email notifications
4. ✅ Configure CloudWatch monitoring
5. ✅ Deploy to production environment

## Production Checklist

- [ ] Use production database (PostgreSQL/MySQL)
- [ ] Set up executor (CeleryExecutor/KubernetesExecutor)
- [ ] Configure email alerts
- [ ] Set up monitoring and logging
- [ ] Implement secrets management
- [ ] Configure backups
- [ ] Set up CI/CD for DAG deployment
