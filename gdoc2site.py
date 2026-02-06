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
import re
from datetime import datetime, timezone


SCOPES = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/docs.readonly']

def print_usage():
    print("Usage:")
    print("  python gdoc2site.py <doc_id>")
    print("  python gdoc2site.py <doc_id> <tab_id>")
    print("")
    print("Examples:")
    print("  python gdoc2site.py 11az...GacI9M")
    print("  python gdoc2site.py 11az...GacI9M t.3fbo....9zik")

def filter_bold_italic(css_text):
    # Regex to separate "Selector { Content }"
    # ([^{]+) captures the selector
    # ([^}]+) captures the properties inside
    pattern = r"([^{]+)\{([^}]+)\}"
    matches = re.findall(pattern, css_text)
    cleaned_output = []

    for selector, content in matches:
        selector = selector.strip()
        
        # 1. Process only class selectors (lines starting with or containing a dot)
        if "." in selector:
            # 2. Split properties by semicolon
            props = content.split(';')
            kept_props = []

            for prop in props:
                if ":" in prop:
                    key, value = prop.split(':', 1)
                    key = key.strip().lower()
                    
                    # 3. Filter: Keep only weight (bold) and style (italic)
                    # ['font-weight', 'font-style', 'color', 'text-decoration']:
                    if key in ['font-weight', 'font-style', 'text-decoration']:
                        kept_props.append(f"{key}:{value}")

            # 4. Only rebuild the rule if there are properties left to keep
            if kept_props:
                # Clean up selector (handling the @import edge case if attached to the first match)
                if ";" in selector: 
                    selector = selector.split(";")[-1]
                    
                new_rule = f"{selector}{{{';'.join(kept_props)}}}"
                cleaned_output.append(new_rule)

    return "\n".join(cleaned_output)

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
        body_tag.name = "div"
        body_html_content = body_tag.prettify()

    style_tag = soup.find("style")
    if style_tag:
        cleaned_style_content = filter_bold_italic(style_tag.prettify())
        style_html_content = f"""<style type="text/css">{cleaned_style_content}</style>"""
    return body_html_content, style_html_content
    

def export_tab_as_html(creds, doc_id, tab_name, tab_id):
    """
    Finds a specific tab by name in a Google Doc and exports it as HTML.
    
    Args:
        creds: Valid Google OAuth2 credentials object.
        doc_id (str): The ID of the Google Doc.
        tab_name (str): The title of the tab you want to export.
        tab_id (str): The id of the tab you want to export.
    """
    target_dir = os.path.join("website", tab_name.replace(" ","-").lower())
    os.makedirs(target_dir, exist_ok=True)
    export_url = (f"https://docs.google.com/document/d/{doc_id}/export"
            f"?format=html&id={doc_id}&tab={tab_id}")

    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(export_url, headers=headers)
    while response.status_code != 200:
        time.sleep(1)
        response = requests.get(export_url, headers=headers)

    body_html_content, style_html_content = clean_content(response.text)
    with open('base.html', 'r', encoding='utf-8') as file:
        template_content = file.read()
        template = jinja2.Template(template_content)
        rendered_html = template.render(title=tab_name, body=body_html_content, style=style_html_content)

    with open(f"{target_dir}/index.html", 'wb') as f:
        f.write(rendered_html.encode('utf-8'))

    print(f"Successfully exported Google Doc '{doc_id}' as '{target_dir}/index.html'")

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

def doc_has_changed(creds, doc_id):
    """
    Returns True if the Google Doc has changed since the last check.
    Uses ONLY the Docs API (document.revisionId).

    True  -> doc changed OR no timestamp file yet
    False -> doc unchanged
    """
    timestamp_file = f"{doc_id}.timestamp"

    # --- Fetch revisionId from Docs API ---
    docs = build("docs", "v1", credentials=creds)
    doc = docs.documents().get(documentId=doc_id, fields="revisionId").execute()
    remote_rev = str(doc["revisionId"])   # revisionId is an integer-like string

    # --- If no saved revision, store and return True ---
    if not os.path.exists(timestamp_file):
        with open(timestamp_file, "w") as f:
            f.write(remote_rev)
        return True

    # --- Load stored revision ---
    with open(timestamp_file, "r") as f:
        local_rev = f.read().strip()

    # --- If different, update and return True ---
    if local_rev != remote_rev:
        with open(timestamp_file, "w") as f:
            f.write(remote_rev)
        return True

    # Same revision → no change
    return False

if __name__ == '__main__':
    if len(sys.argv) == 2:
        # e.g. doc_id = '11azwsMnSUPpR9ClIHSqZ3AcLvKdo0VqBMQyO9GacI9M'
        doc_id = sys.argv[1]
        tab_id = None
        print(f"Exporting all tabs in doc: {doc_id}")
    elif len(sys.argv) == 3:
        # e.g. doc_id = '11azwsMnSUPpR9ClIHSqZ3AcLvKdo0VqBMQyO9GacI9M'
        #      tab_id = 't.3fbogwqz9zik'
        doc_id = sys.argv[1]
        tab_id = sys.argv[2]
        print(f"Exporting tab {tab_id} from doc: {doc_id}")
    else:
        print_usage()
        exit()

    print(doc_id)
    creds = get_creds()

    if doc_has_changed(creds, doc_id) is False and tab_id is None:
        exit()

    tabs = get_tabs_from_doc(creds, doc_id)

    if tab_id:
        tabs = {key: value for key, value in tabs.items() if value == tab_id}

    for tab in tabs:
        export_tab_as_html(creds, doc_id, tab, tabs[tab])
        time.sleep(1)
