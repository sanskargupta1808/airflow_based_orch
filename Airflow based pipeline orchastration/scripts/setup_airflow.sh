#!/bin/bash

export AIRFLOW_HOME='/Users/sanskargupta/Desktop/work/ARK_Infosoft/Airflow based pipeline orchastration'

echo "Setting up Airflow..."

# Install Airflow
pip3 install "apache-airflow[amazon,async,postgres]==2.8.0" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.0/constraints-3.11.txt"

# Initialize database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin

echo "Airflow setup complete!"
echo "Start scheduler: airflow scheduler"
echo "Start webserver: airflow webserver -p 8080"
