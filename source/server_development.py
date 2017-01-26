import os
os.environ["NC_DATA_TOOLS_CONFIGURATION"] = "development"
from server import app


app.run(host="0.0.0.0")
