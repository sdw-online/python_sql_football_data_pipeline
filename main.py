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



# Set up the logger 
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler
file_handler = logging.FileHandler('football_table_standings.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))




# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))


# Instantiate the logger object
logger = logging.getLogger()


# Add the file handler to the logger
logger.addHandler(file_handler)


# Add the console handler to the logger
logger.addHandler(console_handler)


	
url           =   "https://api-football-v1.p.rapidapi.com/v3/standings"
headers       =   {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": API_HOST}
query_string  =   {'season': SEASON,'league': LEAGUE_ID}



# response      =   requests.request("GET", url, headers=headers, params=query_string)

try:
    api_response = requests.get(url, headers=headers, params=query_string, timeout=15)
    api_response.raise_for_status() 

except HTTPError as http_err:
    logger.error(f'HTTP error occurred: {http_err}')

except Timeout:
    logger.error('Request timed out after 15 seconds')

except RequestException as request_err:
    logger.error(f'Request error occurred: {request_err}')


standings_data          =   api_response.json()['response']
# print(standings_data)




# Extracting the standings information
standings = standings_data[0]['league']['standings'][0]


# List to hold our extracted data
data_list = []


# Parsing through each team's standing
for team_info in standings:
    rank            =   team_info['rank']
    team_name       =   team_info['team']['name']
    played          =   team_info['all']['played']
    win             =   team_info['all']['win']
    draw            =   team_info['all']['draw']
    lose            =   team_info['all']['lose']
    goals_for       =   team_info['all']['goals']['for']
    goals_against   =   team_info['all']['goals']['against']
    goals_diff      =   team_info['goalsDiff']
    points          =   team_info['points']
    
    data_list.append([rank, team_name, played, win, draw, lose, goals_for, goals_against, goals_diff, points])

# Create the dataFrame
columns         =   ['P', 'Team', 'GP', 'W', 'D', 'L', 'F', 'A', 'GD', 'Pts']
standings_df    =   pd.DataFrame(data_list, columns=columns)


# Display the dataFrame
print(standings_df.to_string(index=False))




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



# Use SQL to create a table for the Premier League 
create_table_sql_query = """
    CREATE TABLE IF NOT EXISTS premier_league_standings_tbl (
            position            INT PRIMARY KEY,
            team                VARCHAR(255),
            games_played        INTEGER,
            wins                INTEGER,
            draws               INTEGER,
            losses              INTEGER,
            goals_for           INTEGER,
            goals_against       INTEGER,
            goal_difference     INTEGER,
            points              INTEGER
    );
"""


# Run the SQL query 
cur.execute(create_table_sql_query)


# Commit the transaction 
postgres_connection.commit()




# Use SQL to insert data into the Premier League table 
insert_data_sql_query = """
    INSERT INTO public.premier_league_standings_tbl (
            position, team, games_played, wins, draws, losses, goals_for, goals_against, goal_difference, points              
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

    ON CONFLICT (position) DO UPDATE SET
    team               =   EXCLUDED.team, 
    games_played       =   EXCLUDED.games_played, 
    wins               =   EXCLUDED.wins, 
    draws              =   EXCLUDED.draws, 
    losses             =   EXCLUDED.losses, 
    goals_for          =   EXCLUDED.goals_for, 
    goals_against      =   EXCLUDED.goals_against, 
    goal_difference    =   EXCLUDED.goal_difference, 
    points             =   EXCLUDED.points
"""



for idx, row in standings_df.iterrows():
    cur.execute(insert_data_sql_query, 
                (row['P'], 
                 row['Team'], 
                 row['GP'], 
                 row['W'], 
                 row['D'], 
                 row['L'], 
                 row['F'], 
                 row['A'], 
                 row['GD'], 
                 row['Pts'])
    )



# Commit the transaction 
postgres_connection.commit()





# Use SQL to create a view that updates the table rankings
create_ranked_standings_view_sql_query = """
    CREATE OR REPLACE VIEW public.premier_league_standings_vw AS 
        SELECT 
            RANK() OVER (ORDER BY points DESC, goal_difference DESC, goals_for DESC) as position
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
            public.premier_league_standings_tbl;
"""


# Run the SQL query 
cur.execute(create_ranked_standings_view_sql_query)


# Commit the transaction 
postgres_connection.commit()