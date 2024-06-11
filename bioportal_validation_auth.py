import os
import importlib
import requests

class TokenAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, token, *args, **kwargs):
        self.token = token
        super().__init__(*args, **kwargs)

    def send(self, request, *args, **kwargs):
        request.headers['Authorization'] = f'Bearer {self.token}'
        return super().send(request, *args, **kwargs)

def install_token_adapter(token):
    session = requests.Session()
    adapter = TokenAdapter(token)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    requests.Session = lambda: session

def configure_token():
    token = os.getenv('CBIO_AUTH_TOKEN')
    if token:
        print("Token detected: setting up adapter..")
        install_token_adapter(token)

if __name__ == "__main__" and (__package__ is None or __package__ == ''):
    configure_token()
    print("Running importer.")
    importlib.import_module('importer')