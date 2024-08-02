import pandas as pd
import os
import kaggle
import re

class WeatherAssistant:
    def __init__(self):
        # Verificar se os dados já foram baixados e extraídos
        self.check_data_downloaded()

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

    def answer_question(self, question):
        question = question.lower()
        
        # Usar expressões regulares para identificar os anos
        year_matches = re.findall(r'\b(\d{4})\b', question)
        
        # Se houver dois anos especificados, comparar as médias
        if 'comparar' in question and len(year_matches) == 2:
            year1, year2 = int(year_matches[0]), int(year_matches[1])
            avg1 = self.get_average_temperature(year1)
            avg2 = self.get_average_temperature(year2)
            
            if avg1 > avg2:
                comparison = "maior"
            elif avg1 < avg2:
                comparison = "menor"
            else:
                comparison = "igual"

            return (f"A média da temperatura no ano de {year1} foi {avg1:.2f}°C, "
                    f"enquanto que a média de {year2} foi {avg2:.2f}°C, portanto a média de {year1} foi {comparison} do que a de {year2}.")
        
        # Outras condições permanecem inalteradas
        elif 'dia mais quente' in question:
            if len(year_matches) == 1:
                year = int(year_matches[0])
                day, temp = self.get_hottest_day_of_year(year)
                return f"O dia mais quente de {year} foi {day.date()} com temperatura de {temp:.2f}°C."
            else:
                return "Por favor, especifique o ano."

        elif 'média' in question and 'mês' in question:
            if len(year_matches) == 1 and 'de' in question:
                year = int(year_matches[0])
                month_match = re.search(r'\b(\d{1,2})\b', question)
                month = int(month_match.group(1)) if month_match else None
                if month:
                    avg_temp = self.get_monthly_average_temperature(year, month)
                    return f"A média da temperatura em {month}/{year} foi {avg_temp:.2f}°C."
                else:
                    return "Por favor, especifique o mês."
            else:
                return "Por favor, especifique o ano e o mês."

        elif 'média' in question:
            if len(year_matches) == 1:
                year = int(year_matches[0])
                avg_temp = self.get_average_temperature(year)
                return f"A média da temperatura no ano de {year} foi {avg_temp:.2f}°C."
            else:
                return "Por favor, especifique o ano."

        elif 'frio' in question and 'janeiro' in question:
            if len(year_matches) == 1:
                year = int(year_matches[0])
                if self.is_january_cold(year):
                    return f"Janeiro de {year} fez frio."
                else:
                    return f"Janeiro de {year} não fez frio."
            else:
                return "Por favor, especifique o ano."

        elif 'mês mais quente' in question:
            if len(year_matches) == 1:
                year = int(year_matches[0])
                month, temp = self.get_monthly_max_temperature(year)
                return f"O mês mais quente de {year} foi o mês {month} com temperatura máxima de {temp:.2f}°C."
            else:
                return "Por favor, especifique o ano."

        elif 'maior temperatura registrada' in question:
            year_range_match = re.search(r'(\d{4})\s*a\s*(\d{4})', question)
            start_year = int(year_range_match.group(1)) if year_range_match else None
            end_year = int(year_range_match.group(2)) if year_range_match else None
            if start_year and end_year:
                max_temp = self.get_max_temperature_in_period(start_year, end_year)
                return f"A maior temperatura registrada no período de {start_year} a {end_year} foi {max_temp:.2f}°C."
            else:
                return "Por favor, especifique o período."

        else:
            return "Pergunta não reconhecida. Por favor, formule a pergunta de forma diferente."


if __name__ == "__main__":
    assistant = WeatherAssistant()

    print("Digite sua pergunta sobre dados meteorológicos (ou 'sair' para encerrar):")
    while True:
        question = input("> ")
        if question.lower() == 'sair':
            break
        response = assistant.answer_question(question)
        print(response)
