import json
import psycopg2
import rds_config


# Responding with Chatfuel formatted FB message
def respond (err, res=None) :
    return {
        'isBase64Encoded': 'false',
        'statusCode': '400' if err else '200',
        'body': json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        }
    }


def convertToChatFuelMessage(headers, results) :

    template = { "messages": [
            {
                'attachment': {
                    'type': 'template',
                    'payload': {
                        'template_type': 'generic',
                        'elements': []
                    }
                }
            }
        ]
    }

    for result in results:
        # title, subtitle, image_url, buttons
        template['messages'][0]['attachment']['payload']['elements'].append(
            {
                'title': result[1],
                'subtitle': '{}\n{}'.format(result[2], result[3]),
                'image_url': result[7],
                'buttons': [
                    {
                        'type': 'web_url',
                        'url': 'https://www.google.com.au/maps/dir//{}/'.format(result[3]),
                        'title': 'Get Directions'
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
    headers = []
    for desc in cur.description:
        headers.append(desc[0])
    return headers, results


# Generate a query string for the database of commonwealth events based on query string params passed
def generateQueryString( params ):
    return "SELECT * FROM points_of_interest WHERE location='{}'".format(params.get('Location'))


# handles the endpoint being hit by people wanting info, yo
def lambda_function(event, context):
    ''' expected params - location, language, timedate '''
    print("HELLO!")
    payload = event.get( 'queryStringParameters' ) 
    query_string = generateQueryString( params=payload )
    print('query string is {}'.format(query_string))

    # credentials for Amazon RDS instance
    db_hostname = rds_config.db_hostname
    db_username = rds_config.db_username
    db_password = rds_config.db_password
    db_name = rds_config.db_name

    print('config is {}, {}, {}, {}'.format(db_hostname, db_username, db_password, db_name))

    myConnection = psycopg2.connect( host=db_hostname, user=db_username, password=db_password, dbname=db_name )
    print('my connection is... {}'.format(myConnection))
    headers, results = doQuery( myConnection, query_string )
    formatted_result = convertToChatFuelMessage(headers, results)
    myConnection.close()  
    return respond(err=None, res=formatted_result)