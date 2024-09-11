import sys
import pyodbc, pandas as pd
import sqlalchemy as sa
from lib.errors import Errors


# SQL Server Library ---------------------------------------------------------------------------------------------

class SQLServer():
    
    def __init__(self,SOURCETABLE):
        return
    
    def initSQLStr(self,SOURCETABLE):
        EXTRACTSOURCETABLESQL=f"SELECT * FROM {SOURCETABLE};"
        return EXTRACTSOURCETABLESQL
    
    def __del__(self):
       return

    def getODBCDriver(self):
        # Identify which ODBC driver version is installed
        localdrivers = pyodbc.drivers()
        for drv in localdrivers:
            if "ODBC" in drv:
                odbcdriver = drv
        
        return odbcdriver

    def makeConnectionString(self,ODBCDRIVER,SERVER,DATABASE,USERNAME,PASSWD,INTEGRATED):

        if INTEGRATED == "1":
            connectionString = f"DRIVER={ODBCDRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};Trusted_Connection=yes;CHARSET=UTF8"
        else:
            connectionString = f"DRIVER={ODBCDRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWD};CHARSET=UTF8"
        
        return connectionString
    
    def executeQueryToPD(self,cstr,query):
        try:
            connection_url = sa.engine.URL.create("mssql+pyodbc", query={"odbc_connect": cstr})
            engine = sa.create_engine(connection_url)
            with engine.begin() as conn:
                df = pd.read_sql_query(sa.text(query),conn)
            
            return df
        
        except Exception as e:
            print(e.__class__,e.args)
            sys.exit(Errors.FATAL)
