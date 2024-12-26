import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from tqdm import trange
from collections import Counter
import re

# Список технологий для анализа
technologies = [
    'Python', 'SQL', 'Java', 'Scala', 'Bash', 'Git', 'Docker', 'Kubernetes',
    'Apache Airflow', 'Luigi', 'ETL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Cassandra',
    'Redis', 'DynamoDB', 'Amazon Redshift', 'Snowflake', 'Google BigQuery',
    'Teradata', 'Apache Hadoop', 'Apache Spark', 'Apache Kafka', 'Hive', 'Flink',
    'Hadoop', 'Spark', 'Kafka', 'Hive', 'Flink', 'Dask', 'Delta Lake', 'Presto',
    'Trino', 'ElasticSearch', 'AWS', 'S3', 'Redshift', 'Glue', 'Lambda',
    'Google Cloud Platform', 'BigQuery', 'DataFlow', 'Pub/Sub', 'Microsoft Azure',
    'Data Factory', 'Synapse Analytics', 'Blob Storage', 'Tableau', 'Power BI',
    'Looker', 'QlikView', 'Grafana', 'Superset', 'Domo', 'Excel', 'Power Query',
    'Power Pivot', 'Google Analytics', 'Google Sheets', 'A/B тестирование','Selenium','JUnit','pytest','TestNG','Cypress','Appium',
    'Postman','SoapUI','LoadRunner','Gatling','TensorFlow','PyTorch','Scikit-learn','Keras','Hugging', 'Face','OpenAI','APIs','ChatGPT','GPT',
    'MLflow','H2O.ai','LightGBM','XGBoost','Tableau','Power BI','Looker','Grafana','Superse','QlikView','Qlik','Domo','Matplotlib','Seaborn',
    'Plotly','Docker','Kubernetes','Jenkins','GitLab','CI/CD','Ansible','Terraform','Puppet','Chef','Helm','OpenShift','AWS','Azure','Cloud','Amazon',
    'IBM Cloud','Oracle Cloud','Alibaba Cloud','DigitalOcean','Heroku','Vercel','Linode','MySQL','DynamoDB','Oracle Database','MariaDB','Neo4j','HTML',
    'CSS','Node.js','PHP','React','Angular','Vue.js','SASS/SCSS','jQuery','Django','Flask','Fast','JavaScript','C#','TypeScript','Swift','Kotlin','Go'
    ,'Golang','Rust','Scala','R','Dart','Perl',' Objective-C','Visual Basic','Shell (Bash)','Groovy'
]

# Функция для получения страницы вакансий
def getPages(page=0, vacancy=None, date_from=None, date_to=None):
    """Функция для получения страницы вакансий."""
    url = "https://api.hh.ru/vacancies"
    params = {
        'text': vacancy,
        'per_page': 100,
        'page': page,
        'date_from': date_from,
        'date_to': date_to
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None

# Функция для обработки вакансий
def process_vacancies(data):
    """Обрабатывает вакансии и возвращает DataFrame."""
    return pd.DataFrame([
        {
            'name': item.get('name'),
            'area': item.get('area', {}).get('name'),
            'employer': item.get('employer', {}).get('name'),
            'published_at': item.get('published_at'),
            'requirement': item.get('snippet', {}).get('requirement', ''),
            'url': item.get('alternate_url')
        }
        for item in data
    ])

# Функция для анализа технологий
def analyze_technologies(requirements_list, technologies):
    """Анализ технологий в требованиях вакансий."""
    text_data = ' '.join(requirements_list).lower()
    text_data = re.sub(r'[^\w\s]', '', text_data)  # Убираем пунктуацию
    words = text_data.split()
    word_count = Counter(words)

    # Считаем частоту технологий
    tech_count = {tech.lower(): word_count.get(tech.lower(), 0) for tech in technologies}
    # Сортируем технологии по убыванию упоминаний
    sorted_tech = sorted(tech_count.items(), key=lambda x: x[1], reverse=True)
    return sorted_tech

# Основной парсинг
def parse_vacancies(vacancy, technologies, days=30):
    """Парсинг вакансий за последний месяц."""
    df = pd.DataFrame()
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    print(f"Парсинг вакансий '{vacancy}' с {start_date} по {end_date}...")

    for page in trange(0, 20):  # Ограничение: 20 страниц
        data = getPages(page=page, vacancy=vacancy, date_from=start_date, date_to=end_date)
        if data is None or not data.get('items'):
            break

        df_temp = process_vacancies(data['items'])
        df = pd.concat([df, df_temp], ignore_index=True)

    # Удаляем дубликаты вакансий
    df = df.drop_duplicates(subset=['name', 'employer'])

    # Подсчёт вакансий
    total_vacancies = len(df)
    print(f"Всего уникальных вакансий: {total_vacancies}")

    # Анализ технологий
    if 'requirement' in df.columns:
        requirements_list = df['requirement'].dropna().tolist()
        tech_summary = analyze_technologies(requirements_list, technologies)
    else:
        tech_summary = []

    # Вывод анализа
    print("\nТоп-10 технологий по убыванию упоминаний:")
    for tech, count in tech_summary[:10]:  # Ограничиваем вывод до топ-10
        print(f"{tech}: {count} упоминаний")

    return df, tech_summary[:10]  # Возвращаем только топ-10


# Запуск
if __name__ == "__main__":
    vacancy_name = input("Введите название вакансии: ")
    df, tech_summary = parse_vacancies(vacancy_name, technologies, days=30)