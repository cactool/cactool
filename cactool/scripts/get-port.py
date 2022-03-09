import json

try:
    with open("config.json") as file:
        config = json.load(file)
        print(config["port"])
except:
    print(8000)
