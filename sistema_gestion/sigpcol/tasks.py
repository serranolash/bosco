import time
import requests
from bs4 import BeautifulSoup
from background_task import background
from .models import AcademicYear

@background(schedule=60)
def update_exchange_rate_task():
    url = "https://www.bcv.org.ve/"
    
    for _ in range(3):  # Intentar 3 veces
        try:
            response = requests.get(url, timeout=30)  # Aumenta el timeout a 30 segundos
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Intentar encontrar el valor en algún lugar del texto
                exchange_rate = None
                for div in soup.find_all('div'):
                    if 'USD' in div.text:  # Buscamos algo que contenga "USD" en el texto
                        # Intentar extraer la tasa de cambio del texto
                        exchange_rate_text = div.find_next('div').text.strip()
                        
                        # Filtrar solo los números y la coma
                        filtered_value = ''.join([c for c in exchange_rate_text if c.isdigit() or c == ','])
                        exchange_rate = filtered_value.replace(',', '.')

                        # Verificar si el valor filtrado es un número válido
                        try:
                            exchange_rate_decimal = float(exchange_rate)
                            print(f"Tasa de cambio obtenida: {exchange_rate_decimal}")  # Verificar que estás obteniendo la tasa correcta
                            
                            # Actualizar el modelo con la tasa de cambio
                            academic_years = AcademicYear.objects.all()
                            for year in academic_years:
                                year.tasa_moneda = exchange_rate_decimal
                                year.save()
                            return  # Salir si todo salió bien
                        except ValueError:
                            print(f"Error al convertir la tasa de cambio: {exchange_rate}")
                        
                if not exchange_rate:
                    print("No se pudo encontrar el elemento de la tasa de cambio.")
            else:
                print("No se pudo obtener la página web.")
        except Exception as e:
            print(f"Error al intentar obtener la tasa de cambio: {e}")
            time.sleep(1000)  # Esperar 5 segundos antes de intentar nuevamente
