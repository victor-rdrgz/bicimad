import io
import re
import urllib
import zipfile

import requests


def get_links(html: str) -> list:
    '''
    Toma como parámetro un texto HTML y devuelve un conjunto con
    todos los enlaces que coincidan con el patrón definido.
    '''
    # Verificar que el argumento html sea de tipo str
    if not isinstance(html, str):
        raise TypeError(
            "El argumento 'html' debe ser una cadena de texto.")
    # Encontrar todas las coincidencias del patrón en el HTML
    pattern = r'href="(/getattachment/[a-zA-Z0-9-]*/trips_\d{2}_\d{2}_[^"]*-csv\.aspx)"'
    return list(set(re.findall(pattern, html)))


class UrlEMT():
    EMT = 'https://opendata.emtmadrid.es/'
    GENERAL = '/Datos-estaticos/Datos-generales-(1)'
    
    
    def __init__(self):
      '''Buils the object with the links from Bicimad URL'''
      self.__enlaces = UrlEMT.select_valid_urls()


    @staticmethod
    def select_valid_urls():
        '''
        método estático que se encarga de actualizar el atributo de
        los objetos de la clase. Devuelve un conjunto de enlaces válidos.
        Si la petición al servidor de la EMT devuelve un código de
        retorno distinto de 200, la función lanza una excepción de
        tipo ConnectionError.
        '''
        try:
            # Realizar la solicitud HTTP y verificar el código de estado
            r = urllib.request.urlopen(UrlEMT.EMT + UrlEMT.GENERAL)
            if r.getcode() != 200:
                raise ConnectionError(
                    f"Error al intentar conectar con el servidor. "
                    f"Status code: {r.getcode()}")
            # Obtener los enlaces válidos del HTML
            links = get_links(r.read().decode("utf-8"))
            # Analizamos todos los enlaces extraidos
            indexed_links = {}
            for link in links:
                r = requests.head(
                    UrlEMT.EMT+link, allow_redirects=True, timeout=20)
                if r.status_code == 200:
                    splitted_url = link.split('_')
                    indexed_links[
                        int(splitted_url[1]), int(splitted_url[2])] = link
            return indexed_links

        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Error al intentar conectar con el servidor: {e}")

    def get_url(self, month: int, year: int) -> str:
        """
        Devuelve el string de la URL correspondiente al mes/año proporcionados

        Parámetros:
        - year (str): Año en formato de cadena (se espera '21', '22' o '23').
        - month (str): Mes en formato de cadena (entre '1' y '12').

        Retorno:
        - str: URL correspondiente al mes y año si existe.

        Excepciones:
        - ValueError: Si el año o mes no están en los rangos válidos o
            no existe una URL para esa combinación.
        """
        try:
            # Los datos del mes 10 del año 2021 está mal generado por la EMT,
            # por lo que se pide que no se use ese fichero.
            if month==10 and year==21:
                raise ValueError("No hay datos para el par mes/año introducido")
            # Comprobación de rango válido para año y mes
            if year not in range(21, 24):
                raise ValueError("El año debe estar entre 21 y 23.")

            if month not in range(1, 13):
                raise ValueError("El mes debe estar entre 1 y 12.")
        except ValueError:
            # Si la combinación de año y mes no tiene un enlace
            # registrado, lanzar excepción
            raise ValueError("No hay datos para el par mes, año introducido")

        try:
            return self.__enlaces[year, month]
        except KeyError:
            # Si la combinación de año y mes no tiene un enlace
            # registrado, lanzar excepción
            raise KeyError("No hay datos para el par mes, año introducido")


    def get_csv(self, month: int, year: int) -> str:
        '''
        método de instancia que acepta los argumentos de tipo entero
        month y year y devuelve un fichero en formato CSV correspondiente
        al mes month y año year.
        '''
        url = UrlEMT.EMT + self.get_url(month, year)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error al descargar el archivo ZIP: {e}")
        try:
            # Descomprimir el archivo ZIP en memoria
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                # Listar los archivos en el ZIP
                nombres_archivos = z.namelist()
                if not nombres_archivos:
                    raise FileNotFoundError(
                        "No se encontró ningún archivo csv en el ZIP")
                csv_file = [file for file in nombres_archivos 
                            if file.endswith('.csv')]
                # Extraer el CSV
                # (suponiendo que es el primer archivo en la lista)
                with z.open(csv_file[0]) as csv_file:
                    # Leer el contenido del CSV en un objeto TextIO.
                    # Convierte a string y crea un TextIO
                    contenido_csv = io.StringIO(
                        csv_file.read().decode('utf-8'))
                    if contenido_csv.getvalue()=='':
                        raise ValueError(
                            "No se pudo leer el archivo CSV")
            return contenido_csv
        except zipfile.BadZipFile:
            raise FileNotFoundError(
                'El archivo descargado no es un ZIP válido')
        except ValueError as e:
            raise ValueError(e)
        except FileNotFoundError as e:
            raise FileNotFoundError(e)
        except Exception as e:
            raise Exception("Error desconocido. Parando ejecución")


    def __str__(self):
        return (
            "\n".join([f"{key}: {link}" 
                for key, link in self.__enlaces.items()]))
