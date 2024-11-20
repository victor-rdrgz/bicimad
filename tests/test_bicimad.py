import unittest
from unittest.mock import patch, MagicMock, mock_open

from pandas.errors import EmptyDataError, ParserError
import pandas as pd
import numpy as np
from bicimad import BiciMad

class TestBiciMad(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a BiciMad instance only once for all tests"""
        cls.bicimad = BiciMad(2, 22)


    @patch('bicimad.BiciMad.clean')
    @patch('bicimad.BiciMad.get_data')
    def test_init_calls_get_data_and_clean(self, mock_get_data, mock_clean):
        # Checks that the attributes were initialized correctly
        self.assertEqual(self.bicimad._BiciMad__month, 2)
        self.assertEqual(self.bicimad._BiciMad__year, 22)
        self.assertIsInstance(self.bicimad._BiciMad__data, pd.DataFrame)
                
                
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
            BiciMad.get_data(
                self.bicimad._BiciMad__month, self.bicimad._BiciMad__year)
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
            BiciMad(1, 23)
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
                            

    @patch('pandas.read_csv', side_effect=Exception("Unexpected error"))
    def test_get_data_generic_exception(self, mock_read_csv):
        with self.assertRaises(Exception) as context:
            BiciMad.get_data(2, 22)
        self.assertIn('Unexpected error', str(context.exception))
                            

    def test_get_data_invalid_month(self):
        with self.assertRaises(ValueError) as context:
            result = BiciMad.get_data(13, self.bicimad._BiciMad__year)
            self.assertIsInstance(result, pd.DataFrame)
            self.assertIn(
                "Month has to be between 1 and 12", str(context.exception))


    def test_get_data_invalid_year(self):
        with self.assertRaises(ValueError) as context:
            result = BiciMad.get_data(self.bicimad._BiciMad__month, 20)
            self.assertIsInstance(result, pd.DataFrame)
            self.assertIn(
                "Year has to be between 21 and 23", str(context.exception))
            
            
    @patch('bicimad.UrlEMT.get_csv', return_value='dummy_path.csv')
    @patch('pandas.read_csv', side_effect=KeyError("missing_column"))
    def test_get_data_key_error(self, mock_read_csv, mock_get_csv):
        '''Tests when missing column in CSV file'''
        with self.assertRaises(Exception) as context:
            BiciMad.get_data(5, 22)
        
        # Verifica que el mensaje de la excepción contiene el texto esperado
        self.assertIn(
            "Column not found in the CSV file: 'missing_column'", 
            str(context.exception))


    def test_resume(self):
        result = self.bicimad.resume()
        self.assertEqual(result['total_uses'], 280375)
        self.assertAlmostEqual(result['total_time'], 95035.796875)
        self.assertEqual(result['most_popular_station'], '43')
        self.assertEqual(result['uses_from_most_popular'], 3329)


    def test_bikes_not_locked_in_station(self):
        result = self.bicimad.bikes_not_locked_in_station()
        self.assertEqual(result, 711)
        
        
    def test_fleet_1_bikes(self):
        # Mockear la función estática `get_data` para devolver un DataFrame controlado
        with patch('bicimad.BiciMad.get_data', return_value=pd.DataFrame({
            'fleet': ['1.0', '2.0', '1.0', '3.0'],  # Dos valores de '1.0'
            'idBike': ['A', 'B', 'C', 'D'],  # Identificadores de bicicleta
            'trip_minutes': [30, 20, 25, 15]  # Duración del viaje
        })):
            # Crear el objeto `BiciMad` con los datos mockeados
            bicimad = BiciMad(5, 22)

            # Llamar a la función a probar
            result = bicimad.fleet_1_bikes()

            # Crear el DataFrame esperado
            expected_df = pd.DataFrame({
                'fleet': ['1.0', '1.0'],
                'idBike': ['A', 'C'],
                'trip_minutes': [30, 25]
            })
            expected_df = expected_df.astype(
                {'fleet': 'string', 
                 'idBike': 'string'})
            # Reset the index to ensure the filtered DataFrame has a sequential
            # index matching the expected DataFrame for comparison.
            expected_df.reset_index(drop=True, inplace=True)
            result.reset_index(drop=True, inplace =True)
            # Check result with expected_result
            pd.testing.assert_frame_equal(result,expected_df)


    def test_clean_valid(self):
        with patch('bicimad.BiciMad.get_data', return_value=pd.DataFrame({
            'idBike': [1, None, 3, np.nan, 5, np.nan],
            'fleet': ['value1', None, 'value3', np.nan, 'value5', np.nan],
            'col3': ['data1', None, 'data3', np.nan, 'data5', np.nan]
        })):
            bicimad_obj = BiciMad(5, 22)
            bicimad_obj.clean()
            self.assertFalse(
                any(pd.isna(x) for x in bicimad_obj.data['idBike'].tolist()))


    def test_day_time(self):
        with patch('bicimad.BiciMad.get_data', return_value=pd.DataFrame(
        data = {
            'fecha': pd.to_datetime([
                '2023-05-01', 
                '2023-05-01', 
                '2023-05-02']),
            'trip_minutes': [30, 45, 60],
            'fleet': ['1.0', '1.0', '2.0'],
            'idBike': [4,5,6]
        })):
            bicimad_obj = BiciMad(5, 22)
            result = bicimad_obj.day_time()
            self.assertEqual(result[pd.Timestamp('2023-05-01')], 75)
            self.assertEqual(result[pd.Timestamp('2023-05-02')], 60)


    def test_bar_diagram(self):
        series = pd.Series([10, 15, 20], 
                           index=pd.date_range('20230101', periods=3))
        with patch('matplotlib.pyplot.show') as mock_show:
            self.bicimad.bar_diagram(series)
            mock_show.assert_called_once()


    def test_weekday_time(self):
        with patch('bicimad.BiciMad.get_data', return_value=pd.DataFrame({
            'fecha': pd.to_datetime(['2023-01-02', '2023-01-03','2023-01-03']), 
            'trip_minutes': [120, 180, 240],
            'fleet': ['1.0', '1.0', '2.0'],
            'idBike': [4,5,6]
            })):
            bicimad_obj = BiciMad(2,22)
            result = bicimad_obj.weekday_time()
            self.assertEqual(result['Monday'], 2)  # 120 minutes / 60
            self.assertEqual(result['Tuesday'], 7)  # 420 minutes / 60
        
        
    def test_total_usage_day(self):
        # Datos de prueba
        with patch('bicimad.BiciMad.get_data', return_value=pd.DataFrame({
            'fecha': pd.to_datetime([
                '2023-01-02', 
                '2023-01-02', 
                '2023-01-02', 
                '2023-01-03']),
            'trip_minutes': [120, 180, 60, 60],
            'fleet': ['1.0', '1.0', '2.0','3.0'],
            'idBike': [4,5,6,7],
            
        }).set_index('fecha')):
            bicimad_obj = BiciMad(2,22)
            dates = pd.to_datetime(
                ['2023-01-02', '2023-01-03'], format='%Y-%m-%d').date
            expected_result = pd.Series(
                data=[3, 1],
                index=dates
            )
            result = bicimad_obj.total_usage_day()
            try:
                pd.testing.assert_series_equal(result, expected_result)
            except AssertionError as e:
                raise Exception('Las Series no son iguales: ' + str(e))
        

    def test_usage_per_day_per_station(self):
         with patch('bicimad.BiciMad.get_data', return_value=pd.DataFrame({
            'fecha': pd.to_datetime([
                '2023-05-01', 
                '2023-05-01', 
                '2023-05-02']),
            'station_unlock': ['Station1', 'Station1', 'Station2'],
            'fleet': ['1.0', '1.0', '2.0'],
            'idBike': [4,5,6],
        }).set_index('fecha')):
            bicimad_obj = BiciMad(2,22)
            result = bicimad_obj.usage_per_day_per_station()
            self.assertEqual(
                result[(pd.Timestamp('2023-05-01'), 'Station1')], 2)
            self.assertEqual(
                result[(pd.Timestamp('2023-05-02'), 'Station2')], 1)


    def test_most_popular_stations(self):
        with patch('bicimad.BiciMad.get_data', return_value=pd.DataFrame({
            'fecha': pd.to_datetime([
                '2023-05-01', 
                '2023-05-01', 
                '2023-05-02']),
            'station_unlock': ['Station1', 'Station1', 'Station2'],
            'fleet': ['1.0', '1.0', '2.0'],
            'idBike': [4,5,6],
            'address_unlock': ['Address1', 'Address1', 'Address2']
        }).set_index('fecha')):
            bicimad_obj = BiciMad(2,22)
            result = bicimad_obj.most_popular_stations()
            self.assertIn('Address1', result)


    def test_usage_from_most_popular_station(self):
        with patch('bicimad.BiciMad.get_data', return_value=pd.DataFrame({
            'fecha': pd.to_datetime([
                '2023-05-01', 
                '2023-05-01', 
                '2023-05-02']),
            'station_unlock': ['Station1', 'Station1', 'Station2'],
            'fleet': ['1.0', '1.0', '2.0'],
            'idBike': [4,5,6],
            'address_unlock': ['Address1', 'Address1', 'Address2']
        }).set_index('fecha')):
            bicimad_obj = BiciMad(2,22)
            result = bicimad_obj.usage_from_most_popular_station()
            self.assertEqual(result, 2)
            
            
    def test_len(self):
        self.assertEqual(280375, len(self.bicimad))
        
            
    def test_str(self):
        generated_str = str(self.bicimad)
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
