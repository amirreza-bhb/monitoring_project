from sqlalchemy import create_engine

SERVER = "localhost"
DATABASE = "ecoMonitoringDB"

connection_string = (
    f"mssql+pyodbc://{SERVER}/{DATABASE}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&TrustServerCertificate=yes"
)

engine = create_engine(connection_string)
