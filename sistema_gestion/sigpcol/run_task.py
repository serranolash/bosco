import os
import sys
import django

# Asegúrate de que el directorio del proyecto esté en la ruta de búsqueda de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configura el entorno Django antes de cualquier otra cosa
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_gestion.settings')
django.setup()

from sigpcol.models import AcademicYear  # Esta importación debe hacerse después de django.setup()
import requests
from bs4 import BeautifulSoup

def update_exchange_rate_task():
    url = "https://www.bcv.org.ve/estadisticas/tipo-de-cambio"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Aquí debes ajustar el selector para obtener correctamente la tasa de cambio
        exchange_rate_element = soup.find('div', {'class': 'some-class-name'})  # Ajusta este selector
        if exchange_rate_element:
            exchange_rate = exchange_rate_element.text.strip()
            exchange_rate = float(exchange_rate.replace(',', '.'))  # Convierte a float

            # Imprime la tasa de cambio obtenida para verificar
            print(f"Tasa de cambio obtenida: {exchange_rate}")

            # Actualiza la tasa de cambio en todos los años académicos
            academic_years = AcademicYear.objects.all()
            for year in academic_years:
                year.tasa_moneda = exchange_rate
                year.save()

if __name__ == "__main__":
    update_exchange_rate_task()
