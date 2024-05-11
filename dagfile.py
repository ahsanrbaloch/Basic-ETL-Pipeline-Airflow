from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import csv
import os
import subprocess
def extract_data():
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

    # URLs for both BBC and Dawn
    bbc_url = 'https://www.bbc.com/'
    dawn_url = 'https://www.dawn.com/'

    # Extract links from both BBC and Dawn
    bbc_links = extract_links(bbc_url)
    dawn_links = extract_links(dawn_url)

    # Count total links
    total_links = len(bbc_links) + len(dawn_links)
    print("Total links:", total_links)

    # Initialize a list to store articles data
    articles_data = []

    # Extract articles data from BBC
    print("Extracting articles from BBC...")
    for index, link in enumerate(bbc_links, start=1):
        if link.startswith('https://www.bbc.com'):
            articles_data.extend(extract_articles(link))
            print(f"{index}/{total_links} links done from BBC.")

    # Extract articles data from Dawn
    print("Extracting articles from Dawn...")
    for index, link in enumerate(dawn_links, start=index):
        if link.startswith('https://www.dawn.com'):
            articles_data.extend(extract_articles(link))
            print(f"{index}/{total_links} links done from Dawn.")

    # Save the extracted data to a CSV file
    save_dir = "/home/ahsanrbaloch/A2/"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_to_csv(articles_data, os.path.join(save_dir, 'data.csv'))
    print("Data saved to data.csv")

def transform_data():
    # Function to read data from the CSV file and perform transformation
    save_dir = "/home/ahsanrbaloch/A2/"
    input_file_path = os.path.join(save_dir, 'data.csv')
    output_file_path = os.path.join(save_dir, 'transformed_data.csv')

    with open(input_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        transformed_data = []

        for row in reader:
            # Example transformation: Uppercase the titles
            row['Title'] = row['Title'].upper()
            transformed_data.append(row)

    # Save the transformed data to a new CSV file
    with open(output_file_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Title', 'Description']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transformed_data)

    print("Data transformed and saved to transformed_data.csv")

def load_data():
    save_dir = "/home/ahsanrbaloch/A2/"
    transformed_file_path = os.path.join(save_dir, 'transformed_data.csv')

    # Initialize DVC
    subprocess.run(['dvc', 'init'], cwd=save_dir)

    # Add the transformed data file to DVC
    subprocess.run(['dvc', 'add', transformed_file_path], cwd=save_dir)

    # Add Google Drive remote
    subprocess.run(['dvc', 'remote', 'add', 'gdrive', 'gdrive://1uKSuwWAjJUxzNFhkX1HF88HunkUtiCzk'], cwd=save_dir)

    # Set Google Drive remote as default
    subprocess.run(['dvc', 'remote', 'default', 'gdrive'], cwd=save_dir)

    # Push data to Google Drive
    subprocess.run(['dvc', 'push'], cwd=save_dir)

    # Add all files to the Git index
    subprocess.run(['git', 'add', '.'], cwd=save_dir)

    # Commit changes
    commit_message = "Update_data"  # You can customize the commit message as needed
    subprocess.run(['git', 'commit', '-m', commit_message], cwd=save_dir)

    # Push changes to GitHub
    subprocess.run(['git', 'push'], cwd=save_dir)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 11),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

dag = DAG(
    'extract_transform_load_data_dag',
    default_args=default_args,
    description='A DAG to extract and transform data from BBC and Dawn websites',
    schedule_interval=None,
)

# extract_data_task = PythonOperator(
#     task_id='extract_data',
#     python_callable=extract_data,
#     dag=dag,
# )

transform_data_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)
load_data_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=dag,
)

# Define task dependencies
transform_data_task >> load_data_task