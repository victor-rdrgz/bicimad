import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from bicimad.urlemt import UrlEMT


class BiciMad():
    # Columns and DataTypes to make conversion
    COLUMNS_TYPE = {
      'idBike': 'string',
      'fleet': 'string',
      'trip_minutes': 'float32',
      'geolocation_unlock': 'string',
      'address_unlock': 'string',
      'locktype': 'string',
      'unlocktype': 'string',
      'geolocation_lock': 'string',
      'address_lock': 'string',
      'station_unlock': 'string',
      'unlock_station_name': 'string',
      'station_lock': 'string',
      'lock_station_name': 'string'
    }
    
    # Columns we are interested in from the total of csv file
    COLUMNS_TO_PRESERVE = [ 'fecha', 'idBike', 'fleet', 'trip_minutes',
      'geolocation_unlock', 'address_unlock', 'unlock_date',
      'locktype', 'unlocktype', 'geolocation_lock',
      'address_lock', 'lock_date', 'station_unlock',
      'unlock_station_name','station_lock',
      'lock_station_name']

  
    def __init__(self, month: int, year: int) -> None:
        '''
        Initializes an instance of the BiciMad class by loading and cleaning
        bicycle renting data for a specified month and year. This constructor 
        sets the instance variables for month, year, and data used throughout 
        the instance's lifecycle.

        Parameters:
        - month (int): The month for data retrieval, integer (1-12).
        - year (int): The year for data retrieval. Valid values are typically
          recent years such as 21, 22, or 23, representing 2021, 2022, and 2023

        This method automatically fetches the renting data by invoking the 
        static method `get_data` and cleans it using the `clean` method. This
        ensures that the data is ready for use as soon as an instance is 
        created.

        Raises:
        - ValueError: If the `month` or `year` are out of expected range.
        - ConnectionError: If there is an issue with downloading the data.
        - FileNotFoundError: If no data file is found for the given 
            month and year.
        - Exception: For any uncaught errors during data processing.
        '''

        self.__month = month
        self.__year = year
        self.__data = BiciMad.get_data(month, year)
        self.clean()

    @staticmethod
    def get_data(month: int, year: int):
      '''
      Retrieves and returns a DataFrame containing bicycle usage data 
      for a specified month and year from an external source.

      This method fetches the data from a CSV file located via an URL that is
      derived from the month and year parameters. It performs validation 
      checks on the month and year, processes the CSV to a DataFrame applying 
      specified filters and data types, and ensures that the data frame is 
      properly formatted with the correct columns.

      Parameters:
      - month (int): The month for which data is required, valid values are
          from 1 to 12.
      - year (int): The year for which data is required, expected to be a 
          two-digit integer like 21, 22, or 23, corresponding to the years 
          2021 to 2023.

      Returns:
      - pd.DataFrame: A DataFrame populated with the data from the CSV file,
        structured according to the predefined columns and data types.

      Raises:
      - ValueError: If `month` is not within 1-12 or `year` is not within the 
            valid range.
      - ConnectionError: If there is a failure in retrieving the CSV file 
            from the URL.
      - FileNotFoundError: If the CSV file does not exist 
            in the downloaded ZIP.
      - pd.errors.EmptyDataError: If the CSV file is 
            found but contains no data.
      - pd.errors.ParserError: If there are issues parsing the CSV file.
      - KeyError: If an expected column is missing from the CSV file.
      - Exception: For any other unhandled errors that occur during processing.
        '''
      # Comprobación de rango válido para año y mes
      if month not in range(1, 13):
          raise ValueError("Month has to be between 1 and 12")
      if year not in range(21, 24):
          raise ValueError("Year has to be between 21 and 23")

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
              dtype=BiciMad.COLUMNS_TYPE,
              parse_dates = ['fecha', 'unlock_date', 'lock_date'],
              usecols= BiciMad.COLUMNS_TO_PRESERVE)
          return df
      except FileNotFoundError:
        raise FileNotFoundError(f"Error: El archivo {csv} no se encuentra.")
      except pd.errors.EmptyDataError:
        raise Exception("No data found in the CSV file.")
      except pd.errors.ParserError:
        raise pd.errors.ParserError(f"Error: No se pudo analizar el archivo"+ 
          "CSV. Asegúrate de que esté bien formado.")
      except ValueError as e:
        raise ValueError(f"Error: {e}. Asegúrate de que las columnas "
                "especificadas existan en el archivo CSV.")
      except KeyError as e:
        raise Exception(f"Column not found in the CSV file: {e}")
      except Exception as e:
        raise Exception(f"Unexpected error {e}")

    @property
    def data(self):
        '''
        Provides access to the private attribute __data which contains the 
        bicycle usage data loaded and cleaned by this instance.

        This property allows read-only access to the bicycle usage data,
        ensuring that the data cannot be modified directly, thus maintaining
        the integrity of the data throughout the lifecycle of the instance.

        Returns:
        - pd.DataFrame: A DataFrame containing the cleaned and structured
          bicycle usage data. This data includes various details about each
          bicycle rent transaction such as start and end times, locations,
          and other relevant metrics.

        Usage:
        To access the bicycle usage data of an instance of BiciMad:
        >>> bicimad_instance = BiciMad(5, 22)
        >>> data = bicimad_instance.data
        The variable `data` will now hold the DataFrame with the data for 
          May 2022.
        '''
        return self.__data


    def clean(self):
      '''
      Cleans and transforms the data within the DataFrame stored in this 
      instance. This method standardizes the format and prepares the data for 
      analysis by performing several key operations:

      1. Replaces all instances of `None` and the string 'nan' with `np.nan`
        to standardize missing values.
      2. Removes any rows where all elements are NaN, which helps to clean up
        the dataset by eliminating completely empty records.

      The cleaning process is crucial for ensuring that the data is in a 
      suitable format for analysis, free from inconsistencies, and optimized 
      for performance.

      This method modifies the `__data` attribute in place and does not return
      a value.
      '''
      # Reemplazar None y NaN por np.nan
      self.__data.replace([None, 'nan'], np.nan, inplace=True)
      # Eliminar filas donde todos los elementos son NaN
      self.__data.dropna(how='all', inplace=True)


    def resume(self):
      '''
      Generates a summary of bicycle usage statistics for the given month and 
      year. This method aggregates key statistics from the cleaned data set and 
      provides an overview of the bicycle usage metrics.

      Returns:
      - pd.Series: A Series object with the following indices and corresponding 
      values:
          - 'year': The year of the data, indicating the temporal context 
              of the summary.
          - 'month': The month of the data, specifying when the data 
              was collected.
          - 'total_uses': The total number of bicycle uses recorded 
              in the month.
          - 'total_time': The total time for which bicycles were used 
              during the month, calculated in hours.
          - 'most_popular_station': The bicycle station with the 
              highest number of uses, indicating a hotspot of bicycle activity.
          - 'uses_from_most_popular': The number of times bicycles were used 
              from the most popular station, providing insight into station
              traffic.

      The method calculates the total number of uses and total usage time from 
      the 'trip_minutes' column, identifies the most frequently used station, 
      and counts how many times bicycles were used from that station.
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
      '''C3: Create a chart with the data from a series that 
      contains the number of daily rentals for a month.'''
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


    def weekday_time(self) -> pd.Series:
      '''C4: Calculates how many hours have all the bikes been rented
      divided per day of the week'''
      hoursOfRental = self.day_time().to_frame()
      hoursOfRental.rename(
        columns={'trip_minutes': 'trip_hours'}, inplace=True)
      hoursOfRental['trip_hours'] = hoursOfRental['trip_hours']/60
      hoursOfRental['week_day'] = hoursOfRental.index.day_name()
      hoursOfRental = (
          hoursOfRental.groupby('week_day')['trip_hours'].sum().astype(int))
      week_days_order = [
          'Monday', 'Tuesday', 'Wednesday',
          'Thursday', 'Friday', 'Saturday', 'Sunday']
      hoursOfRental = hoursOfRental.reindex(week_days_order)
      return hoursOfRental


    def total_usage_day(self) -> pd.Series:
      '''C5: Calculate the total number of uses per day'''
      return self.data.groupby(self.data.index.date).size()


    def usage_per_day_per_station(self) -> pd.DataFrame:
      '''C6: Calculate the total number of uses per day and unlock station'''
      return self.data.groupby(
        [pd.Grouper(freq='1D'), 'station_unlock']).size()


    def most_popular_stations(self: "BiciMad") -> set:
      '''C7: Calculate the total number of uses per day and unlock station'''
      value_counts = self.data.value_counts('address_unlock')
      max_frequency = value_counts.max()
      return set(value_counts[value_counts==max_frequency].index)


    def usage_from_most_popular_station(self: "BiciMad") -> int:
      '''C8: Calculate station with the max number of uses per day'''
      set_of_most_popular_stations = self.most_popular_stations()
      return self.data['address_unlock'].isin(
        set_of_most_popular_stations).sum()


    def __len__(self):
      '''
      Returns the number of entries in the DataFrame stored in this instance.

      This method overrides the built-in Python `__len__()` method to provide a 
      custom implementation that directly corresponds to the number of records 
      in the DataFrame managed by this instance. It allows the use of Python's 
      built-in `len()` functionto get the count of bicycle usage records loaded
      and cleaned by this instance.

      Returns:
      int: The total number of records in the DataFrame.
      '''
      return len(self.data)


    def __str__(self):
      '''
       Provides a string representation of this BiciMad instance, showcasing
      the data context and a preview of the dataset.

      This method overrides the built-in Python `__str__()` method to provide  
      a custom string representation of the BiciMad instance. It includes a 
      headerwith the month and year of the data, a description of the DataFrame 
      including its size and the columns it contains, and a preview showing the 
      first and last three records.

      Returns:
      str: A formatted string that combines a header, data description, and a 
          preview of the DataFrame's contents.
      '''
      header = f"Reporte de Datos para {self.__month}/{self.__year}"
      
      data_description = (
          f"El DataFrame contiene {len(self)} registros con estas columnas:"
          f"{', '.join(self.data.columns)}."
      )
      preview = "Vista previa de los primeros y últimos registros:\n"
      preview += str(self.data.head(3)) + "\n...\n" + str(self.data.tail(3))
      
      # Juntamos todo en un solo string para el output
      return f"{header}\n{data_description}\n{preview}"