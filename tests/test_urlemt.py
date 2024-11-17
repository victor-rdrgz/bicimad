import re
import unittest
from urllib.error import URLError
import zipfile

import requests
from unittest.mock import MagicMock, patch

# Imports del proyecto local
from bicimad.urlemt import UrlEMT, get_links

class TestUrlEMT(unittest.TestCase):

    FILE_URL = '<img src="/Imagenes/Extensiones-de-archivos/zip_logo.aspx"/><a target="_blank" href="/getattachment/51ba4be6-596f-41d3-8bab-634c4be569c5/trips_21_10_October-csv.aspx" title="Datos de uso de octubre de 2021. Nueva ventana" > Datos de uso de octubre de 2021</a>'
    def test_get_links_valid_html(self):
        html_content = '''
        <a href="/getattachment/1234/trips_21_10_data-csv.aspx">Download</a>
        <a href="/getattachment/5678/trips_22_01_data-csv.aspx">Download</a>
        '''
        expected_links = {
            '/getattachment/1234/trips_21_10_data-csv.aspx', 
            '/getattachment/5678/trips_22_01_data-csv.aspx'}
        self.assertEqual(set(get_links(html_content)), expected_links)


    def test_get_links_invalid_html(self):
        html_content = '<html><body>No links here</body></html>'
        self.assertEqual(set(get_links(html_content)), set())


    def test_get_links_non_string_input(self):
        with self.assertRaises(TypeError):
            get_links(1234)


    @patch('urllib.request.urlopen')
    def test_select_valid_urls_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = self.FILE_URL.encode("utf-8")
        mock_urlopen.return_value = mock_response

        links = UrlEMT.select_valid_urls()
        self.assertIn((21, 10), links)


    @patch('urllib.request.urlopen')
    def test_select_valid_urls_fail(self, mock_urlopen):
        mock_urlopen.side_effect = URLError('Failed to reach server')
        with self.assertRaises(ConnectionError):
            UrlEMT.select_valid_urls()
            
    
    @patch('urllib.request.urlopen')
    def test_select_valid_urls_fail_no_200(self, mock_urlopen):
        # Configurar el mock para simular un código de estado HTTP distinto de 200
        mock_response = MagicMock()
        mock_response.getcode.return_value = 404  # Simular un estado 404
        mock_urlopen.return_value = mock_response

        # Llamar a la función y verificar que se lanza ConnectionError
        with self.assertRaises(ConnectionError) as context:
            UrlEMT.select_valid_urls()

        # Verificar el mensaje de la excepción
        self.assertIn(
            'Error al intentar conectar con el servidor', 
            str(context.exception))
        
        
    @patch('urllib.request.urlopen')
    @patch('requests.head')
    def test_urlopen_head_check_fail(self, mock_head, mock_urlopen):
        # Configura el mock para retornar correctamente en la primera llamada
        # y lanzar una excepción URLError en la segunda llamada
        successful_response = MagicMock()
        successful_response.getcode.return_value = 200
        successful_response.read.return_value = self.FILE_URL.encode('utf-8')
        mock_urlopen.return_value = successful_response
        
        unsuccessful_response = MagicMock()
        unsuccessful_response.getcode.return_value = 400
        unsuccessful_response.read.return_value = b"Unsuccess"
        mock_head.return_value = unsuccessful_response

        links = UrlEMT.select_valid_urls()
        self.assertNotIn((21, 10), links)

        
    def test_get_url_success(self):
        url_from_emt = UrlEMT()
        url_from_emt.get_url(12, 22)
        
        
    def test_get_url_test_keyerror(self):
        url_from_emt = UrlEMT()
        with self.assertRaises(KeyError):
            url_from_emt.get_url(12, 23)
        

    def test_get_url_invalid_month(self):
        with self.assertRaises(ValueError):
            url_emt = UrlEMT()
            url_emt.get_url(13, 22)
    
    
    def test_get_url_invalid_year(self):
        with self.assertRaises(ValueError):
            url_emt = UrlEMT()
            url_emt.get_url(12, 13)
            
            
    def test_get_url_fail_21_10(self):
        with self.assertRaises(ValueError):
            url_emt = UrlEMT()
            url_emt.get_url(10, 21)


    @patch('bicimad.urlemt.UrlEMT.get_url')
    @patch('requests.get')
    @patch('zipfile.ZipFile')
    @patch('io.StringIO')
    def test_get_csv_success(self, mock_string_io, mock_zip_file, mock_requests_get, mock_get_url):
        # Valores de entrada para la prueba
        month = 10
        year = 23
        
        # Contenido simulado de un archivo CSV
        csv_content = "id,name,value\n1,Test,100"
        encoded_csv_content = csv_content.encode('utf-8')  # CSV debe ser bytes antes de decodificar

        # Configuración de get_url para devolver una parte de la URL
        mock_get_url.return_value = '/test/url/for/october'
        
        # Simulación de requests.get
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b"Dummy ZIP content"
        mock_requests_get.return_value = mock_response
        
        # Simulación de zipfile.ZipFile y sus métodos
        mock_zip_instance = MagicMock()
        mock_zip_instance.namelist.return_value = ['data.fake', 'data.csv']
        mock_zip_file.return_value.__enter__.return_value = (
            mock_zip_instance)
        
        mock_csv_file = MagicMock()
        mock_csv_file.read.return_value = encoded_csv_content
        mock_zip_instance.open.return_value.__enter__.return_value = mock_csv_file
        
        # Simular StringIO para capturar el resultado
        mock_string_io.return_value.getvalue.return_value = csv_content

        # Crear una instancia de UrlEMT y ejecutar el método get_csv
        instance = UrlEMT()
        result = instance.get_csv(month, year)
        
        # Asegurarse de que las funciones se llamaron correctamente
        mock_requests_get.assert_called_once_with(UrlEMT.EMT + '/test/url/for/october')
        mock_string_io.assert_called()


    @patch('requests.get')
    def test_get_csv_fail(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException('Failed to download')
        url_emt = UrlEMT()
        url_emt.get_url = MagicMock(return_value='https://example.com/file.csv')
        with self.assertRaises(ConnectionError):
            url_emt.get_csv(21, 10)
            
            
    @patch('bicimad.urlemt.UrlEMT.get_url', return_value='/test/url')
    @patch('requests.get')
    def test_get_csv_empty_zip(self, mock_get, mock_get_url):
        # Configurar la respuesta de requests.get
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()  # No lanzar excepción de status
        mock_response.content = b'Dummy content for zip'  # Contenido simulado del ZIP
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Crear un mock para zipfile.ZipFile que siempre devuelve una lista vacía para namelist
        with patch('zipfile.ZipFile') as mock_zip:
            mock_zip_instance = MagicMock()
            mock_zip_instance.namelist.return_value = []
            mock_zip.return_value.__enter__.return_value = mock_zip_instance
            # Instanciar el objeto que contiene el método get_csv (supongamos que se llama MyClass)
            obj = UrlEMT()
            # Ejecutar el método y capturar la excepción
            with self.assertRaises(FileNotFoundError) as context:
                obj.get_csv(1, 23)  # Asumiendo que 1 es el mes y 2023 el año

            # Verificar que el mensaje de la excepción es correcto
            self.assertIn("No se encontró ningún archivo csv en el ZIP", str(context.exception))
            
            
    @patch('bicimad.urlemt.UrlEMT.get_url', return_value='/test/url')
    @patch('requests.get')
    def test_get_csv_invalid_zip_file(self, mock_get, mock_get_url):
        # Configurar la respuesta de requests.get
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()  # No lanzar excepción de status
        mock_response.content = b'not a zip content'  # Contenido simulado que no es un ZIP
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Crear un mock para zipfile.ZipFile que lance una excepción BadZipFile
        with patch('zipfile.ZipFile', side_effect=zipfile.BadZipFile):
            # Instanciar el objeto que contiene el método get_csv
            obj = UrlEMT()  # Reemplaza MyClass con el nombre de tu clase real que contiene el método get_csv

            # Ejecutar el método y capturar la excepción
            with self.assertRaises(FileNotFoundError) as context:
                obj.get_csv(3, 22)  # Asumiendo que 3 es el mes y 22 el año

            # Verificar que el mensaje de la excepción es correcto
            self.assertIn("El archivo descargado no es un ZIP válido", str(context.exception))
            
            
    @patch('bicimad.urlemt.UrlEMT.get_url')
    @patch('requests.get')
    @patch('zipfile.ZipFile')
    @patch('io.StringIO')
    def test_get_csv_none_content(
        self, mock_string_io, mock_zip_file, mock_requests_get, mock_get_url):
        # Contenido simulado de un archivo CSV
        csv_content = ""
        encoded_csv_content = csv_content.encode('utf-8')  # CSV debe ser bytes antes de decodificar

        # Configuración de get_url para devolver una parte de la URL
        mock_get_url.return_value = '/test/url/for/october'
        
        # Simulación de requests.get
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b"Dummy ZIP content"
        mock_requests_get.return_value = mock_response
        
         # Simulación de zipfile.ZipFile y sus métodos
        mock_zip_instance = MagicMock()
        mock_zip_file.return_value = mock_zip_instance
        mock_zip_instance.namelist.return_value = ['data.csv']
        mock_zip_file.return_value.__enter__.return_value = (
            mock_zip_instance)
        mock_csv_file = MagicMock()
        mock_csv_file.read.return_value = encoded_csv_content
        mock_zip_instance.open.return_value.__enter__.return_value = mock_csv_file
        # Simular StringIO para capturar el resultado
        mock_string_io.return_value.getvalue.return_value = ''

        # Crear una instancia de UrlEMT y ejecutar el método get_csv
        obj = UrlEMT()
        with self.assertRaises(ValueError) as context:
            obj.get_csv(1, 22)
        # Verificar que el mensaje de la excepción es correcto
        self.assertIn("No se pudo leer el archivo CSV", str(context.exception))


    def test_str(self):
        obj_to_print = UrlEMT()
        lines = str(obj_to_print).strip().split('\n')
        pattern = re.compile(r"\(\d{2}, \d{1,2}\): \/getattachment\/[a-f0-9-]+\/trips_\d{2}_\d{2}_[A-Za-z]+-csv\.aspx")
        for line in lines:
            assert pattern.match(line), f"Esta línea no coincide con el formato esperado: {line}"
            
        
        
         # Crear un mock del objeto MyClass
        mock_obj = MagicMock(spec=UrlEMT)
        # Convertir el objeto mock a una cadena para forzar la llamada a __str__
        str(mock_obj)
        # Verificar que __str__ fue llamado al menos una vez
        mock_obj.__str__.assert_called()
        # Alternativamente, verificar que __str__ fue llamado exactamente una vez
        # mock_obj.__str__.assert_called_once()
        # Para verificar si fue llamado al menos una vez usando call_count
        self.assertGreaterEqual(mock_obj.__str__.call_count, 1)


if __name__ == '__main__':
    unittest.main()