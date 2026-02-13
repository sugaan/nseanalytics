from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/opt/airflow')

from src.scraper import BSEScraper
from src.storage import Storage

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 2, 12),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'bse_announcements_pipeline',
    default_args=default_args,
    description='Fetch BSE announcements every 5 minutes',
    schedule_interval='*/5 * * * *',
    catchup=False,
    tags=['bse', 'announcements', 'scraping'],
)

def fetch_announcements(**context):
    """Fetch latest announcements from BSE"""
    scraper = BSEScraper()
    storage = Storage()
    
    announcements = scraper.fetch_announcements()
    
    if announcements:
        # Bulk add announcements
        total, new_count = storage.bulk_add_announcements(announcements)
        
        context['ti'].xcom_push(key='new_announcements', value=new_count)
        context['ti'].xcom_push(key='total_fetched', value=total)
        
        print(f"Fetched {total} announcements, {new_count} new")
    else:
        context['ti'].xcom_push(key='new_announcements', value=0)
        print("No announcements fetched")

def check_new_data(**context):
    """Branch based on whether new data was found"""
    ti = context['ti']
    new_count = ti.xcom_pull(task_ids='fetch_announcements', key='new_announcements')
    
    if new_count and new_count > 0:
        return 'process_announcements'
    else:
        return 'generate_statistics'

def process_announcements(**context):
    """Process new announcements"""
    storage = Storage()
    
    # Get recent announcements (last 100)
    recent = storage.get_announcements(limit=100)
    
    print(f"Processing {len(recent)} recent announcements")
    
    # Count by category
    categories = {}
    for ann in recent:
        cat = ann.category or 'Unknown'
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"Categories: {categories}")
    
    # Count by symbol
    symbols = {}
    for ann in recent:
        sym = ann.symbol or 'Unknown'
        symbols[sym] = symbols.get(sym, 0) + 1
    
    top_companies = sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"Top 10 companies: {top_companies}")

def generate_statistics(**context):
    """Generate statistics from all announcements"""
    storage = Storage()
    stats = storage.get_statistics()
    
    print(f"=== Database Statistics ===")
    print(f"Total announcements: {stats.get('total_announcements', 0)}")
    print(f"Unique companies: {stats.get('unique_symbols', 0)}")
    print(f"Latest announcement: {stats.get('latest_announcement', 'N/A')}")
    print(f"Oldest announcement: {stats.get('oldest_announcement', 'N/A')}")

# Define tasks
fetch_task = PythonOperator(
    task_id='fetch_announcements',
    python_callable=fetch_announcements,
    dag=dag,
)

check_task = BranchPythonOperator(
    task_id='check_new_data',
    python_callable=check_new_data,
    dag=dag,
)

process_task = PythonOperator(
    task_id='process_announcements',
    python_callable=process_announcements,
    dag=dag,
)

stats_task = PythonOperator(
    task_id='generate_statistics',
    python_callable=generate_statistics,
    dag=dag,
)

end_task = EmptyOperator(
    task_id='end',
    trigger_rule='none_failed_min_one_success',
    dag=dag,
)

# Set task dependencies
fetch_task >> check_task >> [process_task, stats_task] >> end_task
