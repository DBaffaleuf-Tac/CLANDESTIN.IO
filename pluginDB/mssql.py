import sys, re, random, string
import pyodbc, pandas as pd
import sqlalchemy as sa
from sqlalchemy import Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
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

    def FKConstraintExists(self,TABLENAME):
        FKCONSTRAINTEXISTS=f"""SELECT ISNULL(
        (SELECT TOP (1) CASE WHEN fk.name IS NOT NULL THEN 1 END
        FROM sys.foreign_keys FK 
        WHERE SCHEMA_NAME(fk.schema_id)+'.'+OBJECT_NAME(fk.parent_object_id) =  '{TABLENAME}'),0) as res ;"""
        return FKCONSTRAINTEXISTS

    def findFKCOlumns(self,TABLENAME):
        FKCOLUMNS=f"""SELECT C.name 
        FROM sys.columns C
        INNER JOIN sys.foreign_key_columns FC 
            ON FC.parent_object_id=C.object_id 
            AND FC.parent_column_id = C.column_id
        WHERE parent_object_id = object_id('{TABLENAME}');"""
        return FKCOLUMNS

    def makeFinalUpdSQL(self,SOURCENAME,WTNAME,UQCOLS,PSDCOLS,BATCHSIZE):

        # 2 statements transaction : UPDATE SRC + DELETE FROM PSD 
        # SET ANSI_WARNINGS TO OFF TO ALLOW DATA TRUNCATION
        # BECAUSE SQLALCHEMY CHANGES THE COLUMN TYPES to varchar(max) in df.to_sql()
        UPDSQLFINAL="""SET ANSI_WARNINGS OFF;"""
        UPDSQLFINAL=UPDSQLFINAL + f"""BEGIN TRANSACTION ; """
        UPDSQLFINAL= UPDSQLFINAL + f""" UPDATE {SOURCENAME} SET """
        
        for psdcol in PSDCOLS:
            UPDSQLFINAL=UPDSQLFINAL + f""" {psdcol} = PSD.{psdcol} , """
        
        # rstrip last comma 
        UPDSQLFINAL = UPDSQLFINAL.rstrip(' , ')

        UPDSQLFINAL = UPDSQLFINAL + f""" FROM {SOURCENAME} SRC """
        UPDSQLFINAL = UPDSQLFINAL + f""" INNER JOIN (SELECT TOP({BATCHSIZE}) * FROM {WTNAME} ORDER BY [index] ASC) PSD ON """
        
        for uqcol in UQCOLS:
            UPDSQLFINAL = UPDSQLFINAL + f""" SRC.{uqcol} = PSD.{uqcol} AND """ 
        
        # Remove the FINAL 'AND' string
        UPDSQLFINAL = re.sub(' AND $', '', UPDSQLFINAL) 

         # Remove TOP batchsize rows from PSD table in the SAME transaction 
        UPDSQLFINAL = UPDSQLFINAL + f""" ; WITH PSD AS (SELECT TOP ({BATCHSIZE}) * FROM {WTNAME} ORDER BY [index] ASC) DELETE FROM PSD """ 

        # And finally COMMIT 
        UPDSQLFINAL = UPDSQLFINAL + """ ; COMMIT TRANSACTION ; """
        UPDSQLFINAL = UPDSQLFINAL + """ SET ANSI_WARNINGS ON ; """

        return UPDSQLFINAL

    def createUniqueIndex(self,WTNAME,COLS):
        # Transforming column list into string 
        joincols = ''
        for col in COLS:
            joincols = joincols + re.sub('\'','',col) + ','
        joincols = re.sub(',$','',joincols)

        rdn = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        idxname = 'idx_PSD_'+rdn
        CREATEINDEXPSDSQL=f"""CREATE UNIQUE INDEX {idxname} on {WTNAME}({joincols}) ; """
        return CREATEINDEXPSDSQL

    def createWorkTableSQL(self,WTNAME,TABLENAME):
        CREATETABLESQL=f"""SELECT * INTO [{WTNAME}] FROM {TABLENAME} WHERE 1=2 ;"""
        return CREATETABLESQL

    def copySourceTableSQL(self,SOURCETABLE,COPYTABLE):
        COPYSOURCETABLESQL=f""" SELECT * INTO {COPYTABLE} FROM {SOURCETABLE} ;"""
        return COPYSOURCETABLESQL

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
            DF.to_sql(name=WTNAME, con=engine, if_exists='replace')
            return True

        except Exception as e:
            print(e.__class__,e.args)
            return False

    def copySourceTable(self,cstr,query):
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

    def dropWorkTable(self,cstr,OWNER,WTNAME):
        try:
            connection_url = sa.engine.URL.create("mssql+pyodbc", query={"odbc_connect": cstr})
            engine = sa.create_engine(connection_url)
            TBL = Table(WTNAME, MetaData(), autoload_with=engine)
            TBL.drop(engine, checkfirst=False)
            return True 

        except Exception as e:
            print(e.__class__,e.args)
            return False

    def finalUpdate(self,cstr,query):
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

    def createIndexPSD(self,cstr,query):
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