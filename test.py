import requests

response = requests.get("https://api.telegram.org/bot748225256:AAFFhmHUnWHXnj8J4-gnbeLZNJXLw2F3jak/getUpdates")
print(response.content)