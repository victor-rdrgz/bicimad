import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from bicimad.bicimad import BiciMad

class TestBiciMad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.month = 5  # Mes de prueba
        cls.year = 2023  # Año de prueba
        # Crear un DataFrame de prueba
        cls.test_data = pd.DataFrame({
            'fecha': pd.date_range(start=f'{cls.year}-{cls.month}-01', periods=4, freq='D'),
            'idBike': ['101', '102', '103', '104'],
            'fleet': ['1.0', '2.0', '1.0', '2.0'],
            'trip_minutes': [45, 30, 35, 40],
            'station_lock': ['station1', 'station2', 'station3', 'station1'],
        })

        # Patching the get_data static method to return the test data
        cls.get_data_patch = patch('bicimad.bicimad.BiciMad.get_data', return_value=cls.test_data)
        cls.mock_get_data = cls.get_data_patch.start()

    @classmethod
    def tearDownClass(cls):
        print("Limpiando después de los tests")
        # Stop the patcher
        cls.get_data_patch.stop()

    def setUp(self):
        # Instanciando BiciMad con los valores configurados en setUpClass
        self.bicimad = BiciMad(self.month, self.year)

    def test_bicimad_initialization(self):
        """ Prueba que verifica si la inicialización es correcta """
        self.assertEqual(self.bicimad._BiciMad__month, self.month)
        self.assertEqual(self.bicimad._BiciMad__year, self.year)
        self.assertTrue(not self.bicimad._BiciMad__data.empty)

    def test_day_time_computation(self):
        """ Prueba que verifica si la computación de tiempo por día es correcta """
        result = self.bicimad.day_time()
        expected = pd.Series(
            [45, 30, 35, 40],
            index=pd.to_datetime(['2023-05-01', '2023-05-02', '2023-05-03', '2023-05-04'])
        )
        pd.testing.assert_series_equal(result, expected)

    def test_clean_data(self):
        """ Prueba el método clean para verificar si maneja correctamente los valores NaN """
        self.bicimad._BiciMad__data.loc[0, 'trip_minutes'] = np.nan
        self.bicimad.clean()
        self.assertTrue(pd.notna(self.bicimad._BiciMad__data['trip_minutes']).all())

if __name__ == '__main__':
    unittest.main()
