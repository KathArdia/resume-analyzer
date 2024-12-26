# !pip install transformers
# !pip install pyspellchecker
# !pip install textblob
# !pip install python-docx PyPDF2 langdetect language-tool-python

import re
from typing import List, Dict
from spellchecker import SpellChecker
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import docx
import PyPDF2
from langdetect import detect
import language_tool_python
import json
from datetime import datetime
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from typing import List, Dict

from transformers import AutoTokenizer, AutoModelForCausalLM
import os
import json
import docx
from typing import List, Dict
from datetime import datetime
import re

# Функция для чтения текста из файла резюме
def read_resume_text(file_path: str) -> str:
    if file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file_path.endswith('.pdf'):
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        return text
    else:
        raise ValueError("Формат файла не поддерживается. Используйте DOCX или PDF.")

# Извлечение job_title из текста резюме
def extract_job_title(resume_text: str) -> str:
    # Ищем раздел "Цель" или заголовок
    objective_match = re.search(r"Цель[:\-]?\s*(.+)", resume_text, re.IGNORECASE)
    if objective_match:
        return objective_match.group(1).strip()

    # Если не найдено, можно установить значение по умолчанию
    return "Data Analyst"

# Генерация текста с использованием трансформера
def generate_text_with_transformer(prompt: str, max_length: int = 512, max_new_tokens: int = 150) -> str:
    input_ids = tokenizer.encode(prompt, return_tensors="pt")

    # Убедимся, что длина входных данных меньше max_length
    if input_ids.shape[1] > max_length:
        input_ids = input_ids[:, :max_length]

    output = model.generate(
        input_ids,
        max_new_tokens=max_new_tokens,
        num_return_sequences=1,
        temperature=0.7,
        top_p=0.9,
        do_sample=True
    )
    return tokenizer.decode(output[0], skip_special_tokens=True)

# Обновленная функция генерации раздела "Цель"
def generate_objective_section(job_title: str) -> str:
    prompt = f"Напиши цель для резюме на позицию {job_title}:\nЦель:"
    return generate_text_with_transformer(prompt, max_length=50)

# Функция анализа резюме
def analyze_resume(file_path: str, job_keywords: List[str]) -> Dict:
    text = read_resume_text(file_path)

    if detect(text) != 'ru':
        raise ValueError("Язык резюме должен быть русским.")

    spelling_and_grammar_errors = check_spelling_and_grammar(text)
    keyword_check = check_keywords(text, job_keywords)
    timing_issues = check_timing(text)

    skills_section = re.search(r"Навыки:\s*(.*)", text, re.IGNORECASE)
    skills = [skill.strip() for skill in skills_section.group(1).split(",")] if skills_section else []

    corrected_text = generate_corrected_text(text)
    summary = generate_summary(skills, job_keywords)
    corrected_text_with_summary = insert_summary_into_corrected_text(corrected_text, summary)

    match_score = len(keyword_check["found_keywords"]) / len(job_keywords) * 100 if job_keywords else 0
    return {
        "original_text": text,
        "corrected_text": corrected_text_with_summary,
        "summary": summary,
        "spelling_and_grammar_errors": spelling_and_grammar_errors,
        "missing_keywords": keyword_check["missing_keywords"],
        "timing_issues": timing_issues,
        "match_score": match_score
    }

# Основной блок
if __name__ == "__main__":
    from google.colab import files

    print("Загрузите файл резюме (DOCX или PDF):")
    uploaded = files.upload()
    resume_file_path = list(uploaded.keys())[0]

    print("Загрузите файл с требованиями (JSON):")
    uploaded_requirements = files.upload()
    requirements_file_path = list(uploaded_requirements.keys())[0]

    with open(requirements_file_path, 'r', encoding='utf-8') as f:
        job_keywords = json.load(f).get("job_keywords", [])

    # Загрузка модели и токенизатора
    model_name = "sberbank-ai/rugpt3small_based_on_gpt2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    try:
        # Чтение текста резюме
        resume_text = read_resume_text(resume_file_path)

        # Извлечение job_title из резюме
        job_title = extract_job_title(resume_text)

        # Анализ резюме
        result = analyze_resume(resume_file_path, job_keywords)

        print("\n--- Исправленное резюме ---\n")
        print(result["corrected_text"])

        # Генерация нового раздела "Цель"
        objective = generate_objective_section(job_title)
        print("\n--- Сгенерированная цель ---\n")
        print(objective)

        print("\n--- Замечания ---\n")
        print("Ошибки орфографии и грамматики:")
        if not result["spelling_and_grammar_errors"]["errors"]:
            print("Ошибок не обнаружено.")
        else:
            print(result["spelling_and_grammar_errors"]["errors"])

        print("\nПропущенные ключевые слова:")
        print(", ".join(result["missing_keywords"]) if result["missing_keywords"] else "Все ключевые слова найдены.")

        print(f"\nСоответствие требованиям: {result['match_score']:.2f}%")

        if result["timing_issues"]:
            print("\nЗамечания по хронологии:")
            for issue in result["timing_issues"]:
                print(issue)
    except ValueError as e:
        print(f"Ошибка: {e}")