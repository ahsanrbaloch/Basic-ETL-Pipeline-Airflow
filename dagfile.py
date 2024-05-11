from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import csv
import os
save_dir = r"C:/Users/hp/Desktop"
# Define your functions here
def extract_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = [link.get('href') for link in soup.find_all('a', href=True)]
    return links

def extract_articles(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []
    for article in soup.find_all('article'):
        title = article.find('h2')
        description = article.find('p')
        if title and description:
            articles.append({
                'title': title.text.strip(),
                'description': description.text.strip()
            })
    return articles

def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'Description'])
        for article in data:
            writer.writerow([article['title'], article['description']])

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 5, 10),
    'retries': 1,
}

# Define the DAG
with DAG('data_extraction_dag', default_args=default_args, schedule_interval='@daily') as dag:
    
    # Define the task to extract links
    extract_links_task = PythonOperator(
        task_id='extract_links',
        python_callable=extract_links,
        op_kwargs={'url': 'https://www.bbc.com/'}
    )
    
    # Define the task to extract articles
    extract_articles_task = PythonOperator(
        task_id='extract_articles',
        python_callable=extract_articles,
        op_kwargs={'url': 'https://www.bbc.com/'}
    )
    
    # Define the task to save data to CSV
   
   # Define the task to save data to CSV
    save_to_csv_task = PythonOperator(
    task_id='save_to_csv',
    python_callable=save_to_csv,
    op_kwargs={'data': '{{ task_instance.xcom_pull(task_ids="extract_articles") }}', 'filename': os.path.join(save_dir, 'data.csv')}
)


    # Set task dependencies
    extract_links_task >> extract_articles_task >> save_to_csv_task
