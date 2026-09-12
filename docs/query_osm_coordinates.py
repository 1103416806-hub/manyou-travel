"""One-off, cached OpenStreetMap research; not an application geocoder."""
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).parent
query = '''[out:json][timeout:60];
nwr(30.10,120.00,30.36,120.22)["name"~"断桥|孤山|白堤|西泠印社|北山街|浙江省博物馆|中国丝绸博物馆|南宋御街|河坊街|龙井村|中国茶叶博物馆|茅家埠|浴鹄湾|拱宸桥|桥西历史|刀剪剑|小河直街|西溪国家湿地|河渚街|中国湿地博物馆|西溪东门"];
out center;'''
url = 'https://overpass.kumi.systems/api/interpreter?' + urllib.parse.urlencode({'data':query})
request = urllib.request.Request(url,headers={'User-Agent':'ManyouPortfolio-coordinate-review/0.1 (one-time small POI verification)'})
data=json.load(urllib.request.urlopen(request,timeout=80))
(ROOT/'map-coordinates-osm-raw.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'map-coordinates-query.txt').write_text(query,encoding='utf-8')
for e in data['elements']:
    print(json.dumps({'type':e['type'],'id':e['id'],'name':e.get('tags',{}).get('name'),'lat':e.get('lat'),'lon':e.get('lon'),'center':e.get('center'),'tags':e.get('tags',{})},ensure_ascii=False))
