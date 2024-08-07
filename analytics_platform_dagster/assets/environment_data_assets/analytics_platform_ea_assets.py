import requests
import pandas as pd

from ...utils.variables_helper.url_links import asset_urls
from ...utils.io_manager_helper.io_manager import AwsWranglerDeltaLakeIOManager
from dagster import asset, OpExecutionContext, Output

@asset(group_name="environment_assets")
def ea_flood_areas(context: OpExecutionContext):
    """
    tbc
    """
    try:
        # Get data from api and create dataframe
        url = asset_urls.get("ea_flood_areas")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['items'])
        # Log DataFrame info for debugging
        context.log.info(f"DataFrame info:\n{df.info()}")
        context.log.info(f"DataFrame dtypes:\n{df.dtypes}")
        context.log.info(f"DataFrame head:\n{df.head()}")

        delta_io = AwsWranglerDeltaLakeIOManager("analytics-data-lake-bronze")
        return Output(delta_io.handle_output(context, df))
    except Exception as error:
        context.log.error(f"Error in dbt_trade_barriers: {str(error)}")
        raise error

@asset(group_name="environment_assets")
def ea_floods(context: OpExecutionContext):
    """
    tbc
    """
    try:
        # Get data from api and create dataframe
        url = asset_urls.get("ea_floods")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['items'])
        
        context.log.info(f"DataFrame info:\n{df.info()}")
        context.log.info(f"DataFrame dtypes:\n{df.dtypes}")
        context.log.info(f"DataFrame head:\n{df.head()}")

        delta_io = AwsWranglerDeltaLakeIOManager("analytics-data-lake-bronze")
        return Output(delta_io.handle_output(context, df))
    except Exception as error:
        context.log.error(f"Error in dbt_trade_barriers: {str(error)}")
        raise error
