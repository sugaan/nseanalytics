from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago


def test_imports():
    """Test if all project imports work."""
    print("Testing imports...")
    
    try:
        from src.storage import Storage
        print("✅ Storage imported")
        
        storage = Storage()
        stats = storage.get_statistics()
        print(f"✅ Database connected: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        raise


with DAG(
    dag_id='test_project_setup',
    description='Test NSE/BSE project configuration',
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    tags=['test'],
) as dag:
    
    test_task = PythonOperator(
        task_id='test_imports_and_db',
        python_callable=test_imports,
    )
