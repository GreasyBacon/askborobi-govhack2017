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

def convertToChatFuelMessage(headers, results, language="english") :

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

    if language.lower() == 'english':
        get_directions = 'Get Directions'
        venue_info = 'Venue Info'
    elif language.lower() == 'francais':
        get_directions = 'Obtenir Directions'
        venue_info = 'Info de Lieu'

    for result in results:
        # title, subtitle, image_url, buttons
        template['messages'][0]['attachment']['payload']['elements'].append(
            {
                'title': result[1],
                'subtitle': '@ {} - {}\n{}\n{}'.format(result[2], result[3], result[9], result[13]),
                'image_url': result[6],
                'buttons': [
                    {
                        'type': 'web_url',
                        'url': 'https://www.google.com.au/maps/dir//{}/'.format(result[13]),
                        'title': get_directions
                    },
                    {
                        'type': 'web_url',
                        'url': result[14],
                        'title': venue_info
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


def frenchCategoryMapping(category):

    if category == 'Boxe':
        converted_category = 'Boxing'
    elif category == 'Bols de Pelouse': 
        converted_category = 'Lawn Bowls'
    elif category == 'Gym Artistique':
        converted_category = 'Gymnastics'
    elif category == 'Le Hockey':
        converted_category = 'Hockey'
    
    return converted_category


def frenchLocationMapping(location):

    if location == 'La Gold Coast':
        converted_location = 'Gold Coast'

    return converted_location


# Generate a query string for the database of commonwealth events based on query string params passed
def generateQueryString( params ):

    category = params.get('sport_type')
    location = params.get('Location')
    if params.get('language') == 'Francais':
        category = frenchCategoryMapping(params.get('sport_type'))
        location = frenchLocationMapping(params.get('Location'))

    return "SELECT commonwealth_events.id, commonwealth_events.name, commonwealth_events.start, commonwealth_events.end, commonwealth_events.venue_id, commonwealth_events.category," + \
           "commonwealth_events.image_url, commonwealth_events.city, venues.id, venues.name, venues.code, venues.lat, venues.lon, venues.address, venues.link, venues.description " + \
           "FROM commonwealth_events, venues WHERE city = '{}' AND category = '{}' AND commonwealth_events.venue_id=venues.id".format(location, category)


# handles the endpoint being hit by people wanting info, yo
def lambda_function(event, context):
    ''' expected params - sport_type, location, language, timedate '''
    print("HELLO!")
    payload = event.get( 'queryStringParameters' ) 
    query_string = generateQueryString( params=payload )
    language = payload.get('language', 'English')
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
    formatted_result = convertToChatFuelMessage(headers, results, language)
    myConnection.close()  
    return respond(err=None, res=formatted_result)