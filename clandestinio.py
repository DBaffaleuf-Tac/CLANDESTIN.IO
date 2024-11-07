# PRIVATE IMPORTS -----------------------------------------------------------------------------------------------
from lib.settings import loadSettings
from lib.errors import Errors
from pluginDB.mssql import SQLServer 
from assistant.assistant import assistant

# BUILTIN IMPORTS -----------------------------------------------------------------------------------------------
import sys, getopt, re, string, os.path, argparse, time, datetime, random
import pandas as pd
import numpy as np
from tqdm import tqdm

# --------------------------------------------------------------------------------------------------------------
# FUNCTION checkParams()
#                                 _               _    ____
#                             ___| |__   ___  ___| | _|  _ \ __ _ _ __ __ _ _ __ ___  ___
#                            / __| '_ \ / _ \/ __| |/ / |_) / _` | '__/ _` | '_ ` _ \/ __|
#                           | (__| | | |  __/ (__|   <|  __/ (_| | | | (_| | | | | | \__ \
#                            \___|_| |_|\___|\___|_|\_\_|   \__,_|_|  \__,_|_| |_| |_|___/

def checkParams(__PROVIDER, __DATABASE, __TABLENAME,__CMAP,__DRYRUN,__VERBOSE):
 
    # DRY RUN TESTING AND WARNING NOTIFICATION MESSAGES
    # if --dryrun is not mentionned, send a warning message asking for confirmation 
    # if not confirmed, the execution is aborted and the program exits
    if __DRYRUN == False:
        print('---------------- !!! WARNING - DRY RUN DEACTIVATED !!! ---------------- ')
        print('---------------- !!! THE DATA WILL BE PSEUDONYMIZED !!! ---------------')
        drResp = input('ARE YOU SURE YOU WANT TO PROCEED Y/N : ')
        if drResp == "Y" or drResp == "y":
            print('------------ CONFIRMED, PROCEEDING WITH PSEUDONYMIZATION ... ------')
            return True
        else:
            print('------------ NOT CONFIRMED, aborting ... ---------')
            return False
    else:
        return True

# --------------------------------------------------------------------------------------------------------------
# FUNCTION printParams()
#                                   _       _   ____
#                        _ __  _ __(_)_ __ | |_|  _ \ __ _ _ __ __ _ _ __ ___  ___
#                       | '_ \| '__| | '_ \| __| |_) / _` | '__/ _` | '_ ` _ \/ __|
#                       | |_) | |  | | | | | |_|  __/ (_| | | | (_| | | | | | \__ \
#                       | .__/|_|  |_|_| |_|\__|_|   \__,_|_|  \__,_|_| |_| |_|___/
#                       |_|

def printParams(__PROVIDER, __DATABASE, __TABLENAME,__CMAP,__DRYRUN,__PARALLEL,__VERBOSE):
    print (f'__PROVIDER : {__PROVIDER}')
    print (f'__DATABASE : {__DATABASE}')
    print (f'__TABLENAME : {__TABLENAME}')
    print (f'__CMAP : {__CMAP}')
    print (f'__DRYRUN : {__DRYRUN}')
    print (f'__PARALLEL : {__PARALLEL}')
    print (f'__VERBOSE : {__VERBOSE}')

    return

