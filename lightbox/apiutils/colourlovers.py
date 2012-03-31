import requests, urllib, json, time
from frack.projects.lightbox import utils

while True:
  g = requests.get("http://www.colourlovers.com/api/palettes/top?format=json&numResults=100")
  colourpallets=json.loads(g.text)
  for pallet in colourpallets:
    outputjson = []
    for color, channel in zip(pallet["colors"] * 2, range(5)):
      color = utils.HexToRgb(color)
      outputjson.append(
          {"channel": channel,"color": color,"opacity": 1,"steps": 40})
    postdata = {"json":json.dumps(outputjson)}
    data = urllib.urlencode(postdata)
    print postdata
    r  = requests.post("http://bugs.local.frack.nl:8000/", data=data)
    print r
    time.sleep(60)
