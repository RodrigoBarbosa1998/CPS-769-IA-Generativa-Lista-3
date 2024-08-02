import openai
import pandas as pd
import os
import kaggle
import re
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

# Substitua com sua chave API
openai_api_key = '***************'  

# Classe WeatherAssistant
class WeatherAssistant:
    def __init__(self):
        self.check_data_downloaded()
        self.llm = OpenAI(api_key=openai_api_key, model="gpt-4o-mini")
        self.template = PromptTemplate(
            input_variables=['question'],
            template=(
                "Você é um assistente de clima que responde a perguntas com base em um dataset de clima. "
                "Aqui está a pergunta do usuário: {question}. Responda de forma clara e concisa."
            )
        )

    def download_data(self):
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files('gregoryoliveira/brazil-weather-information-by-inmet', path='.', unzip=True)
        print("Dataset baixado e extraído com sucesso.")
        
    def check_data_downloaded(self):
        downloaded = any(os.path.exists(f'weather_{year}') and os.path.isdir(f'weather_{year}') for year in range(2000, 2025))
        
        if downloaded:
            print("Os dados já foram baixados.")
        else:
            self.download_data()

    def load_data(self, year=None):
        data_frames = []
        folder_name = f'weather_{year}' if year else None
        
        if folder_name and os.path.exists(folder_name) and os.path.isdir(folder_name):
            for file_name in os.listdir(folder_name):
                if file_name.endswith('.csv'):
                    file_path = os.path.join(folder_name, file_name)
                    df = pd.read_csv(file_path)
                    data_frames.append(df)
        elif not year:
            for year in range(2000, 2025):
                folder_name = f'weather_{year}'
                if os.path.exists(folder_name) and os.path.isdir(folder_name):
                    for file_name in os.listdir(folder_name):
                        if file_name.endswith('.csv'):
                            file_path = os.path.join(folder_name, file_name)
                            df = pd.read_csv(file_path)
                            data_frames.append(df)
        
        if not data_frames:
            raise FileNotFoundError("Nenhum arquivo de dados encontrado.")
        
        data = pd.concat(data_frames, ignore_index=True)
        
        # Ajustar os nomes das colunas conforme necessário
        data.columns = [col.strip().lower().replace(' ', '_').replace('(', '').replace(')', '') for col in data.columns]
        
        # Verificar o nome da coluna de data correto
        if 'data_yyyy-mm-dd' in data.columns:
            data['data_yyyy-mm-dd'] = pd.to_datetime(data['data_yyyy-mm-dd'])
        else:
            raise KeyError("Coluna 'data_yyyy-mm-dd' não encontrada.")
        
        # Adicionar colunas de ano e mês
        data['year'] = data['data_yyyy-mm-dd'].dt.year
        data['month'] = data['data_yyyy-mm-dd'].dt.month
        
        return data

    def answer_question(self, question):
        # Usar o chatbot para responder à pergunta
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Ou o modelo que você está usando
            messages=[
                {"role": "system", "content": "Você é um assistente de clima que responde a perguntas com base em um dataset de clima."},
                {"role": "user", "content": question}
            ],
            max_tokens=150
        )
        return response.choices[0].message['content'].strip()

    # Métodos adicionais para obter dados
    def get_max_temperature(self, year):
        data = self.load_data(year=year)
        max_temp = data['temperatura_do_ar_-_bulbo_seco,_horaria_°c'].max()
        return max_temp

    def get_monthly_average_temperature(self, year, month):
        data = self.load_data(year=year)
        monthly_data = data[data['month'] == month]
        avg_temp = monthly_data['temperatura_do_ar_-_bulbo_seco,_horaria_°c'].mean()
        return avg_temp

    def get_cold_january(self, year):
        data = self.load_data(year=year)
        january_data = data[data['month'] == 1]
        cold_temp = january_data['temperatura_do_ar_-_bulbo_seco,_horaria_°c'].min()
        return cold_temp

    def get_hottest_day_of_year(self, year):
        data = self.load_data(year=year)
        hottest_day = data.loc[data['temperatura_do_ar_-_bulbo_seco,_horaria_°c'].idxmax()]
        return hottest_day['data_yyyy-mm-dd'], data['temperatura_do_ar_-_bulbo_seco,_horaria_°c'].max()

    def get_monthly_max_temperature(self, year):
        data = self.load_data(year=year)
        monthly_max_temps = data.groupby('month')['temperatura_do_ar_-_bulbo_seco,_horaria_°c'].max()
        hottest_month = monthly_max_temps.idxmax()
        hottest_month_temp = monthly_max_temps.max()
        return hottest_month, hottest_month_temp

    def get_max_temperature_in_period(self, start_year, end_year):
        data = self.load_data()
        period_data = data[(data['year'] >= start_year) & (data['year'] <= end_year)]
        max_temp = period_data['temperatura_do_ar_-_bulbo_seco,_horaria_°c'].max()
        return max_temp

    def get_average_temperature(self, year):
        data = self.load_data(year=year)
        avg_temp = data['temperatura_do_ar_-_bulbo_seco,_horaria_°c'].mean()
        return avg_temp

    def compare_yearly_averages(self, year1, year2):
        avg1 = self.get_average_temperature(year1)
        avg2 = self.get_average_temperature(year2)
        difference = avg1 - avg2
        return avg1, avg2, difference

    def is_january_cold(self, year):
        average_temp = self.get_monthly_average_temperature(year, 1)
        # Definindo um limite para considerar um mês como "frio"
        threshold = 20
        return average_temp < threshold

# Função para interação com o usuário
def interact_with_weather_assistant():
    assistant = WeatherAssistant()

    while True:
        question = input("Digite sua pergunta sobre o clima ou 'sair' para encerrar: ")
        if question.lower() == 'sair':
            break
        answer = assistant.answer_question(question)
        print(answer)

if __name__ == "__main__":
    interact_with_weather_assistant()
