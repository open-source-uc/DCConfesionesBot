import httplib2
from apiclient import discovery
from oauth2client.file import Storage
from time import gmtime, strftime
import os 

ID = os.environ["Id_Google"]
sheet_ID = os.environ["sheet_id"]
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'secret_client.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    Returns:
        Credentials, the obtained credential.
    """
    store = Storage('sheets.googleapis.com-python-quickstart.json')
    credentials = store.get()
    return credentials


def get_sheet_info():

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = ID

    values = service.spreadsheets().get(spreadsheetId=spreadsheetId,
                                        ranges=[],
                                        includeGridData=False)
    values = values.execute()

    rangeName = values["sheets"][0]['properties']['title']
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    if not values:
        print('No data found.')
    else:
        print(values)
        return values


def get_sheet_message():

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = ID

    values = service.spreadsheets().get(spreadsheetId=spreadsheetId,
                                        ranges=[],
                                        includeGridData=False)
    values = values.execute()

    rangeName = 'Pendientes'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    if not values:
        print('No data found.')
        return {}
    else:
        data = {}
        for messages in values:
            if messages[2] == "TRUE":
                data[int(messages[0])] = [messages[1], True]
            else:
                data[int(messages[0])] = [messages[1], False]
        return data

def delete_all():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    spreadsheetId = ID
    body = {'values': []}

    rangeName = 'Pendientes'
    result = service.spreadsheets().values().clear(
        spreadsheetId=spreadsheetId, range=rangeName, body={})

    result.execute()

def delete_row(id_):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = ID

    rangeName = 'Pendientes'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    if not values:
        print('No data found.')
        return {}
    else:
        data = {}
        number = -1
        for messages in values:
            number += 1
            if int(messages[0]) == id_:
                body = {'requests': [
                    {"deleteDimension": {
                        "range": {
                            "sheetId": sheet_ID,
                            "dimension": "ROWS",
                            "startIndex": number,
                            "endIndex": number + 1
                            }
                        }
                    }]
                }
                number -= 1
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheetId,
                    body=body).execute()
        return data

def write(data):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    spreadsheetId = ID
    body = {'values': [data]}

    rangeName = 'Datos'
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheetId, range=rangeName,
        valueInputOption="RAW", body=body)

    result.execute()


def write_message(data):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    spreadsheetId = ID
    body = {'values': [data]}

    rangeName = 'Pendientes'
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheetId, range=rangeName,
        valueInputOption="RAW", body=body)

    result.execute()


def write_message_accepted(data):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    spreadsheetId = ID
    body = {'values': [data]}

    rangeName = 'Aceptados'
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheetId, range=rangeName,
        valueInputOption="RAW", body=body)

    result.execute()

if __name__ == '__main__':

    SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
    CLIENT_SECRET_FILE = 'secret_client.json'
    APPLICATION_NAME = 'Google Sheets API Python Quickstart'


