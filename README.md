![image](https://github.com/user-attachments/assets/fe8737a3-f322-4ff1-acc6-ccb40871d79d)

Clandestinio is a python command-line tool to help pseudonymize data **in your test/dev/UAT environments**, on a per-table basis. It is based on generative AI to help identify which columns in the table can be considered sensitive as per the GDPR regulations, and eventually substitue data while preserving the semantic. 

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





# Notes and remarks

# Stats
