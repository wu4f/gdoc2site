# Takes a Google Doc ID and exports each tab in it as HTML within articles
# directory
# 1. Enabled both Google Drive API and Google Docs API in GCP project pdx-cs
# 2. Added an OAuth2 client and retrieved its JSON credentials at
# credentials.json
# 3. Upon invocation, do the Auth to get an OAuth token for the rest of the
# accesses
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import jinja2
import urllib
import requests
from bs4 import BeautifulSoup
import time
import os
import sys
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/docs.readonly']

def clean_content(html):
    def unwrap_google_url(url):
        if not url.startswith("https://www.google.com/url"):
            return url
        # Parse the URL query parameters
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        # 'q' contains the real URL if present
        if "q" in query and query["q"]:
            real_url = query["q"][0]
            return urllib.parse.unquote(real_url)
        return url

    soup = BeautifulSoup(html, 'html.parser')

    for a in soup.find_all("a", href=True):
        original = a["href"]
        cleaned = unwrap_google_url(original)
        a["href"] = cleaned    

    body_tag = soup.find("body")

    if body_tag:
        body_html_content = body_tag.prettify() # or str(body_tag)

    return body_html_content
    

def export_tab_as_html(creds, doc_id, tab_name, tab_id):
    """
    Finds a specific tab by name in a Google Doc and exports it as HTML.
    
    Args:
        creds: Valid Google OAuth2 credentials object.
        doc_id (str): The ID of the Google Doc.
        tab_name (str): The title of the tab you want to export.
        tab_id (str): The id of the tab you want to export.
    """
    os.makedirs("articles", exist_ok=True)
    output_filename = f"""{tab_name.replace(" ","-").lower()}.html"""
    export_url = (f"https://docs.google.com/document/d/{doc_id}/export"
            f"?format=html&id={doc_id}&tab={tab_id}")

    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(export_url, headers=headers)
    while response.status_code != 200:
        time.sleep(1)
        response = requests.get(export_url, headers=headers)

    body_html_content = clean_content(response.text)
    with open('base.html', 'r', encoding='utf-8') as file:
        template_content = file.read()
        template = jinja2.Template(template_content)
        rendered_html = template.render(title=tab_name, body=body_html_content)

    with open(f"articles/{output_filename}", 'wb') as f:
        f.write(rendered_html.encode('utf-8'))

    print(f"Successfully exported Google Doc '{doc_id}' as '{output_filename}'")

def get_tabs_from_doc(creds, doc_id):
    service = build('docs', 'v1', credentials=creds)
    print("Document:", doc_id)
    doc = service.documents().get(documentId=doc_id,includeTabsContent=True).execute()

    tabs = doc['tabs']
    tab_mapping = {}

    if tabs:
        for tab in tabs:
            props = tab.get('tabProperties', {})
            t_id = props.get('tabId')
            t_title = props.get('title')
        
            print(f" - Tab Name: {t_title} | ID: {t_id}")
            # Example: Accessing a specific ID by name later
            # target_tab_id = tab_mapping['Introduction']
            tab_mapping[t_title] = t_id
    else:
        # Fallback for documents that don't use the Tabs feature
        print("No tabs found. This is likely a standard single-page document.")
    return tab_mapping
 
def get_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

if __name__ == '__main__':
    try:
        tab_id = sys.argv[1]
        print(f"Exporting: {tab_id}")
    except IndexError:
        tab_id = 0
        pass
    creds = get_creds()
    doc_id = '11azwsMnSUPpR9ClIHSqZ3AcLvKdo0VqBMQyO9GacI9M'
    tabs = get_tabs_from_doc(creds, doc_id)

    if tab_id:
        tabs = {key: value for key, value in tabs.items() if value == tab_id}

    for tab in tabs:
        export_tab_as_html(creds, doc_id, tab, tabs[tab])
        time.sleep(1)
