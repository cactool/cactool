import json
import os

if "PORT" in os.environ:
    print(os.environ["PORT"])

try:
    with open("config.json") as file:
        config = json.load(file)
        print(config["port"])
except:
    print(8000)
