from pathlib import Path
from dotenv import dotenv_values
import sys, os, errno
from lib.errors import Errors

# LOADING SETTINGS ---------------------------------------------------------------------------------------------
class loadSettings:
    def __init__(self):
        return

    def loadDotEnv(self):
        envFileName='.env'
        initFile = Path.cwd() / envFileName
        
        groq_api_key=""
        model=""
        temperature=""
        host=""
        port=""
        username=""
        passwd=""
        integrated=0
        frac=0
        batchsize=0
        secrets=""
    
        try:
            secrets = dotenv_values(initFile)
            groq_api_key=secrets["GROQ_API_KEY"]
            model=secrets["MODEL"]
            temperature=secrets["TEMPERATURE"]
            host=secrets["HOST"]
            port=secrets["PORT"]
            username=secrets["USERNAME"]
            passwd=secrets["PASSWD"]
            integrated=secrets["INTEGRATED"]
            frac=secrets["FRAC"]
            batchsize=secrets["BATCHSIZE"]
        
        except Exception as e: 
            print(f'{e.__class__}, {e.args} : File {initFile} could not be found, aborting ...')
            sys.exit(Errors.FATAL)

        return secrets
            
    def __del__(self):
       return