def pseudonymize(sourcerecords,GDPRcolumnsList,UQCOLS,batches,batchsize,settings):
    Pseudonymizer = assistant()
    pseudonymizedData = pd.DataFrame()
    UQRecords = sourcerecords[UQCOLS]

    for i in tqdm(range(batches)):            
        if not sourcerecords.empty:
            # Select batchsize first rows from the original dataframe
            reduxRecords = sourcerecords[GDPRcolumnsList].head(batchsize)
            
            # Pseudonymize the selected batchsize rows and return a new dataframe    
            try:
                reduxGDPRSubsituteData = Pseudonymizer.replaceGDPRData(settings['GROQ_API_KEY'],settings["MODEL"],settings["TEMPERATURE"],reduxRecords)
                if type(reduxGDPRSubsituteData) is pd.core.frame.DataFrame: 
                    pseudonymizedData = pd.concat([pseudonymizedData,reduxGDPRSubsituteData],ignore_index=False)
                    # Remove pseudonymized rows from the original dataframe by concatenation and duplicates removal
                    combinator = pd.concat([sourcerecords,reduxRecords],ignore_index=False)
                    sourcerecords = combinator[~combinator.index.duplicated(keep=False)]
                else:
                    # Sometimes pandasai returns str instead of DF when error occuring at 
                    # processing some of it (usually when it is insufficiently cleaned)
                    print(f'type of reduxGDPRSubsituteData : {type(reduxGDPRSubsituteData)}')
                    sys.exit(Errors.FATAL)

            except Exception as e:
                print(f'Exception : {e.args}')
                sys.exit(Errors.FATAL)

    reduxFinal = pd.concat([UQRecords,reduxRecords],axis=1,ignore_index=False)
    pseudonymizedFinal = pd.concat([UQRecords,pseudonymizedData],axis=1, ignore_index=False)

    return pseudonymizedFinal, reduxFinal

#  -------------------------------------------------------------------------------------------------------------
# FUNCTION main()
#                                     __  __    _    ___ _   _
#                                    |  \/  |  / \  |_ _| \ | |
#                                    | |\/| | / _ \  | ||  \| |
#                                    | |  | |/ ___ \ | || |\  |
#                                    |_|  |_/_/   \_\___|_| \_|

