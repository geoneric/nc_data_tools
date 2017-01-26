import os
from nc_data_tools import create_app


app = create_app(os.getenv("NC_DATA_TOOLS_CONFIGURATION"))
