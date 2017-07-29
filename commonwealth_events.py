import json
import psycopg2
import rds_config

# credentials for Amazon RDS instance
db_hostname = rds_config.db_hostname
db_username = rds_config.db_username
db_password = rds_config.db_password
db_name = rds_config.db_name

myConnection = psycopg2.connect( host=db_hostname, user=db_username, password=db_password, dbname=db_name )


# Responding with Chatfuel formatted FB message
def respond (err, res=None) :
    return {
        'statusCode': '400' if err else '200',
        'body': res,
        'headers': {
            'Content-Type': 'application/json',
        }
    }

def convertToChatFuelMessage(headers, results) :

    template = {
        'attachment': {
            'type': 'template',
            'payload': {
                'template_type': 'generic',
                'elements': []
            }
        }
    }

    for result in results:
        # title, subtitle, image_url, buttons
        template['attachment']['type']['payload']['elements'].append(
            {
                'title': result[0],
                'subtitle': '@ {}\n{}\n{}'.format(result[2], result[9], result[13]),
                'image_url': result[6],
                'buttons': [
                    {
                        'type': 'web_url',
                        'url': '',
                        'title': 'Get Directions'
                    },
                    {
                        'type': 'web_url',
                        'url': result[14],
                        'title': 'Venue Info'
                    },
                    {
                        'type': 'element_share'
                    }
                ]
            }
        )

    return template

# Simple routine to run a query on a database and return the results
def doQuery( conn, queryString ) :
    cur = conn.cursor()
    cur.execute( queryString )
    results = cur.fetchall()
    headers = [desc[0] for desc in cur.description]
    return headers, results


# Generate a query string for the database of commonwealth events based on query string params passed
def generateQueryString( params ):
    return "SELECT * FROM commonwealth_events, venues WHERE city = '{}' AND category = '{}'".format(params.get('location'), params.get('sport_type'))


# handles the endpoint being hit by people wanting info, yo
def lambda_function(event, context):
    ''' expected params - sport_type, location, language, timedate '''
    payload = event.get( 'queryStringParameters' ) 
    query_string = generateQueryString( payload )
    headers, results = doQuery( myConnection, query_string )
    formatted_result = convertToChatFuelMessage(headers, results)
    myConnection.close()    
    return respond(err=None, res=formatted_result)