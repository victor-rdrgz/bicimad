import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from bicimad.urlemt import UrlEMT


class BiciMad():
    def __init__(self, month: int, year: int) -> None:
        '''
        Class Constructor. Gets renting data from a given month/year pair
        Cleans data according to specification
        '''
        self.__month = month
        self.__year = year
        self.__data = BiciMad.get_data(month, year)
        self.clean()

    @staticmethod
    def get_data(month: int, year: int):
        '''
        Método estático que acepta los argumentos de tipo entero
        month y year y devuelve un objeto de tipo DataFrame
        con los datos de uso correspondientes al mes y año indicados.

        Parámetros:
        - month (int): Mes como número entero (1-12).
        - year (int): Año como número entero (por ejemplo, 2023).

        Retorno:
        - pd.DataFrame: DataFrame que contiene los datos filtrados.

        Excepciones:
        - ValueError: Si el mes o año no son válidos.
        - KeyError: Si alguna de las columnas especificadas no existe en el
                    DataFrame.
        '''
        # Comprobación de rango válido para año y mes
        if month not in range(1, 13):
            raise ValueError("El año debe estar entre 21 y 23.")
        if year not in range(21, 24):
            raise ValueError("El mes debe estar entre 1 y 12.")

        COLUMNS_TO_PRESERVE = [ 'fecha', 'idBike', 'fleet', 'trip_minutes',
            'geolocation_unlock', 'address_unlock', 'unlock_date',
            'locktype', 'unlocktype', 'geolocation_lock',
            'address_lock', 'lock_date', 'station_unlock',
            'unlock_station_name','station_lock',
            'lock_station_name']

        url_manager = UrlEMT()
        try:
            # obtenemos el csv haciendo uso de la clase UrlEMT()
            csv = url_manager.get_csv(month, year)
        except Exception as e:
            raise ConnectionError(f"Error al obtener datos desde la URL: {e}")

        try:
            # Convierte el csv en un DataFrame
            df = pd.read_csv(
                csv ,
                sep=';',
                quotechar="'",
                index_col='fecha',
                parse_dates = ['fecha', 'unlock_date', 'lock_date'],
                usecols= COLUMNS_TO_PRESERVE)
            return df
        except FileNotFoundError:
          print(f"Error: El archivo {csv} no se encuentra.")
        except pd.errors.ParserError:
            print(f"Error: No se pudo analizar el archivo CSV. Asegúrate de que"
                    "esté bien formado.")
        except ValueError as e:
            print(f"Error: {e}. Asegúrate de que las columnas especificadas "
                   "existan en el archivo CSV.")
        except Exception as e:
            print(f"Se ha producido un error inesperado: {e}")

    @property
    def data(self):
        '''
        Método decorado con el decorador @property para acceder
        al atributo que representa los datos de uso. El atributo
        ha de llamarse igual.

        Retorno:
        - Los datos almacenados en el atributo privado __data.
        '''
        return self.__data


    def clean(self):
        '''
        Método de instancia que se encarga de realizar la limpieza
        y transformación del dataframe que representa los datos.
        Modifica el dataframe y no devuelve nada. Realiza las
        siguientes tareas:
        '''
        # Reemplazar None y NaN por np.nan
        self.__data.replace([None, 'nan'], np.nan, inplace=True)
        # Eliminar filas donde todos los elementos son NaN
        self.__data.dropna(how='all', inplace=True)
        # Convertir columnas a tipo string según enunciado y EXTRA
        # convertir el resto de columnas a tipos de datos más adecuados.

        ################### Se ahorra un 64% de memoria ###################
        data_types={
          'idBike': 'string',
          'fleet': 'string',
        }
        self.__data = self.__data.astype(data_types)


    def resume(self):
      '''
      Método de instancia que devuelve un objeto de tipo Series con las
      siguientes restricciones:
        - el índice está formado con las etiquetas: 'year', 'month',
          'total_uses', 'total_time', 'most_popular_station',
          'uses_from_most_popular'
        - los valores son: el año, el mes, el total de usos en dicho mes, el
           total de horas en dicho mes, el conjunto de estaciones de bloqueo con
            mayor número de usos y el número de usos de dichas estaciones.
      '''
      # Calcular el total de usos en el mes
      total_uses = len(self.data)

      # Calcular el total de tiempo de uso en horas
      # (sumando los minutos y convirtiendo a horas)
      total_time = self.data['trip_minutes'].sum() / 60

      # Encontrar la estación de bloqueo más popular
      most_popular_station = self.data['station_lock'].mode().iloc[0]

      # Calcular el número de usos de la estación de bloqueo más popular
      uses_from_most_popular = (
          self.data['station_lock'] == most_popular_station).sum()

      # Crear y devolver la serie con el formato solicitado
      return pd.Series({
          'year': self.__year,
          'month': self.__month,
          'total_uses': total_uses,
          'total_time': total_time,
          'most_popular_station': most_popular_station,
          'uses_from_most_popular': uses_from_most_popular
      })


    def bikes_not_locked_in_station(self) -> int:
      '''C1: Analyzes data looking for how many bikes have been unlocked
      in an station and not blocked in one of them'''
      not_locked_bikes = (
          self.data[self.data['station_unlock'].notnull() &
          self.data['station_lock'].isnull()].shape[0])
      return not_locked_bikes


    def fleet_1_bikes(self) -> pd.DataFrame:
      '''C2: Analyzes data looking for how many bikes are in fleet 1'''
      return self.data[self.data['fleet'] == '1.0']


    def day_time(self) -> pd.Series:
      '''C3: Calculates how many hours have all the bikes been
      rented divided per day'''
      rent_by_day = self.data.groupby('fecha')['trip_minutes'].sum()

      return rent_by_day

    @staticmethod
    def bar_diagram(serie: pd.Series) -> None:
      '''C3: Create a chart with the data from a series that contains the number
       of daily rentals for a month.'''
      ax = serie.plot(
          kind='bar',
          color='skyblue',
          figsize=(20, 8),
          xlabel='Fecha',
          ylabel='Horas de Uso',
          fontsize=18)
      plt.title('Horas Totales de Uso de Bicicletas por Día', fontsize=24)
      plt.xticks(rotation=45, ha='right')
      plt.tight_layout()
      plt.show()


    def weekday_time(self: "Bicimad") -> pd.Series:
      '''C4: Calculates how many hours have all the bikes been rented
      divided per day of the week'''
      hoursOfRental = self.day_time().to_frame()
      hoursOfRental.rename(columns={'trip_minutes': 'trip_hours'}, inplace=True)
      hoursOfRental['week_day'] = hoursOfRental.index.day_name()
      hoursOfRental = (
          hoursOfRental.groupby('week_day')['trip_hours'].sum().astype(int))
      week_days_order = [
          'Monday', 'Tuesday', 'Wednesday',
          'Thursday', 'Friday', 'Saturday', 'Sunday']
      hoursOfRental = hoursOfRental.reindex(week_days_order)
      return hoursOfRental


    def total_usage_day(self: "Bicimad") -> pd.Series:
      '''C5: Calculate the total number of uses per day'''
      return self.data.groupby(self.data.index.date).size()


    def usage_per_day_per_station(self: "Bicimad") -> pd.DataFrame:
      '''C6: Calculate the total number of uses per day and unlock station'''
      return self.data.groupby([pd.Grouper(freq='1D'), 'station_unlock']).size()


    def most_popular_stations(self: "BiciMad") -> set:
      '''C7: Calculate the total number of uses per day and unlock station'''
      value_counts = self.data.value_counts('address_unlock')
      max_frequency = value_counts.max()
      return set(value_counts[value_counts==max_frequency].index)


    def usage_from_most_popular_station(self: "BiciMad") -> int:
      '''C8: Calculate station with the max number of uses per day'''
      set_of_most_popular_stations = self.most_popular_stations()
      return self.data['address_unlock'].isin(set_of_most_popular_stations).sum()


    def __len__(self):
      return len(self.data)


    def __str__(self):
      print(f"Mes: {self.__month}, Año: {self.__year}")
      print(self.data)