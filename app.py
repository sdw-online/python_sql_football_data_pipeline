import os
import logging 
import requests 
import psycopg2
import pandas as pd 
from dotenv import load_dotenv
from requests.exceptions import HTTPError, RequestException, Timeout

# Load the environment variables 
load_dotenv()


API_KEY         =   os.getenv("API_KEY")
API_HOST        =   os.getenv("API_HOST")
LEAGUE_ID       =   os.getenv("LEAGUE_ID")
SEASON          =   os.getenv("SEASON")
DB_NAME         =   os.getenv("DB_NAME")
DB_USERNAME     =   os.getenv("DB_USERNAME")
DB_PASSWORD     =   os.getenv("DB_PASSWORD")
DB_HOST         =   os.getenv("DB_HOST")
DB_PORT         =   os.getenv("DB_PORT")



# Set up Postgres database connection
postgres_connection = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USERNAME,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)


# Get a cursor from the database
cur = postgres_connection.cursor()



# Fetch the Premier League data from Postgres
get_prem_league_standings_sql_query = """
    SELECT 
        position
        ,team
        ,games_played
        ,wins
        ,draws
        ,losses
        ,goals_for
        ,goals_against
        ,goal_difference
        ,points
    FROM 
        public.premier_league_standings_tbl
    ORDER BY 
        position;
"""


