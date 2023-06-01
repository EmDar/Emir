import requests

response = requests.get('http://localhost:5000')

if response.status_code == 200:
    print('Success! The server responded with:', response.text)
else:
    print('Oh no! Something went wrong.')