def main():

    global __PROVIDER
    global __DATABASE
    global __TABLENAME
    global __CMAP
    global __DRYRUN 
    global __VERBOSE
    global __PARALLEL

    __PROVIDER=""
    __DATABASE=""
    __TABLENAME=""
    __CMAP=[]
  
    start=time.time()
    print(f"Clandestinio has started at {datetime.datetime.fromtimestamp(start)}")
    
    # ARGPARSE -----------------------------------------------------------------------------------------------------
    with open('revision','r') as revision:
        usageBanner = revision.read()
    parser = argparse.ArgumentParser(usage=usageBanner,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-P", "--provider", type=str, choices=["mssql","my","pg","exl"], required=True, help="name of the provider { 'mssql' | 'my' | 'pg' | 'xlsx' } ")
    parser.add_argument("-D", "--databasename", type=ascii, required=True, help="database name if applicable (ignored for excel data)")
    parser.add_argument("-T", "--tablename", type=ascii, required=True, help="full qualified name of the target table / mongo collection / excel tab")
    parser.add_argument("-C", "--cmap", type=ascii, required=False, help="forcing a comma-separated key-value pairs of column_name:type ie 'fname:firstname,lname:lastname'")
    parser.add_argument("-R", "--dryrun", dest='run', action='store_true', required=False, help="Presents the results but does not actually subsitute the data")
    parser.add_argument("-V", "--verbose", dest='verbose', action='store_true', required=False, help="Verbose mode, False by default")
    parser.add_argument("-Y", "--parallel", dest='parallel', action='store_true', required=False, help="Parallel mode, False by default")
    parser.set_defaults(run=False)
    parser.set_defaults(verbose=False)
    parser.set_defaults(parallel=False)

    args = parser.parse_args()
    config = vars(args)
    __PROVIDER=config["provider"]
    __DATABASE=config["databasename"].replace("'","")
    __TABLENAME=config["tablename"].replace("'","")
    __CMAP=config["cmap"]
    __DRYRUN=config["run"]
    __VERBOSE=config["verbose"]
    __PARALLEL=config["parallel"]


    if __VERBOSE == 1:
        print ('--> ENTERING VERBOSE MODE ----------------------------------------------------------\n')

    # ARGV sanity checks -------------------------------------------------------------------------
    if not checkParams(__PROVIDER, __DATABASE, __TABLENAME, __CMAP,__DRYRUN, __VERBOSE):
        sys.exit(Errors.FATAL)

    if __VERBOSE == 1:
        print ('--> VERBOSE : clandestinio -> printParams() -------------------------------------------------------')
        printParams(__PROVIDER, __DATABASE, __TABLENAME, __CMAP,__DRYRUN, __PARALLEL,__VERBOSE)
        print('\n')

    # Loading environment  -----------------------------------------------------------------------
    Envs = loadSettings()
    if not Envs:
        sys.exit(Errors.FATAL)
    
    else: 
        settings = Envs.loadDotEnv()

        if __VERBOSE == 1:
            print ('--> VERBOSE : clandestinio -> main() -------------------------------------------------------')
            print("DOTENV VARIABLES: ",settings)
            print('\n')
            

        # Connect to the source ----------------------------------------------------------------------
        if __PROVIDER == 'mssql':
            server = SQLServer(__TABLENAME)
            odbcdriver = server.getODBCDriver()
            if __VERBOSE == 1:
                print ('--> VERBOSE : clandestinio -> main() -------------------------------------------------------')
                print("ODBC Driver Used: ",odbcdriver)
                print('\n')

        elif __PROVIDER == 'my': # NOT IMPLEMENTED
            return Errors.SUCCESS
        elif __PROVIDER == 'pg': # NOT IMPLEMENTED
            return Errors.SUCCESS
        elif __PROVIDER == 'exl': # NOT IMPLEMENTED
            return Errors.SUCCESS

        cstr = server.makeConnectionString(odbcdriver,settings['HOST'],__DATABASE,settings['USERNAME'],settings['PASSWD'],settings['INTEGRATED'])
        if __VERBOSE == 1:
            print ('--> VERBOSE : clandestinio -> main() -------------------------------------------------------')
            print("Connection String: ",cstr)
            print('\n')

        # Data Source Sanity checks ------------------------------------------------------------------------------ 
        if server.executeQuerySingleValue(cstr,server.UniqueConstraintExists(__TABLENAME)) == 0:
            print(f'No unique constraint or primary key found in table {__TABLENAME} for host {settings['HOST']}')
            sys.exit(Errors.FATAL)     
        else:
            # Find the column(s) used in the first identified unique constraint 
            # findUniqueColumns returns one tuple / 2 columns in the form (index_id,comma-separated-columns-list)
            # Example : [(2, 'Id,CreationDate')]
            # We only need the list of columns included in the first unique constraint we encounter thus [0][1]
            # And finally transforming into list
            UQCOLS = server.executeQuery(cstr,server.findUniqueColumns(__TABLENAME))[0][1].upper().split(',')
            if __VERBOSE == 1:
                print ('--> VERBOSE : clandestinio -> main() -------------------------------------------------------')
                print(f"At least one unique constraint has been found on {__TABLENAME} on columns ({UQCOLS})")
                print('\n')            

        # Load data ----------------------------------------------------------------------------------
        sourcerecords = server.executeQueryToPD(cstr,server.initSQLStr(__TABLENAME))

        # Normalize and Clean data -------------------------------------------------------------------
        # 1) Adding a hash value for UNIQUENESS
        sourcerecords['clandestinioid'] = sourcerecords.apply(lambda x: hash(tuple(x)), axis = 1)
        # 2) Normalizing column names 
        sourcerecords.columns = (sourcerecords.columns.str.strip().str.upper()
              .str.replace(' ', '_', regex=True)
              .str.replace('(', '', regex=True)
              .str.replace(')', '', regex=True))  
                
        # 3) Convert any object dtype in String dtype and remove any non ASCII character
        for col in sourcerecords.keys():   
            if sourcerecords.dtypes[col] == "object":
                sourcerecords[col] = sourcerecords[col].astype("string")
                sourcerecords[col] = sourcerecords[col].str.encode('ascii', 'ignore').str.decode('ascii')

        # 4) Replacing NaNs
        sourcerecords = sourcerecords.fillna('')

        # 3) Sampling DOTENV.FRAC% non-NaN random values for LLM to detect existence of GDPR data
        frac=float(settings['FRAC'])
        samplerecords=sourcerecords.sample(frac=frac,random_state=1).head(10)

        if __VERBOSE == 1:
            print ('--> VERBOSE : clandestinio -> main() -------------------------------------------------------')
            print(f"{frac*100} % sampling top 10 rows for GDPR data identification: ",samplerecords)
            print('\n')
        
        # IA -> Target columns ID --------------------------------------------------------------------
        GDPRfinder = assistant()
        GDPRcolumnsList = GDPRfinder.findGDPRData(settings['GROQ_API_KEY'],settings["MODEL"],settings["TEMPERATURE"],samplerecords).split(',')

        if __VERBOSE == 1:
            print ('--> VERBOSE : clandestinio -> main() -------------------------------------------------------')
            print(f"Identified Columns for the dataset are : {GDPRcolumnsList}")
            print('\n')

        # IA -> Local pseudonymization ---------------------------------------------------------------        
        batchsize=int(settings["BATCHSIZE"])
        if batchsize == 0:
            print('BATCHSIZE CANNOT BE ZERO, CHANGE THE VALUE IN .ENV FILE !!!')
            sys.exit(Errors.FATAL)
        else:
            if batchsize <= len(sourcerecords):
                batches=1
            else:    
                batches=int(len(sourcerecords)/batchsize) + 1
               
        # Pseudonymization Loop of batchsize rows
        print(f"-> Proceeding {len(sourcerecords)} rows in {batches} batches of {batchsize}  rows... ")
        
        # single / multi threaded depending on --parallel
        # --parallel not used at this point
        # SINGLE - THREADED
        
        pseudonymizedData, reduxRecords = pseudonymize(sourcerecords,GDPRcolumnsList,UQCOLS,batches,batchsize,settings)

        if __VERBOSE == 1:
            print ('--> VERBOSE : clandestinio -> main() -------------------------------------------------------')
            print(f"ORIGINAL DATA : \n {reduxRecords}")
            print(f"PSEUDOMYNIZED DATA : \n {pseudonymizedData}")
            print('\n')
        
        # Import local pseudonymized -----------------------------------------------------------------
        # Create physical worktable in the database using original column names  
        OWNER=__TABLENAME.split('.')[0]       
        TBL=__TABLENAME.split('.')[1]
        WTNAME=f"PSEUDO_{TBL}_{str(random.randint(0,99999))}"
        if not server.createWorkTable(cstr,server.createWorkTableSQL(OWNER,WTNAME,__TABLENAME)):
            print(f"Error during worktable creation, aborting...")
            sys.exit(Errors.FATAL)
                
        # Import data from pseudonymizedData DF
        server.loadWorkTable(cstr,OWNER,WTNAME,pseudonymizedData)

        # Final substitution -------------------------------------------------------------------------

        # Cleaning -----------------------------------------------------------------------------------
        # Drop remaining DFs
        # Drop Worktable
        server.dropWorkTable(cstr,OWNER,WTNAME) # <-- does not work if the table not empty grrrr alchemy !!!


    end=time.time()
    elapsed=(end-start)
    print(f"Clandestinio has completed in {elapsed} seconds")
    return Errors.SUCCESS

#  ------------------------------------------------------------------------------------------------
# Entry Point
#                    _____ _   _ _____ ______   __  ____   ___ ___ _   _ _____
#                   | ____| \ | |_   _|  _ \ \ / / |  _ \ / _ \_ _| \ | |_   _|
#                   |  _| |  \| | | | | |_) \ V /  | |_) | | | | ||  \| | | |
#                   | |___| |\  | | | |  _ < | |   |  __/| |_| | || |\  | | |
#                   |_____|_| \_| |_| |_| \_\|_|   |_|    \___/___|_| \_| |_|

if __name__ == "__main__":
    main()
