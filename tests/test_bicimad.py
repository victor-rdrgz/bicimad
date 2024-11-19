import unittest
from unittest.mock import patch, MagicMock, mock_open

from pandas.errors import EmptyDataError, ParserError
import pandas as pd
import numpy as np
from bicimad import BiciMad

class TestBiciMad(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.month = 5  # Mes de prueba
        cls.year = 22  # Año de prueba
        # cls.data = BiciMad(5, 22).data()

    def setUp(self):
        # Crear una instancia de BiciMad para cada prueba
        self.bicimad = BiciMad(self.month, self.year)

    @patch('bicimad.BiciMad.clean')
    @patch('bicimad.BiciMad.get_data')
    def test_init_calls_get_data_and_clean(self, mock_get_data, mock_clean):
        # Configurar el retorno simulado de get_data
        mock_get_data.return_value = pd.DataFrame({
            'fecha': pd.to_datetime(['2023-05-01']),
            'idBike': ['12345'],
            'trip_minutes': [30]
        })

        # Crear una instancia de BiciMad para probar la inicialización
        bicimad_instance = BiciMad(5, 22)

        # Verificar que los métodos se llamaron con los argumentos esperados
        mock_get_data.assert_called_once_with(5, 22)
        mock_clean.assert_called_once()

        # Verificar que los atributos se inicializaron correctamente
        self.assertEqual(bicimad_instance._BiciMad__month, 5)
        self.assertEqual(bicimad_instance._BiciMad__year, 22)
        self.assertIsInstance(bicimad_instance._BiciMad__data, pd.DataFrame)


    def test_get_data_valid_input(self):
        with patch('bicimad.UrlEMT.get_csv') as mock_get_csv:
            mock_get_csv.return_value = 'path/to/csv'
            with patch('pandas.read_csv') as mock_read_csv:
                mock_read_csv.return_value = pd.DataFrame({
                    'fecha': pd.to_datetime(['2022-05-01']),
                    'idBike': ['12345'],
                    'trip_minutes': [30]
                })
                result = BiciMad.get_data(self.month, self.year)
                self.assertIsInstance(result, pd.DataFrame)
                
                
    def test_get_data_invalid_month(self):
        with patch('bicimad.UrlEMT.get_csv') as mock_get_csv:
            mock_get_csv.return_value = 'path/to/csv'
            with patch('pandas.read_csv') as mock_read_csv:
                mock_read_csv.return_value = pd.DataFrame({
                    'fecha': pd.to_datetime(['2023-05-01']),
                    'idBike': ['12345'],
                    'trip_minutes': [30]
                })
                result = BiciMad.get_data(13, self.year)
                self.assertIsInstance(result, pd.DataFrame)
                
                
    def test_get_data_invalid_year(self):
        with patch('bicimad.UrlEMT.get_csv') as mock_get_csv:
            mock_get_csv.return_value = 'path/to/csv'
            with patch('pandas.read_csv') as mock_read_csv:
                mock_read_csv.return_value = pd.DataFrame({
                    'fecha': pd.to_datetime(['2023-05-01']),
                    'idBike': ['12345'],
                    'trip_minutes': [30]
                })
                result = BiciMad.get_data(self.month, 25)
                self.assertIsInstance(result, pd.DataFrame)
                
                
    @patch('bicimad.UrlEMT.get_csv',
           side_effect=Exception("Simulated connection error"))
    def test_get_data_connection_error(self, mock_get_csv):
        with self.assertRaises(ConnectionError) as context:
            BiciMad.get_data(5, 23)
        self.assertIn(
            "Error al obtener datos desde la URL", str(context.exception))


    @patch('bicimad.UrlEMT.get_csv')
    @patch('pandas.read_csv', side_effect=FileNotFoundError("File not found"))
    def test_get_data_file_not_found_error(self, mock_read_csv, mock_get_csv):
        try:
            BiciMad.get_data(5, 22)
        except FileNotFoundError as e:
            self.assertIn("Error: El archivo", str(e))
        else:
            self.fail("FileNotFoundError no fue levantada cuando se esperaba.")


    @patch('bicimad.UrlEMT.get_csv')
    @patch('pandas.read_csv', 
           side_effect=pd.errors.ParserError("Parser error"))
    def test_get_data_parser_error(self, mock_read_csv, mock_get_csv):
        with self.assertRaises(pd.errors.ParserError) as context:
            BiciMad.get_data(5, 22)
            self.assertTrue(
                any('Error: Column not found' in elemento 
                    for elemento in str(context.exception)))
            
            
    @patch('bicimad.UrlEMT.get_csv')
    @patch('builtins.open', new_callable=mock_open)
    def test_empty_data_error(self, mock_open_func, mock_get_csv):
        """Test for EmptyDataError when the CSV file is empty"""
        # Simula que el método get_csv devuelve una ruta al archivo CSV
        mock_get_csv.return_value = 'dummy_path.csv'
        
        # Simula que el contenido del archivo CSV está vacío
        mock_open_func.return_value.read.return_value = ''
        
        # Comprueba que se lanza la excepción EmptyDataError
        with self.assertRaises(Exception) as context:
            test_object = BiciMad(1, 23)
        self.assertIn("No data found in the CSV file.", str(context.exception))


    @patch('bicimad.UrlEMT.get_csv')
    @patch('pandas.read_csv', side_effect=ValueError("Column not found"))
    def test_get_data_value_error(self, mock_read_csv, mock_get_csv):
        with self.assertRaises(ValueError) as context:
            BiciMad.get_data(5, 22)
            self.assertTrue(
                any('Error: No se pudo analizar el archivo CSV. '+
                    'Asegúrate de que esté bien formado.' in elemento 
                    for elemento in str(context.exception)))
                            

    @patch('bicimad.UrlEMT.get_csv')
    @patch('pandas.read_csv', side_effect=Exception("Unexpected error"))
    def test_get_data_generic_exception(self, mock_read_csv, mock_get_csv):
        with self.assertRaises(Exception) as context:
            BiciMad.get_data(5, 22)
            # Verificar el mensaje de la excepción
            self.assertTrue(
                any('Asegúrate de que las columnas especificadas'+
                    'existan en el archivo CSV.' in elemento 
                    for elemento in str(context.exception)))
                            

    def test_get_data_invalid_month(self):
        with self.assertRaises(ValueError):
            BiciMad.get_data(13, self.year)


    def test_get_data_invalid_year(self):
        with self.assertRaises(ValueError):
            BiciMad.get_data(self.month, 25)


    def test_get_data_connection_error(self):
        with patch('bicimad.UrlEMT.get_csv',
                   side_effect=ConnectionError("Failed to fetch data")):
            with self.assertRaises(ConnectionError):
                BiciMad.get_data(self.month, self.year)


    def test_resume(self):
        data = {
            'station_lock': ['A', 'A', 'B'],
            'trip_minutes': [30, 20, 50]
        }
        df = pd.DataFrame(data)
        self.bicimad._BiciMad__data = df
        result = self.bicimad.resume()
        self.assertEqual(result['total_uses'], 3)
        self.assertAlmostEqual(result['total_time'], 1.67, places=2)
        self.assertEqual(result['most_popular_station'], 'A')
        self.assertEqual(result['uses_from_most_popular'], 2)


    def test_bikes_not_locked_in_station(self):
        data = {
            'station_unlock': ['Station1', 'Station2', None],
            'station_lock': [None, 'Station2', None]
        }
        df = pd.DataFrame(data)
        self.bicimad._BiciMad__data = df
        result = self.bicimad.bikes_not_locked_in_station()
        self.assertEqual(result, 1)
        
        
    def test_fleet_1_bikes(self):
        data = {
            'station_lock': ['A', 'A', 'B'],
            'trip_minutes': [30, 20, 50],
            'fleet': ['1.0', '1.0', '2.0']
        }
        
        expected_result = pd.DataFrame({
            'station_lock': ['A', 'A'],
            'trip_minutes': [30, 20],
            'fleet': ['1.0', '1.0']
            })
        df = pd.DataFrame(data)
        self.bicimad._BiciMad__data = df
        result = self.bicimad.fleet_1_bikes()
        try:
            pd.testing.assert_frame_equal(result, expected_result)
        except AssertionError as e:
            raise Exception('Los dataframes no son iguales')


    def test_clean_valid(self):
        data = pd.DataFrame({
            'idBike': [1, None, 3, np.nan, 5, np.nan],
            'fleet': ['value1', None, 'value3', np.nan, 'value5', np.nan],
            'col3': ['data1', None, 'data3', np.nan, 'data5', np.nan]
        })
        df = pd.DataFrame(data)
        self.bicimad._BiciMad__data = df
        self.bicimad.clean()
        self.assertFalse(
            any(pd.isna(x) for x in self.bicimad.data['idBike'].tolist()))


    def test_day_time(self):
        data = {
            'fecha': pd.to_datetime([
                '2023-05-01', 
                '2023-05-01', 
                '2023-05-02']),
            'trip_minutes': [30, 45, 60]
        }
        df = pd.DataFrame(data)
        self.bicimad._BiciMad__data = df
        result = self.bicimad.day_time()
        self.assertEqual(result[pd.Timestamp('2023-05-01')], 75)
        self.assertEqual(result[pd.Timestamp('2023-05-02')], 60)


    def test_bar_diagram(self):
        series = pd.Series([10, 15, 20], 
                           index=pd.date_range('20230101', periods=3))
        with patch('matplotlib.pyplot.show') as mock_show:
            self.bicimad.bar_diagram(series)
            mock_show.assert_called_once()


    def test_weekday_time(self):
        data = {
            'fecha': pd.to_datetime(['2023-01-02', '2023-01-03']), 
            'trip_minutes': [120, 180]
        }
        df = pd.DataFrame(data)
        self.bicimad._BiciMad__data = df
        result = self.bicimad.weekday_time()
        self.assertEqual(result['Monday'], 2)  # 120 minutes / 60
        self.assertEqual(result['Tuesday'], 3)  # 180 minutes / 60
        
        
    def test_total_usage_day(self):
        # Datos de prueba
        data = {
            'fecha': pd.to_datetime([
                '2023-01-02', 
                '2023-01-02', 
                '2023-01-02', 
                '2023-01-03']),
            'trip_minutes': [120, 180, 60, 60]
        }
        df = pd.DataFrame(data)
        df.set_index('fecha', inplace=True)
        self.bicimad._BiciMad__data = df
        dates = pd.to_datetime(
            ['2023-01-02', '2023-01-03'], format='%Y-%m-%d').date
        expected_result = pd.Series(
            data=[3, 1],
            index=dates
        )
        result = self.bicimad.total_usage_day()
        try:
            pd.testing.assert_series_equal(result, expected_result)
        except AssertionError as e:
            raise Exception('Las Series no son iguales: ' + str(e))
        

    def test_usage_per_day_per_station(self):
        data = {
            'fecha': pd.to_datetime([
                '2023-05-01', 
                '2023-05-01', 
                '2023-05-02']),
            'station_unlock': ['Station1', 'Station1', 'Station2']
        }
        df = pd.DataFrame(data)
        df.set_index('fecha', inplace=True)
        self.bicimad._BiciMad__data = df
        result = self.bicimad.usage_per_day_per_station()
        self.assertEqual(result[(pd.Timestamp('2023-05-01'), 'Station1')], 2)
        self.assertEqual(result[(pd.Timestamp('2023-05-02'), 'Station2')], 1)


    def test_most_popular_stations(self):
        data = {
            'address_unlock': ['Address1', 'Address1', 'Address2']
        }
        df = pd.DataFrame(data)
        self.bicimad._BiciMad__data = df
        result = self.bicimad.most_popular_stations()
        self.assertIn('Address1', result)


    def test_usage_from_most_popular_station(self):
        data = {
            'address_unlock': ['Address1', 'Address1', 'Address2']
        }
        df = pd.DataFrame(data)
        self.bicimad._BiciMad__data = df
        with patch.object(BiciMad, 
                          'most_popular_stations', return_value={'Address1'}):
            result = self.bicimad.usage_from_most_popular_station()
            self.assertEqual(result, 2)
            
            
    def test_len(self):
        obj_to_check_lenght = BiciMad(2, 22)
        self.assertEqual(280375, len(obj_to_check_lenght))
        
            
    def test_str(self):
        # Crear un objeto de BiciMad con datos de prueba
        obj_to_print = BiciMad(2, 22)
        generated_str = str(obj_to_print)
        # self.assertIn('Reporte de Datos para 2/22', generated_str)
        self.assertIn('Reporte de Datos para 2/22\nEl DataFrame contiene '
                      '280375 registros con estas columnas:idBike, fleet, '
                      'trip_minutes, geolocation_unlock, address_unlock, '
                      'unlock_date, locktype, unlocktype, geolocation_lock, '
                      'address_lock, lock_date, station_unlock, '
                      'unlock_station_name, station_lock, lock_station_name.\n'
                      'Vista previa de los primeros y últimos registros:\n',
            generated_str
        )

if __name__ == '__main__':
    unittest.main()
