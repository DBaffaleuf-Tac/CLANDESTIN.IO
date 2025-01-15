![image](https://github.com/user-attachments/assets/fe8737a3-f322-4ff1-acc6-ccb40871d79d)

Clandestinio is a python command-line tool to help pseudonymize data **in your test/dev/UAT environments**, on a per-table basis. It is based on generative AI to help identify which columns in the table can be considered sensitive as per the GDPR regulations, and eventually substitue data while preserving the semantic. 

It assumes that you have reloaded your live data on a **non production** database server (can be uat, test, development, anything else but production), and can be run at the end of your refresh pipeline for each table you would want to pseudonymize. 

# Disclaimer - Very important
Pseudonymizing can be irreversible to your data. The location of the data to be pseudonymized is specified in a configuration file, but it is easy to make mistakes and point to the wrong server and port. There is some protection built in the tool when run in interactive mode but it cannot prevent all user mistakes. 

Bottom-line : 
* **NEVER USE THIS TOOL ON YOUR PRODUCTION DATA**  
* **ALWAYS MAKE BACKUPS BEFORE YOU CHANGE ANYTHING ON YOUR DATA**
* **YOU ARE ULTIMATELY RESPONSIBLE FOR MANIPULATING YOUR DATA** 

# Prerequisites
- Python3 and the following modules: 
  - pyodbc
  - pandas
  - sqlalchemy
  - groq
  - langchain
  - pandasai
  - polars
  - tqdm

For now, Clandestinio is only compatible with SQL Server. There are plans to extend the capabilities to other RDBMS such as MariaDB, PostgreSQL, MongoDB, and possibly excel spreadsheets. 
 
# Installation
* Extract the repository to your local workstation, laptop using git:
  ```shell
  git clone https://github.com/DBaffaleuf-Tac/CLANDESTIN.IO.git
  ```
* Install the python modules mentionned in the prerequisites depending on your environment (conda, pip, etc...)
  ```shell
    cd CLANDESTIN.IO/
    pip install -r requirements.txt
  ```
* OR

  ```shell
    cd CLANDESTIN.IO/
    conda install --yes --file requirements.txt
  ```

# Configuration .env file 
Before running anything a little configuration is needed. Use the .sample.env file to create your own .env file :
  ```shell
   cp .sample.env .env
  ```
**Contents of the .env file :**
```shell
# !!! Sensitive information !!! 

# Put your Groq API KEY here
GROQ_API_KEY="YOUR_GROQ_API_KEY_HERE"

# LIST OF SUPPORTED MODELS : https://console.groq.com/docs/models 
#MODEL="mixtral-8x7b-32768"
#MODEL="llama3-70b-8192"
#MODEL="llama-3.1-70b-versatile"
MODEL="YOUR_MODEL_HERE"
TEMPERATURE="0.0"

# Database Server connection info 
HOST="YOUR_DATABASE_HOST_SERVER_HERE"
PORT="YOUR_DATABASE_HOST_PORT_HERE"
USERNAME="YOUR_DATABASE_USERNAME_HERE"
PASSWD="YOUR_DATABASE_PASSWORD_HERE"
# If DB Server is MSSQL, prefer using integrated security with no passwd by setting INTEGRATED=1 
INTEGRATED=0
# SAMPLE VALUE FOR IA PREDICTION
FRAC=0.1
# BATCHSIZE FOR PSEUDONYMIZATION
BATCHSIZE=10000
```

**Settings in the file :** 
* GROQ_API_KEY : this is where you put your GROQ API KEY. You can create your own API key at https://console.groq.com/keys
* MODEL : this is the name of the Gen model you are using. You can change the model according to your needs. The list of available models can be found at https://console.groq.com/docs/models
* TEMPERATURE : the temperature parameter of the model. The default and recommended value is 0.0 so the model responses are consistent across multiple runs.
* HOST : this is where you don't want to mess up. Put the name of your **non production** database server here
* PORT : port of your  **non production** database server here. Even if each RDBMS has a default port, specify it. 
* USERNAME : name of the database user to query the data table and propagate substitutions. THis user must have read - write access to the table mentionned in --tablename
* PASSWORD : obviously the password. For SQL Server this can be left blank if INTEGRATED is set to 1 (see below)
* INTEGRATED : 0 is the default. Only for SQL Server. When set to 1, integrated authentication is used and no password has to be provided. This is the recommended method.
* FRAC : % of the data sampled to identify personnal data in discovery mode (when --cmap is not used). 10% is the default.
* BATCHSIZE : both the number of rows passed to the Gen AI model for substitution in each batch, and the number of rows updated in the final / copy table per transaction. 10K is the default, but take a look at the Stats paragraph at the end to seek for the value that most suits your working set.     

# Usage
  ```shell
  python3 clandestinio.py <options ...>
  ```
OR

  ```shell
  py -3 \clandestinio.py <options ...>
  ```

# Options 

|  Option          |  Default Value  |  Mandatory Y/N  |          Description                                                                   | 
|------------------|-----------------|-----------------|----------------------------------------------------------------------------------------|
|   -h / --help    |      False      |       N         |      prints help / revision page                                                       |
|  -p / --provider |       N/A       |       Y         |      name of the provider {mssql} only SQL Server in v0.1                              |
| -D / --database  |       N/A       |       Y         |      database name                                                                     |
| -T / --tablename |       N/A       |       Y         |      full qualified name of the target table (schema.table)                            |
|   -C / --cmap    |       N/A       |       N         |      forcing a comma-separated list of columns ex 'firstname,lastname'                 |
| -G / --copytable |      False      |       N         |      When set, creates a copy of the table and substitues data only in the copy        |
|   -R / --dryrun  |      False      |       N         |      When set, presents the results but does not actually subsitute the data           |
|  -V / --verbose  |      False      |       N         |      When set, runs in verbose mode                                                    |
|   -F / --force   |      False      |       N         |      When set and with dryrun off, overrides the test (run in btach mode)              |

* --provider : as of v0.1, only SQL Server is available. Only use --provider=mssql
* --tablename : full qualified name means schema.object notation, see examples below
* --cmap : when not set, Clandestinio runs in discovery mode and leverages generative AI to detect which column can be considered personnal data. When set, forces a list of columns.
* --copytable : useful to test results before implementing them. When set, a full copy of the base table is made and prefixed COPY_% and only data in this table will be substituted
* --dryrun : when not set, in interactive mode a warning banner asks for confirmation before moving on with substitution. when set, only presents at the console an example of original and pseudonymized data.   See examples below.
* --verbose : prints intermediary results, specifically data samples before and after substitution, columns identification, and timing.
* --force : bypass the warning message in non dryrun mode, to allow users to run in silent / batch mode.
    
# Examples
## Minimal options :
  ```shell
  $ py -3 .\clandestinio.py --provider="mssql" --database="stackoverflow" --tablename="dbo.Users_small"
  Clandestinio has started at 2025-01-15 08:57:33.876401
  WARNING : Data will be substituted
  ---------------- !!! WARNING - DRY RUN DEACTIVATED !!! ----------------
  ---------------- !!! THE DATA WILL BE PSEUDONYMIZED !!! ---------------
  ARE YOU SURE YOU WANT TO PROCEED Y/N : Y
  ------------ CONFIRMED, PROCEEDING WITH PSEUDONYMIZATION ... ------
  -> Pseudonimyze : proceeding 10000 rows in 2 batches of 10000  rows... 
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:05<00:00,  2.96s/it]
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:01<00:00,  1.55it/s]
  Clandestinio has completed in 23.18284249305725 seconds
  ```

## Silent mode (--force):
  ```shell
  $ py -3 .\clandestinio.py --provider="mssql" --database="stackoverflow" --tablename="dbo.Users_small" --force 
  Clandestinio has started at 2025-01-15 09:05:55.981625
  WARNING : Data will be substituted
  -> Pseudonimyze : proceeding 10000 rows in 2 batches of 10000  rows... 
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:05<00:00,  2.92s/it] 
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00,  2.65it/s]
  Clandestinio has completed in 8.408372402191162 seconds
  ```
## Dryrun mode (--dryun):
  ```shell
  $ py -3 .\clandestinio.py --provider="mssql" --database="stackoverflow" --tablename="dbo.Users_small" --dryrun        
  Clandestinio has started in DRY RUN mode at 2025-01-15 09:08:12.659155
  WARNING : Only examples of substituted data will be presented
  -> Pseudonimyze : proceeding 10000 rows in 2 batches of 10000  rows... 
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:05<00:00,  2.84s/it] 
  --> DRYRUN : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 6.739 seconds
  ORIGINAL DATA :
            ID                                            ABOUTME AGE            CREATIONDATE  ...   VIEWS                         WEBSITEURL ACCOUNTID       CLANDESTINIOID
  0         1  <p>Hi, I'm not really a person.</p>\n\n<p>I'm ...     2008-07-31 00:00:00.000  ...     649     http://meta.stackexchange.com/        -1     7169893833049206
  1         2  <p><a href="http://www.codinghorror.com/blog/a...     2008-07-31 14:22:31.287  ...  408587  http://www.codinghorror.com/blog/         1  -126767350700192332
  2         3  <p>Developer on the Stack Overflow team.  Find...     2008-07-31 14:22:31.287  ...   23966           http://stackoverflow.com         2  -275375620745238106
  3         4  <p><a href="http://blog.stackoverflow.com/2009...     2008-07-31 14:22:31.287  ...   24396             http://jarroddixon.com         3 -1596034666079574500
  4         5  <p>I am:</p>\n\n<ul>\n<li>the co-founder and C...     2008-07-31 14:22:31.317  ...   73755     http://www.joelonsoftware.com/         4  3733231243798771846
  ...     ...                                                ...  ..                     ...  ...     ...                                ...       ...                  
  ...
  9995   9996                                                        2008-09-19 21:27:54.243  ...      83                                        10277  7381926564352699852
  9996   9997                                                        2008-09-19 21:32:26.587  ...      11                                       561187  4936372891790958402
  9997   9998  <p>I'm a software engineer based in Guadalajar...     2008-09-19 21:36:27.763  ...     713                http://pablasso.com     10278  3907909480035912445
  9998   9999  <p>I am a software engineer in Athens, Greece....     2008-09-19 21:39:34.043  ...     530                                        10279  2219898713749716072
  9999  10000                                                        2008-09-19 21:45:50.410  ...      58                                        10280  -581975977735534489
  
  [10000 rows x 15 columns]
  PSEUDOMYNIZED DATA :
            ID                                            ABOUTME  ...                                   LOCATION                    WEBSITEURL
  0         1  Head sign note voice forget firm imagine. List...  ...                   Marisachester, Guatemala              https://king.com
  1         2  Your even should range wear affect special. Wr...  ...                      West Heather, Reunion          https://mccarthy.com
  2         3  Feeling around like rate team drive. Note majo...  ...                West Lauren, Czech Republic         https://macdonald.org
  3         4  Game particular new history. By crime alone ed...  ...                        Millerton, Djibouti        https://cross-rose.org
  4         5  White parent maybe learn house account size. O...  ...                          Williamton, Niger              https://pope.net
  ...     ...                                                ...  ...                                        ...                           ...
  9995   9996  Fight consumer discussion I. Because science m...  ...                       Ryanchester, Andorra         https://middleton.com
  9996   9997  Expect few cover star data yeah tough former. ...  ...                            East Lisa, Mali    https://burnett-massey.com
  9997   9998  Run respond occur loss. Friend hit cultural mi...  ...                           Port Jacob, Guam  https://crawford-jenkins.com
  9998   9999  Different central first decade common probably...  ...          Hughesfurt, Sao Tome and Principe          https://williams.com
  9999  10000  Meet where site lose big someone. Prepare citi...  ...  Jonathanfort, French Southern Territories           https://bullock.org
  
  [10000 rows x 7 columns]
   
  Clandestinio has completed in 6.762551307678223 seconds
  ```

## Copytable mode (--copytable):
  ```shell
  $ py -3 .\clandestinio.py --provider="mssql" --database="stackoverflow" --tablename="dbo.Users_small" --copytable --force
  Clandestinio has started at 2025-01-15 09:10:56.195622
  WARNING : Data will be substituted
  -> Pseudonimyze : proceeding 10000 rows in 2 batches of 10000  rows... 
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:07<00:00,  3.66s/it] 
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00,  2.30it/s]
  Clandestinio has completed in 9.927576780319214 seconds
  ```

* Cmap mode (-cmap):
  ```shell
  py -3 .\clandestinio.py --provider="mssql" --database="stackoverflow" --tablename="dbo.Users_small"  --force --cmap='DisplayName,Location' 
  Clandestinio has started at 2025-01-15 19:07:22.570647
  WARNING : Data will be substituted
  -> Pseudonimyze : proceeding 10000 rows in 2 batches of 10000  rows... 
    0%|                                                                                                                                                                                                                                                 | 0/2 [00:00<?, ?it/s]         
  100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:02<00:00,  1.26s/it] 
  100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00,  3.11it/s]
  Clandestinio has completed in 5.395118713378906 seconds
  ```

## Verbose mode (-verbose):
  ```shell
  $ py -3 .\clandestinio.py --provider="mssql" --database="stackoverflow" --tablename="dbo.Users_small" --copytable --force --verbose
  Clandestinio has started at 2025-01-15 09:13:48.422752
  WARNING : Data will be substituted
  --> ENTERING VERBOSE MODE ----------------------------------------------------------
  
  --> VERBOSE : clandestinio -> printParams() -------------------------------------------------------
  __PROVIDER : mssql
  __DATABASE : stackoverflow
  __TABLENAME : dbo.Users_small
  __CMAP : None
  __DRYRUN : False
  __PARALLEL : False
  __VERBOSE : True
  __FORCE : True
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  DOTENV VARIABLES:  OrderedDict({'GROQ_API_KEY': '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', 'MODEL': 'llama-3.1-70b-versatile', 'TEMPERATURE': '0.0', 'HOST': 'DAVID-PC', 'PORT': '1433', 'USERNAME': 'dbaff-sql', 'PASSWD': 'capdata', 'INTEGRATED': '0', 'FRAC': '0.1', 'BATCHSIZE': '10000'})
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  ODBC Driver Used:  ODBC Driver 17 for SQL Server
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 0.0 seconds
  Connection String:  DRIVER=ODBC Driver 17 for SQL Server;SERVER=DAVID-PC;DATABASE=stackoverflow;UID=dbaff-sql;PWD=capdata;CHARSET=UTF8
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 0.08 seconds
  At least one unique constraint has been found on dbo.Users_small on columns (['ID'])
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 0.224 seconds
  10.0 % sampling top 10 rows for GDPR data identification:          ID                                            ABOUTME AGE            CREATIONDATE  ... VIEWS                         WEBSITEURL ACCOUNTID       CLANDESTINIOID
  9953  9954                           PhD Candidate, Developer     2008-09-19 19:43:51.717  ...   378                 http://www.from.bz     10235  5069681592649123493
  3850  3851  Scientist and software developper for a scient...     2008-09-11 11:33:00.943  ...   217           http://www.lri.fr/~semet      3940   585918664376754270
  4962  4963  Software Engineering Research Scientist for a ...     2008-09-15 14:50:50.573  ...   195             https://lolindrath.com      5081  2486981336065714974
  3886  3887  Software engineer focusing mainly on parallel,...     2008-09-11 13:54:15.657  ...    87        http://james.thevasaks.net/      3977 -4901959274289050828
  5437  5438  I'm a mexican developer who owns a small websh...     2008-09-15 17:35:21.757  ...    51             http://joaquin.axai.mx      5575 -4817111646987662867
  8517  8518                                                        2008-09-17 13:30:30.750  ...    20                                         8754  9014658398988800973
  2041  2042                                                        2008-08-25 17:46:55.040  ...    66                                         2089  5997801950785661366
  1989  1990  <p>I'm a contract Mac &amp; iOS developer work...     2008-08-25 07:54:29.033  ...   967         http://benedictcohen.co.uk      2037  3275388604982469404
  1933  1934  <p>I am a .NET software engineer working in Ir...     2008-08-24 17:15:55.357  ...   328  http://secretdeveloper.github.io/      1978 -1429516346746781969
  9984  9985                              <p>F# developer</p>\n     2008-09-19 20:56:26.097  ...  7482   http://lorgonblog.wordpress.com/     10266 -5243816490475443100
  
  [10 rows x 15 columns]
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 0.846 seconds
  Identified Columns for the dataset are : ['ABOUTME', 'AGE', 'DISPLAYNAME', 'EMAILHASH', 'LOCATION', 'WEBSITEURL']
  
  
  -> Pseudonimyze : proceeding 10000 rows in 2 batches of 10000  rows...
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:05<00:00,  2.80s/it] 
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 6.475 seconds
  ORIGINAL DATA : 
            ID                                            ABOUTME AGE            CREATIONDATE  ...   VIEWS                         WEBSITEURL ACCOUNTID       CLANDESTINIOID
  0         1  <p>Hi, I'm not really a person.</p>\n\n<p>I'm ...     2008-07-31 00:00:00.000  ...     649     http://meta.stackexchange.com/        -1   351799999803420987
  1         2  <p><a href="http://www.codinghorror.com/blog/a...     2008-07-31 14:22:31.287  ...  408587  http://www.codinghorror.com/blog/         1 -3341815431060270276
  2         3  <p>Developer on the Stack Overflow team.  Find...     2008-07-31 14:22:31.287  ...   23966           http://stackoverflow.com         2  7169479428293242071
  3         4  <p><a href="http://blog.stackoverflow.com/2009...     2008-07-31 14:22:31.287  ...   24396             http://jarroddixon.com         3    18047808857711048
  4         5  <p>I am:</p>\n\n<ul>\n<li>the co-founder and C...     2008-07-31 14:22:31.317  ...   73755     http://www.joelonsoftware.com/         4   112447770132852244
  ...     ...                                                ...  ..                     ...  ...     ...                                ...       ...                  
  ...
  9995   9996                                                        2008-09-19 21:27:54.243  ...      83                                        10277 -3307792509388308692
  9996   9997                                                        2008-09-19 21:32:26.587  ...      11                                       561187   727047970802066139
  9997   9998  <p>I'm a software engineer based in Guadalajar...     2008-09-19 21:36:27.763  ...     713                http://pablasso.com     10278 -5420654786267601664
  9998   9999  <p>I am a software engineer in Athens, Greece....     2008-09-19 21:39:34.043  ...     530                                        10279 -5394005644704851735
  9999  10000                                                        2008-09-19 21:45:50.410  ...      58                                        10280 -7219539445845054025
  
  [10000 rows x 15 columns]
  PSEUDOMYNIZED DATA :
            ID                                            ABOUTME  ...                                   LOCATION                     WEBSITEURL
  0         1  <p>Play reach agency source. Open fly trade vi...  ...                      Martinezfort, Liberia    https://martinez-mills.info
  1         2  <p>Camera reflect collection father of. Speech...  ...  Zamoramouth, United States Virgin Islands   https://frazier-wallace.info
  2         3                <p>Future size majority future.</p>  ...                         Garciaton, Georgia               https://shea.com
  3         4  <p>Institution customer world day.\nWhatever d...  ...                    Amyfurt, American Samoa        https://gross-brock.com
  4         5  <p>Yeah everyone baby drug. Name town dinner c...  ...                         Wendyville, Jersey  https://rodriguez-hubbard.com
  ...     ...                                                ...  ...                                        ...                            ...
  9995   9996  <p>Radio star first growth. May quickly here a...  ...                      New Lindsey, Mongolia              https://short.org
  9996   9997  <p>Represent indeed in grow foreign rule list....  ...                       New Deborah, Comoros           https://pacheco.info
  9997   9998  <p>Moment already life teach range. Occur poor...  ...      South Stephenstad, Dominican Republic            https://stevens.net
  9998   9999  <p>Cell cut safe. Suddenly any use run anyone ...  ...                   West Chelseaport, Cyprus        https://hughes-page.com
  9999  10000                         <p>Our me up four Mrs.</p>  ...                  Lake Cameronstad, Eritrea              https://cohen.com
  
  [10000 rows x 7 columns]
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 6.518 seconds
  Creating and importing worktable PSEUDO_Users_small_60869
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 7.128 seconds
  Creating indexes to speed final update
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 7.158 seconds
  Creating a copy of table dbo.Users_small into dbo.COPY_Users_small_63938...
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 7.158 seconds
  Copying table into dbo.COPY_Users_small_63938
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 7.23 seconds
  Creating indexes to speed final update
  
  
  --> VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 7.257 seconds
  Final substitution using 2 round(s) of 10000 rows from dbo.PSEUDO_Users_small_60869 into dbo.COPY_Users_small_63938
  
  
  -->VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 7.258 seconds
  final update : SET ANSI_WARNINGS OFF;BEGIN TRANSACTION ;  UPDATE dbo.COPY_Users_small_63938 SET  ABOUTME = PSD.ABOUTME ,  AGE = PSD.AGE ,  DISPLAYNAME = PSD.DISPLAYNAME ,  EMAILHASH = PSD.EMAILHASH ,  LOCATION = PSD.LOCATION ,  WEBSITEURL = PSD.WEBSITEURL FROM dbo.COPY_Users_small_63938 SRC  INNER JOIN (SELECT TOP(10000) * FROM dbo.PSEUDO_Users_small_60869 ORDER BY [index] ASC) PSD ON  SRC.ID = PSD.ID ; WITH PSD AS (SELECT TOP (10000) * FROM dbo.PSEUDO_Users_small_60869 ORDER BY [index] ASC) DELETE FROM PSD  ; COMMIT TRANSACTION ;  SET ANSI_WARNINGS ON ;
  
  
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00,  2.55it/s] 
  -->VERBOSE : clandestinio -> main() -------------------------------------------------------
  TIMER :T + 8.045 seconds
  Cleaning worktable PSEUDO_Users_small_60869
  
  
  Clandestinio has completed in 8.076989889144897 seconds
  ```


# Notes and remarks


# Stats
## Adjusting BATCHSIZE according to your working set :
Depending on the amount of data to pseudonymize, the value of batchsize has a tremendous effect on the overall performance.
Here are some stats of working sets from 10K rows to 1M rows, using various batchsizes from n batches of 10K rows to 1 batch of the full working set size :
![image](https://github.com/user-attachments/assets/d303d83e-f25e-4d4b-8558-ec96614257c8)
First serie on x-axis is the size of the working set from 10K rows (light blue) to 1M rows (dark blue)
In each serie, multiple batchsizes used ranging from 10K to the size of the full working set, in %  

We can see that the best elasped performance is reached when the batchsize is equivalent to the size of the working set (100%), however, it has also a huge effect on the amount of transaction log size needed to accomodate for such a transaction. It is always best advised to run high volume updates in small to medium size batches to avoid filling the transaction log. As a reference, the latest test updating 1M rows using 1 batch of 1M update takes 3.4Gb of transaction log). 
Bottom-line, don't necessarily use BATCHSIZE equivalent to 100% of the working set, find the right balance between performance and transaction log size.  

## Groq API and model limitations 
Also we can note that with multiple batches comes multiple requests to the Groq API. Sending more than 200K token per day with the llama-3.1-70b-versatile model will raise a rate error such as : 
```shell
groq.RateLimitError: Error code: 429 - {'error': {'message': 'Rate limit reached for model `llama-3.1-70b-versatile` in organization `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` on : Limit 200000, Used 200586, 
```
Limits for all models listed here : https://console.groq.com/settings/limits 

## Performance of seconds per iteration
When running multiple batches, we can see a slight variation in the time needed by the model to process each batch. When we take a look at the 2 longest runs :
* 500K rows in 51 x 10K batches
* 1M rows in 101 x 10K batches

It seems the number of seconds per iteration only fluctuates between 7 and 21 seconds depending on the traffic on the API endpoints, which makes the performance quite consistent across batches :
![image](https://github.com/user-attachments/assets/9638d9cb-488a-4a77-a3ea-dfd82a42d86c)
  
