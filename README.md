# Componentes del Paquete

## Clase `UrlEMT`

### Funciones y Métodos
- **`__init__`**: Constructor que inicializa la instancia y recopila enlaces válidos.
- **`select_valid_urls`**: Método estático que filtra y devuelve URLs válidas desde la web de la EMT.
- **`get_url(year, month)`**: Obtiene la URL específica para el año y mes proporcionados.
- **`get_csv(year, month)`**: Descarga y extrae un archivo CSV del conjunto de datos para el año y mes especificados.

## Clase `BiciMad`

### Descripción
**Gestiona los datos de uso de bicicletas para un mes y año específicos**, proporcionando métodos para la limpieza y el análisis de los datos.

### Métodos
- **`__init__(month, year)`**: Inicializa los datos del mes y año seleccionados.
- **`get_data(month, year)`**: Retorna un DataFrame con los datos de uso para el mes y año.
- **`clean`**: Limpia el DataFrame, preparándolo para el análisis.
- **`resume`**: Retorna un resumen estadístico de los datos.
- **Otros métodos incluyen** `bikes_not_locked_in_station`, `fleet_1_bikes`, `day_time`, `bar_diagram`, `weekday_time`, `total_usage_day`, `usage_per_day_per_station`, `most_popular_stations`, y `usage_from_most_popular_station`.

# Uso Básico

```python
from bicimad import UrlEMT, BiciMad

# Configurar la conexión y descargar datos
url_manager = UrlEMT()
data = url_manager.get_csv(2023, 2)

# Cargar y analizar los datos
bicimad = BiciMad(2, 2023)
print(bicimad.resume())
