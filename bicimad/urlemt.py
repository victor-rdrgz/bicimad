import io
import re
import urllib
import zipfile

import requests


def get_links(html: str) -> list:
    '''
    Extracts and returns a list of links from the provided HTML text 
    that match a specific pattern.

    Parameters:
    - html (str): The HTML content as a string from which links 
      will be extracted.
    Returns:
    - list: A list of unique links matching the pattern found in 
      the HTML content.
    Exceptions:
    - TypeError: Raised if the provided argument is not a string.
    '''
    if not isinstance(html, str):
        raise TypeError(
            "html argument must be a text string.")
    # Find all matches of the pattern in the HTML.
    pattern = (
    r'href="(/getattachment/[a-zA-Z0-9-]*/trips_\d{2}_\d{2}_[^"]*-csv\.aspx)"')
    
    return list(set(re.findall(pattern, html)))


class UrlEMT():
    EMT = 'https://opendata.emtmadrid.es/'
    GENERAL = '/Datos-estaticos/Datos-generales-(1)'
    
    
    def __init__(self):
      '''Builds the object with the links from Bicimad URL'''
      self.__enlaces = UrlEMT.select_valid_urls()


    @staticmethod
    def select_valid_urls() -> list:
        '''
        Retrieves and returns a list of valid URLs from the EMT server.

        This static method performs an HTTP request to the EMT server to obtain 
        valid URLs and checks their status. If the response status code from the 
        server is not 200, or if there is a connection issue, an exception is 
        raised.
        Returns:
        - list: A list of valid URLs with their corresponding indices.
        Exceptions:
        - ConnectionError: Raised if the connection to the server fails or if 
        the server returns a non-200 status code.
        - TimeoutError: If the request to validate the URLs takes too long.
        '''
        try:
            # Make the HTTP request and check the status code
            r = urllib.request.urlopen(UrlEMT.EMT + UrlEMT.GENERAL)
            if r.getcode() != 200:
                raise ConnectionError(f"Status code: {r.getcode()}")
            # Getting valid links from HTML
            links = get_links(r.read().decode("utf-8"))
            # Check that the URLs obtained are valid
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
                f"Error trying to connect with the server. {e}")

    def get_url(self, month: int, year: int) -> str:
        """
        Returns the URL string corresponding to the provided month/year.

        Parameters:
        - year (int): Year as an integer (expected values: 21, 22, or 23).
        - month (int): Month as an integer (between 1 and 12).

        Returns:
        - str: The URL corresponding to the month and year if it exists.

        Exceptions:
        - ValueError: If the year or month are not within valid ranges or
          if a URL for that combination does not exist.
        - KeyError: If the year and month are within valid ranges but the URL 
          doesn't exist.
        """
        try:
            # Check for valid range for year and month
            if year not in range(21, 24):
                raise ValueError("Year must be between 21 and 23.")

            if month not in range(1, 13):
                raise ValueError("Month must be between 1 and 12.")
            if (year == 23 and month in range(3,13) or
            year == 21 and month in range(1,7)):
                raise ValueError("There is no data from march 2023")
        except ValueError:
            # If the year and month combination is not within the allowed 
            # values, raise an exception.
            raise ValueError(
                "There is no data for the provided month/year combination."
            )
        try:
            return self.__enlaces[year, month]
        except KeyError:
            # If the combination of year and month does not have a registered 
            # link, raise an exception
            raise KeyError("There is no data for the provided" +
                           "month/year combination.")


    def get_csv(self, month: int, year: int) -> str:
        '''
        Instance method that accepts integer arguments `month` and `year` and 
        returns a CSV file corresponding to the given month and year.

        Parameters:
        - month (int): Month as an integer (between 1 and 12).
        - year (int): Year as an integer (expected values: 21, 22, or 23).

        Returns:
        - io.StringIO: A StringIO object containing the CSV content.

        Exceptions:
        - ConnectionError: If there is an issue downloading the ZIP file.
        - FileNotFoundError: If no CSV file is found in the ZIP or if the ZIP 
        is not valid.
        - ValueError: If the CSV file cannot be read (e.g., it is empty).
        - Exception: For any other unexpected errors, with a generic message.
        '''
        url = UrlEMT.EMT + self.get_url(month, year)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error downloading zip file: {e}")
        try:
            # Unzip ZIP file in memory
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                # List file names in ZIP
                file_names = z.namelist()
                if not file_names:
                    raise FileNotFoundError(
                        "No CSV file was found in the ZIP.")
                csv_file = [file for file in file_names 
                            if file.endswith('.csv')]
                with z.open(csv_file[0]) as csv_file:
                    # Reads the content of the CSV into a TextIO object.
                    # Converts to string and creates a TextIO.
                    csv_content = io.StringIO(
                        csv_file.read().decode('utf-8'))
                    if csv_content.getvalue()=='':
                        raise ValueError("Could not read the CSV file")
            return csv_content
        except zipfile.BadZipFile:
            raise FileNotFoundError(
                'Downloaded file is not a valid ZIP')
        except ValueError as e:
            raise ValueError(e)
        except FileNotFoundError as e:
            raise FileNotFoundError(e)
        except Exception as e:
            raise Exception("Unknown error. Stropping execution")


    def __str__(self):
        return (
            "\n".join([f"{key}: {link}" 
                for key, link in self.__enlaces.items()]))