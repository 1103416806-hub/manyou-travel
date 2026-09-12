"""One-time cached manual POI verification; not shipped as app integration.
Policy: https://operations.osmfoundation.org/policies/nominatim/
Single thread, one machine, > 1 s between requests, persistent cache.
"""
import json,pathlib,sys,time,urllib.parse,urllib.request
sys.stdout.reconfigure(encoding='utf-8')
root=pathlib.Path(__file__).parent
cache_path=root/'map-coordinates-nominatim-raw.json'
cache=json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
names=['浙江省博物馆','中山中路','桥西直街','西溪湿地东门']
for name in names:
    if name not in cache:
        time.sleep(2)
        url='https://nominatim.openstreetmap.org/search?'+urllib.parse.urlencode({'q':'杭州 '+name,'format':'jsonv2','limit':3,'viewbox':'120.00,30.36,120.22,30.1','bounded':1})
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ManyouPortfolio-coordinate-review/0.1 (one-time POI verification)'})
            cache[name]={'query_url':url,'results':json.load(urllib.request.urlopen(req,timeout=20))}
        except Exception as e:
            cache[name]={'query_url':url,'error':str(e),'results':[]}
        cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8')
    print(name,json.dumps(cache[name],ensure_ascii=False),flush=True)
