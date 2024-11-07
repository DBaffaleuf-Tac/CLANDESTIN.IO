import sys
import pyodbc, pandas as pd
import sqlalchemy as sa
from sqlalchemy import Table, MetaData
from lib.errors import Errors


# SQL Server Library ---------------------------------------------------------------------------------------------

class SQLServer():
    
    def __init__(self,SOURCETABLE):
        return
    
    def initSQLStr(self,SOURCETABLE):
        EXTRACTSOURCETABLESQL=f"SELECT * FROM {SOURCETABLE};"
        return EXTRACTSOURCETABLESQL
    
    def databaseExists(self,DBNAME):
        DATABASEEXISTS=f"""SELECT ISNULL(
            (SELECT CASE WHEN name IS NOT NULL THEN 1 END
            FROM sys.databases WHERE name = '{DBNAME}'),0) AS res;"""
        return DATABASEEXISTS

    def tableExists(self,TABLENAME):
        TABLEEXISTS=f"""SELECT ISNULL(
        (SELECT CASE WHEN b.name IS NOT NULL THEN 1 END 
        FROM sys.tables b 
        INNER JOIN sys.schemas c ON b.schema_id = c.schema_id 
        WHERE schema_name(b.schema_id)+'.'+b.name = '{TABLENAME}' ),0)  AS res;"""
        return TABLEEXISTS

    def UniqueConstraintExists(self,TABLENAME):
        UNIQUECONSTRAINTEXISTS=f"""SELECT ISNULL(
        (SELECT TOP (1) CASE WHEN a.type IS NOT NULL THEN 1 END 
        FROM sys.key_constraints a 
        INNER JOIN sys.tables b ON a.parent_object_id = b.OBJECT_ID 
        INNER JOIN sys.schemas c ON a.schema_id = c.schema_id 
        WHERE a.type in ('PK','UQ')
        AND schema_name(b.schema_id)+'.'+b.name =  '{TABLENAME}'
        ORDER BY a.type),0)  AS res; """
        return UNIQUECONSTRAINTEXISTS

    def findUniqueColumns(self,TABLENAME):
        UNIQUECOLUMN=f"""SELECT TOP(1) i.index_id, STRING_AGG(c.name ,',') as columns
        FROM sys.key_constraints a 
        INNER JOIN sys.tables b ON a.parent_object_id = b.object_id  
        INNER JOIN sys.indexes i on i.object_id = b.object_id and a.unique_index_id = i.index_id
        INNER JOIN sys.index_columns ic on ic.index_id = i.index_id and ic.object_id=i.object_id
        INNER JOIN sys.columns c on c.column_id = ic.column_id AND c.object_id = ic.object_id
        WHERE a.type in ('PK','UQ')
        AND schema_name(b.schema_id)+'.'+b.name = '{TABLENAME}'  
		group by i.index_id ; """
        return UNIQUECOLUMN

    def createWorkTableSQL(self,OWNER,WTNAME,TABLENAME):
        CREATETABLESQL=f"""SELECT * INTO [{OWNER}].[{WTNAME}] FROM {TABLENAME} WHERE 1=2 ;"""
        return CREATETABLESQL

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

    def executeQuery(self,cstr,query):
        try:
            connection_url = sa.engine.URL.create("mssql+pyodbc", query={"odbc_connect": cstr})
            engine = sa.create_engine(connection_url)
            with engine.connect() as conn: 
                res = conn.execute(sa.text(query)).fetchall()
            
            return res

        except Exception as e:
            print(e.__class__,e.args)
            sys.exit(Errors.FATAL)

    def executeQuerySingleValue(self,cstr,query):
        try:
            connection_url = sa.engine.URL.create("mssql+pyodbc", query={"odbc_connect": cstr})
            engine = sa.create_engine(connection_url)
            with engine.connect() as conn: 
                res = conn.execute(sa.text(query)).fetchone()
            
            return res[0]

        except Exception as e:
            print(e.__class__,e.args)
            sys.exit(Errors.FATAL)
                
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

    def createWorkTable(self,cstr,query):
        try:
            connection_url = sa.engine.URL.create("mssql+pyodbc", query={"odbc_connect": cstr})
            engine = sa.create_engine(connection_url)
            with engine.connect() as conn: 
                res = conn.execute(sa.text(query))
                conn.commit()
            return True

        except Exception as e:
            print(e.__class__,e.args)
            return False

    def loadWorkTable(self,cstr,OWNER,WTNAME,DF):
        try:
            connection_url = sa.engine.URL.create("mssql+pyodbc", query={"odbc_connect": cstr})
            engine = sa.create_engine(connection_url)
            DF.to_sql(name=OWNER+'.'+WTNAME, con=engine)
            return True

        except Exception as e:
            print(e.__class__,e.args)
            sys.exit(Errors.FATAL)

    def dropWorkTable(self,cstr,OWNER,WTNAME):
        try:
            connection_url = sa.engine.URL.create("mssql+pyodbc", query={"odbc_connect": cstr})
            engine = sa.create_engine(connection_url)     
            TBL = Table(WTNAME, MetaData(), schema=OWNER, autoload_with=engine)
            TBL.drop(engine, checkfirst=False)     

        except Exception as e:
            print(e.__class__,e.args)
            sys.exit(Errors.FATAL)
