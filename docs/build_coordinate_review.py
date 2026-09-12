"""Produce reviewed representative coordinates from cached query results."""
import ast,json,pathlib
root=pathlib.Path(__file__).parent
tree=ast.parse((root.parent/'manyou'/'demo.py').read_text(encoding='utf-8'))
routes=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROUTES' for t in n.targets))
raw=json.loads((root/'map-coordinates-nominatim-raw.json').read_text(encoding='utf-8'))
# An exact named object can still be an area or a long road, not a verified entrance.
choices={
'断桥残雪':('断桥',0,'桥梁步行路段代表点；不是出入口或导航路网核验。'),
'孤山与白堤':('孤山',0,'选取孤山岛屿代表点；行程名称同时包含白堤，坐标不代表整段步行路线或入口。'),
'西泠印社外街':('西泠印社',0,'选取西泠印社景点 POI，未查到名为“外街”的独立道路对象；建议标题标注为西泠印社附近。'),
'北山街':('北山街',0,'北山街西段道路代表点；不是整条街的唯一中心或入口。'),
'浙江省博物馆之江馆区':('浙江省博物馆',1,'精确匹配浙江省博物馆(之江馆)，非孤山馆；馆舍面状对象代表点，不表示入口。'),
'中国丝绸博物馆':('中国丝绸博物馆',0,'馆区面状对象代表点；不表示入口。'),
'南宋御街':('中山中路',0,'选取中山中路清河坊步行段代表点；杭州政协资料证明南宋御街与中山路基本重叠，非遗址陈列馆坐标。'),
'河坊街':('河坊街',2,'选取清河坊社区段道路代表点；不是整条街的唯一中心。'),
'龙井村':('龙井村',0,'村落代表点；不表示停车、入口或步道起点。'),
'中国茶叶博物馆双峰馆区':('中国茶叶博物馆',0,'精确匹配双峰馆区，非龙井馆区；馆区面状对象代表点。'),
'茅家埠':('茅家埠',0,'选取村落代表点，未使用同名水湾中心。'),
'浴鹄湾':('浴鹄湾',1,'仅选取同名杨公堤公交站作为到访参考点；景区本体为水面，不把湖心当作行走目标。UI 应注明“浴鹄湾公交站附近”。'),
'拱宸桥':('拱宸桥',1,'桥梁台階路段代表点；没有选用同名街区或公交站。'),
'桥西历史街区':('桥西直街',0,'选取街区内桥西直街步行段代表点；拱墅区官方文旅资料确认桥西直街属于桥西历史街区。'),
'中国刀剪剑博物馆':('中国刀剪剑博物馆',0,'馆舍面状对象代表点；不表示入口。'),
'小河直街':('小河直街',0,'步行街路段代表点；不表示整条街唯一中心或入口。'),
'西溪国家湿地公园':('西溪国家湿地公园',0,'大型湿地保护区代表点，仅用于区域展示；不是入园门、可行走停靠点，不应用于导航终点。'),
'西溪河渚街':('河渚街',0,'河渚街道路代表点；不表示停车点或景区入口。'),
'西溪中国湿地博物馆':('中国湿地博物馆',0,'馆舍面状对象代表点；不表示入口。'),
'西溪东门周边':('西溪湿地东门',0,'仅为紫金港路上的“西溪湿地东门”公交站参考点，非景区入口坐标。UI 应注明公交站附近。'),
}
items=[]
for day,(_,_,stops) in enumerate(routes,1):
    for name,lat,lon,*_ in stops:
        item={'name':name,'day':day,'original_lat':lat,'original_lng':lon,'lat':None,'lng':None,'status':'unverified','source_url':None,'note':'本次未找到能够明确匹配的地理对象，不能继续把旧演示坐标视作已核验。'}
        if name in choices:
            query,index,note=choices[name]
            results=raw.get(query,{}).get('results',[])
            if len(results)>index:
                r=results[index]
                item.update(lat=float(r['lat']),lng=float(r['lon']),status='osm_representative',source_url=f"https://www.openstreetmap.org/{r['osm_type']}/{r['osm_id']}",osm_type=r['osm_type'],osm_id=r['osm_id'],osm_name=r['name'],feature_type=r['type'],query_url=raw[query]['query_url'],note=note)
        if name=='南宋御街':
            item['identity_source_url']='https://www.hzzx.gov.cn/content/2024-10/28/content_8805726.htm'
        if name=='桥西历史街区':
            item['identity_source_url']='https://www.gongshu.gov.cn/art/2024/4/30/art_1229789753_59080391.html'
        items.append(item)
data={'coordinate_system':'WGS84 (EPSG:4326)','retrieved_at':'2026-09-12','attribution':'© OpenStreetMap contributors','license':'ODbL 1.0','license_url':'https://www.openstreetmap.org/copyright','method':'一次性人工指定景点列表，Nominatim 单线程请求间隔 2 秒并缓存；无运行时公共 Nominatim 服务接入。前两次 Overpass 请求分别 504 和超时，无可用结果。','policy_url':'https://operations.osmfoundation.org/policies/nominatim/','limits':'地理数据库匹配只能核验坐标出处及对象名称，不能核验现场开放、景点入口、可步行性或帖子事实。','items':items}
(root/'map-coordinates.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(f"Written {len(items)} records, {sum(i['lat'] is not None for i in items)} reviewed")
