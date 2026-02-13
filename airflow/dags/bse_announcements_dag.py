from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, '/opt/airflow')
sys.path.insert(0, '/opt/airflow/src')

from src.orchestrator import NSEAnnouncementOrchestrator
from src.storage import Storage
from src.downloader import AttachmentDownloader
from loguru import logger


default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}


def fetch_bse_announcements(**context):
    """Fetch BSE announcements and store in database."""
    logger.info("Starting BSE announcements fetch")
    
    orchestrator = NSEAnnouncementOrchestrator(source='bse')
    results = orchestrator.fetch_and_store(download_attachments=False)
    
    context['ti'].xcom_push(key='fetch_results', value=results)
    
    logger.info(f"Fetch completed: {results}")
    print(f"✅ Fetched {results['total_new']} new announcements")
    
    return results


def check_new_announcements(**context):
    """Check if there are new announcements to process."""
    ti = context['ti']
    fetch_results = ti.xcom_pull(task_ids='fetch_announcements', key='fetch_results')
    
    if fetch_results and fetch_results.get('total_new', 0) > 0:
        print(f"📊 Found {fetch_results['total_new']} new announcements")
        return 'generate_statistics'
    else:
        print("ℹ️ No new announcements")
        return 'skip_process'


def generate_statistics(**context):
    """Generate and log database statistics."""
    storage = Storage()
    stats = storage.get_statistics()
    
    ti = context['ti']
    fetch_results = ti.xcom_pull(task_ids='fetch_announcements', key='fetch_results')
    
    print("\n" + "=" * 60)
    print("📈 DATABASE STATISTICS")
    print("=" * 60)
    print(f"Total Announcements: {stats['total_announcements']}")
    print(f"Unique Companies: {stats['unique_symbols']}")
    print(f"Latest Announcement: {stats['latest_announcement']}")
    
    if fetch_results:
        print(f"\n🔄 New: {fetch_results.get('total_new', 0)}")
    print("=" * 60 + "\n")
    
    return stats


# Define the DAG
with DAG(
    dag_id='bse_announcements_pipeline',
    default_args=default_args,
    description='Fetch and process BSE corporate announcements',
    schedule_interval='0 9,14,18 * * *',  # 9 AM, 2 PM, 6 PM IST
    start_date=days_ago(1),
    catchup=False,
    tags=['bse', 'announcements', 'production'],
    max_active_runs=1,
) as dag:
    
    task_fetch = PythonOperator(
        task_id='fetch_announcements',
        python_callable=fetch_bse_announcements,
    )
    
    task_check = BranchPythonOperator(
        task_id='check_new_data',
        python_callable=check_new_announcements,
    )
    
    task_skip = EmptyOperator(
        task_id='skip_process',
    )
    
    task_stats = PythonOperator(
        task_id='generate_statistics',
        python_callable=generate_statistics,
    )
    
    # Define dependencies
    task_fetch >> task_check >> [task_stats, task_skip]
