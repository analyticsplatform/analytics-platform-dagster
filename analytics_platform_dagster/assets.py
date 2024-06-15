import json
import requests
import duckdb
import pandas as pd
import geopandas as gpd
import zipfile
import tempfile
import os

from shapely.ops import transform
from loguru import logger
from dagster import asset


@asset
def dbt_trade_barriers():
    # Get data from api and create dataframe
    url = 'https://data.api.trade.gov.uk/v1/datasets/market-barriers/versions/latest/data?format=json'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data['barriers'])

    # Create a connection to a persistent DuckDB database file named "data"
    con = duckdb.connect('data.duckdb')

    # Create a table and insert the data
    con.execute('CREATE TABLE IF NOT EXISTS trade_barriers AS SELECT * FROM df')
    print("Data stored in the 'trade_barriers' table.")


@asset()
def ea_flood_areas():
    # Get data from api and create dataframe
    url = 'https://environment.data.gov.uk/flood-monitoring/id/floodAreas?_limit=9999'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data['items'])

    # Create a connection to a persistent DuckDB database file named "data"
    con = duckdb.connect('data.duckdb')

    # Create a table and insert the data
    con.execute('CREATE TABLE IF NOT EXISTS ea_flood_areas AS SELECT * FROM df')
    print("Data stored in the 'trade_barriers' table.")


@asset(deps=[ea_flood_areas])
def ea_floods():
    # Get data from api and create dataframe
    url = 'https://environment.data.gov.uk/flood-monitoring/id/floods'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data['items'])

    # Create a connection to a persistent DuckDB database file named "data"
    con = duckdb.connect('data.duckdb')

    # Create a table and insert the data
    con.execute('CREATE TABLE IF NOT EXISTS ea_floods AS SELECT * FROM df')
    print("Data stored in the 'trade_barriers' table.")
    

@asset()
def os_open_usrns():
    
    db_file='openusrn.duckdb'
    num_rows=20
    url = "https://api.os.uk/downloads/v1/products/OpenUSRN/downloads?area=GB&format=GeoPackage&redirect"
    
    try:
        # Step 1: Retrieve the redirect URL
        response = requests.get(url)
        response.raise_for_status()
        status_code = response.status_code
        redirect_url = response.url
        logger.success(f"Success! Redirect URL is: {redirect_url}, Status Code is:{status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving the redirect URL: {e}")
        raise
    
    try:
        # Step 2: Download the content from the redirect URL
        response = requests.get(redirect_url)
        response.raise_for_status()
        zip_content = response.content
        logger.success("Zip found")
        # Step 3: Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 4: Write the zip file to the temporary directory
            zip_path = os.path.join(temp_dir, 'temp.zip')
            with open(zip_path, 'wb') as zip_file:
                zip_file.write(zip_content)

            # Step 5: Extract the contents of the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Step 6: Find the GeoPackage file
            gpkg_file = None
            for file_name in os.listdir(temp_dir):
                if file_name.endswith('.gpkg'):
                    gpkg_file = os.path.join(temp_dir, file_name)
                    break

            # Step 7: Load the specified number of rows from the GeoPackage into a GeoDataFrame
            # Change this in the future so it reads in a batch and keeps reading after to process the full gpkg file
            if gpkg_file:
                try:
                    gdf = gpd.read_file(gpkg_file, rows=num_rows)
                    # This works but returns a warning: 'Geometry column does not contain geometry' - think this is just a bug and there's a couple of github issues on it
                    # the to_wkt() successfully makes the geometry col in well known text...
                    gdf['geometry'] = gdf['geometry'].apply(lambda geom: transform(lambda x, y, z: (x, y), geom))
                    gdf['geometry'] = gdf['geometry'].to_wkt()
                    gdf.info()
                except Exception as e:
                    logger.error(f"Error loading GeoPackage into GeoDataFrame: {e}")
                    raise

                try:
                    # Create a DuckDB connection with the specified file path using a context manager
                    with duckdb.connect(database=db_file, read_only=False) as con:
                        # Install and load the spatial extension
                        con.execute('INSTALL spatial; LOAD spatial;')
                        # Create a table from the GeoPackage file
                        table_name = 'open_usrns_table'
                        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM gdf;")
                        # Query the table in the DuckDB database
                        query = f"""
                        SELECT usrn, geometry
                        FROM {table_name}
                        LIMIT 20;
                        """
                        result = con.execute(query).fetchdf()
                        print(result)
                except duckdb.Error as e:
                    logger.error(f"Error executing DuckDB operations: {e}")
                    raise

                return gdf
            else:
                raise FileNotFoundError("No GeoPackage file found in the zip archive")
    except Exception as e:
        logger.error(f"Error processing the GeoPackage: {e}")
        raise

# Example usage
# gdf = os_open_usrns()
