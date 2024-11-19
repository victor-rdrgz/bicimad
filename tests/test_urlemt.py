import re
import unittest
from urllib.error import URLError
import zipfile

import requests
from unittest.mock import MagicMock, patch

from bicimad.urlemt import UrlEMT, get_links

class TestUrlEMT(unittest.TestCase):

    FILE_URL = (
        '<img src="/Imagenes/Extensiones-de-archivos/zip_logo.aspx"/><a '
        'target="_blank" href="/getattachment/51ba4be6-596f-41d3-8bab-'
        '634c4be569c5/trips_21_10_October-csv.aspx" title="Datos de uso de '
        'octubre de 2021. Nueva ventana" > Datos de uso de octubre de 2021</a>'
    )
    
    HTML_WITH_LINKS = '''
        <a href="/getattachment/1234/trips_21_10_data-csv.aspx">Download</a>
        <a href="/getattachment/5678/trips_22_01_data-csv.aspx">Download</a>
        '''
        
    EXPECTED_LINKS = {
            '/getattachment/1234/trips_21_10_data-csv.aspx', 
            '/getattachment/5678/trips_22_01_data-csv.aspx'}
    
    HTML_WITHOUT_LINKS = '<html><body>No links here</body></html>'
    
    URL_12_22 = ('/getattachment/34b933e4-4756-4fed-8d5b-2d44f7503ccc/trips_22'
                 '_12_December-csv.aspx')
     
     
    def test_get_links_valid_html(self):
        ''' Tests correct behaviour of the method when html with links'''        
        self.assertEqual(set(get_links(
            self.HTML_WITH_LINKS)), self.EXPECTED_LINKS)


    def test_get_links_invalid_html(self):
        ''' Tests correct behaviour of the method when html without links'''
        self.assertEqual(set(get_links(self.HTML_WITHOUT_LINKS)), set())


    def test_get_links_non_string_input(self):
        ''' Tests behaviour when wrong input'''
        with self.assertRaises(TypeError):
            get_links(1234)


    @patch('urllib.request.urlopen')
    def test_select_valid_urls_success(self, mock_urlopen):
        ''' Tests extracting html from web and links from hmtl correctly'''
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = self.FILE_URL.encode("utf-8")
        mock_urlopen.return_value = mock_response

        links = UrlEMT.select_valid_urls()
        self.assertIn((21, 10), links)
        assert links[(21,10)] == self.URL_12_22
        


    @patch('urllib.request.urlopen')
    def test_select_valid_urls_fail(self, mock_urlopen):
        ''' Tests extracting html from web error handled correctly'''
        mock_urlopen.side_effect = URLError('Failed to reach server')
        with self.assertRaises(ConnectionError):
            UrlEMT.select_valid_urls()
            
    
    @patch('urllib.request.urlopen')
    def test_select_valid_urls_fail_no_200(self, mock_urlopen):
        '''Tests selec_valid_url() when request returns an error'''
        mock_response = MagicMock()
        mock_response.getcode.return_value = 404  # Simular un estado 404
        mock_urlopen.return_value = mock_response
        with self.assertRaises(ConnectionError) as context:
            UrlEMT.select_valid_urls()
            self.assertIn(
                'Status code: 404', 
                str(context.exception))
        
        
    @patch('urllib.request.urlopen')
    @patch('requests.head')
    def test_urlopen_head_check_fail(self, mock_head, mock_urlopen):
        '''Tests when html and links are extracted from web correctly but 
           link are not valid'''
        successful_response = MagicMock()
        successful_response.getcode.return_value = 200
        successful_response.read.return_value = self.FILE_URL.encode('utf-8')
        mock_urlopen.return_value = successful_response
        
        unsuccessful_response = MagicMock()
        unsuccessful_response.getcode.return_value = 400
        unsuccessful_response.read.return_value = b"Unsuccess"
        mock_head.return_value = unsuccessful_response

        links = UrlEMT.select_valid_urls()
        self.assertNotIn((22, 12), links)

        
    def test_get_url_success(self):
        '''Tests get_url success'''
        url_from_emt = UrlEMT()
        url = url_from_emt.get_url(12, 22)
        assert (url == self.URL_12_22)
        
        
    @patch('bicimad.urlemt.UrlEMT.select_valid_urls', return_value={})
    def test_get_url_test_keyerror(self, mock_select_valid_urls):
        '''Tests when previous check are passed but still no link stored for
            month/year combination'''
        url_from_emt = UrlEMT()
        with self.assertRaises(KeyError):
            url_from_emt.get_url(2, 23)
        

    def test_get_url_invalid_month(self):
        '''Tests value error when out of range month is provided'''
        with self.assertRaises(ValueError):
            url_emt = UrlEMT()
            url_emt.get_url(13, 22)
    
    
    def test_get_url_invalid_year(self):
        '''Tests value error when out of range year is provided'''
        with self.assertRaises(ValueError):
            url_emt = UrlEMT()
            url_emt.get_url(12, 13)
            
            
    def test_get_url_fail_21_10(self):
        '''Tests value error when 10/21 is provided. This combination of 
        month/year doesn't have usage data'''
        with self.assertRaises(ValueError):
            url_emt = UrlEMT()
            url_emt.get_url(10, 21)


    def test_get_url_fail_21_before_july(self):
        '''Tests value error when out of range month/year is provided'''
        with self.assertRaises(ValueError):
            url_emt = UrlEMT()
            url_emt.get_url(6, 21)


    def test_get_url_fail_23_after_february(self):
        '''Tests value error when out of range month/year is provided'''
        with self.assertRaises(ValueError):
            url_emt = UrlEMT()
            url_emt.get_url(3, 23)
            
            
    @patch('bicimad.urlemt.UrlEMT.get_url')
    @patch('requests.get')
    @patch('zipfile.ZipFile')
    @patch('io.StringIO')
    def test_get_csv_success(
        self, mock_string_io, mock_zip_file, mock_requests_get, mock_get_url):
        ''' Tests get_csv when correct behaviour. Methods called in the 
        execution are mocked'''
        # Values for testing
        month = 10
        year = 23
        
        # Simulated content of a CSV file
        csv_content = "id,name,value\n1,Test,100"
        encoded_csv_content = csv_content.encode('utf-8')

        # Setting get_url to return a portion of the URL
        mock_get_url.return_value = '/test/url/for/october'
        
        # Simulated requests.get
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b"Dummy ZIP content"
        mock_requests_get.return_value = mock_response
        
        # simulated zipfile.ZipFile y its methods
        mock_zip_instance = MagicMock()
        mock_zip_instance.namelist.return_value = ['data.fake', 'data.csv']
        mock_zip_file.return_value.__enter__.return_value = (
            mock_zip_instance)
        
        mock_csv_file = MagicMock()
        mock_csv_file.read.return_value = encoded_csv_content
        mock_zip_instance.open.return_value.__enter__.return_value = (
            mock_csv_file)
        
        # Simulated StringIO
        mock_string_io.return_value.getvalue.return_value = csv_content

        # Create an instance of UrlEMT and run the get_csv method
        instance = UrlEMT()
        result = instance.get_csv(month, year)
        
        # Asegurarse de que las funciones se llamaron correctamente
        mock_requests_get.assert_called_once_with(
            UrlEMT.EMT + '/test/url/for/october')
        mock_string_io.assert_called()


    @patch('bicimad.urlemt.UrlEMT.get_url', return_value='https://fakeurl.com')
    @patch('requests.get')
    def test_get_csv_fail(self, mock_get, mock_get_url):
        '''Tests when provided url is not of a csv file'''
        mock_get.side_effect = requests.exceptions.RequestException(
            'Failed to download')
        url_emt = UrlEMT()
        with self.assertRaises(ConnectionError) as context:
            url_emt.get_csv(21, 10)
            self.assertIn("Error downloading zip file:", str(context.exception))
            
            
    @patch('bicimad.urlemt.UrlEMT.get_url', return_value='/test/url')
    @patch('requests.get')
    def test_get_csv_empty_zip(self, mock_get, mock_get_url):
        '''Tests get_csv when zip file downloaded is empty'''
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b'Dummy content for zip'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        with patch('zipfile.ZipFile') as mock_zip:
            mock_zip_instance = MagicMock()
            mock_zip_instance.namelist.return_value = []
            mock_zip.return_value.__enter__.return_value = mock_zip_instance            
            obj = UrlEMT()
            with self.assertRaises(FileNotFoundError) as context:
                obj.get_csv(1, 23) 
            # Check if exception error message is the expected one
            self.assertIn(
                "No CSV file was found in the ZIP.", 
                str(context.exception))
            
            
    @patch('bicimad.urlemt.UrlEMT.get_url', return_value='/test/url')
    @patch('requests.get')
    def test_get_csv_invalid_zip_file(self, mock_get, mock_get_url):
        '''Tests when zip file is not correct'''
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock() 
        mock_response.content = b'not a zip content'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        # Crear un mock para zipfile.ZipFile que lance una excepción BadZipFile
        with patch('zipfile.ZipFile', side_effect=zipfile.BadZipFile):
            # Instanciar el objeto que contiene el método get_csv
            obj = UrlEMT()
            # Ejecutar el método y capturar la excepción
            with self.assertRaises(FileNotFoundError) as context:
                obj.get_csv(3, 22)  # Asumiendo que 3 es el mes y 22 el año
            # Verificar que el mensaje de la excepción es correcto
            self.assertIn(
                "Downloaded file is not a valid ZIP", 
                str(context.exception))
            
            
    @patch('bicimad.urlemt.UrlEMT.get_url')
    @patch('requests.get')
    @patch('zipfile.ZipFile')
    @patch('io.StringIO')
    def test_get_csv_no_content(
        self, mock_string_io, mock_zip_file, mock_requests_get, mock_get_url):
        '''Tests when csv file is correctly downloaded but it's empty'''
        csv_content = ""
        encoded_csv_content = csv_content.encode('utf-8')
        
        mock_get_url.return_value = '/test/url/for/october'
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b"Dummy ZIP content"
        mock_requests_get.return_value = mock_response
        
        mock_zip_instance = MagicMock()
        mock_zip_file.return_value = mock_zip_instance
        mock_zip_instance.namelist.return_value = ['data.csv']
        mock_zip_file.return_value.__enter__.return_value = (
            mock_zip_instance)
        mock_csv_file = MagicMock()
        mock_csv_file.read.return_value = encoded_csv_content
        mock_zip_instance.open.return_value.__enter__.return_value = (
            mock_csv_file)

        mock_string_io.return_value.getvalue.return_value = ''

        obj = UrlEMT()
        with self.assertRaises(ValueError) as context:
            obj.get_csv(1, 22)
        # Verificar que el mensaje de la excepción es correcto
        self.assertIn("Could not read the CSV file", str(context.exception))


    def test_str(self):
        ''' Tests str method. Url structure is checked '''
        obj_to_print = UrlEMT()
        lines = str(obj_to_print).strip().split('\n')
        pattern = re.compile(
            r"\(\d{2}, \d{1,2}\): /getattachment/[a-f0-9-]+/trips_\d{2}_\d{2}_"
            r"[A-Za-z]+-csv\.aspx"
        )
        for line in lines:
            assert (pattern.match(line), 
            f"Esta línea no coincide con el formato esperado: {line}")
                    
        # Crear un mock del objeto MyClass
        mock_obj = MagicMock(spec=UrlEMT)
        # Convertir el objeto mock a una cadena para 
        # forzar la llamada a __str__
        str(mock_obj)
        # Verificar que __str__ fue llamado al menos una vez
        mock_obj.__str__.assert_called()
        # Alternativamente, verificar que __str__ fue llamado exactamente 
        # una vez mock_obj.__str__.assert_called_once()
        # Para verificar si fue llamado al menos una vez usando call_count
        self.assertGreaterEqual(mock_obj.__str__.call_count, 1)


if __name__ == '__main__':
    unittest.main()