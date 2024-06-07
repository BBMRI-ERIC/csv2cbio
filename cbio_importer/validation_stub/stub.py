import requests


class TokenAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, token, *args, **kwargs):
        self.token = token
        super().__init__(*args, **kwargs)

    def send(self, request, *args, **kwargs):
        # Add the token to the request headers
        request.headers['Authorization'] = f'Bearer {self.token}'
        return super().send(request, *args, **kwargs)


# Function to install the adapter into requests
def install_token_adapter(token):
    session = requests.Session()
    adapter = TokenAdapter(token)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    requests.Session = lambda: session
