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
* --dryrun : when not set, in interactive mode a warning banner asks for confirmation before moving on with substitution. See examples below.
* --verbose : prints intermediary results, specifically data samples before and after substitution, columns identification, and timing.
* --force : bypass the warning message in non dryrun mode, to allow users to run in silent / batch mode.
    
# Examples
* Minimal options :
  ```shell
  py -3 .\clandestinio.py --provider="mssql" --database="stackoverflow" --tablename="dbo.Users_small"
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

* Silent mode (--force):
  ```shell
  py -3 .\clandestinio.py --provider="mssql" --database="stackoverflow" --tablename="dbo.Users_small" --force 
  Clandestinio has started at 2025-01-15 09:05:55.981625
  WARNING : Data will be substituted
  -> Pseudonimyze : proceeding 10000 rows in 2 batches of 10000  rows... 
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:05<00:00,  2.92s/it] 
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00,  2.65it/s]
  Clandestinio has completed in 8.408372402191162 seconds
  ```
* Dryrun mode (--dryun):
  ```shell
  py -3 .\clandestinio.py --provider="mssql" --database="stackoverflow" --tablename="dbo.Users_small" --dryrun        
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

* Copytable mode (--copytable):
  ```shell
  ```

* Cmap mode (-cmap):
  ```shell
  ```

* Verbose mode (-verbose):
  ```shell
  ```


# Notes and remarks


# Stats
