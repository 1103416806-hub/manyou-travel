import type {Activity,Plan} from './types';

export type DiningArea={name:string;lat:number;lng:number;radius:number;source_url:string;reason:string};

// Curated area suggestions for the bundled Hangzhou example, not restaurant POIs.
// WGS84 reference geometry: OpenStreetMap, checked 2026-09-13.
const areas:Record<string,DiningArea>={
 'd1-meal':{name:'北山街东段',lat:30.2627230,lng:120.1509942,radius:180,source_url:'https://www.openstreetmap.org/way/29021290',reason:'可在断桥北岸的北山街东段寻找午餐，再继续白堤与孤山的下午行程。'},
 'd2-meal':{name:'之江文化中心周边',lat:30.1621809,lng:120.0964232,radius:180,source_url:'https://www.openstreetmap.org/relation/19222157',reason:'上午看展后，可先在之江文化中心周边寻找午餐，再安排下午的馆区间交通。'},
 'd3-meal':{name:'龙井路沿线',lat:30.2272857,lng:120.1087497,radius:180,source_url:'https://www.openstreetmap.org/way/583614082',reason:'从龙井村前往双峰馆区时，可沿龙井路寻找合适的餐馆，把午餐安排在茶山行程中。'},
 'd4-meal':{name:'桥弄街东段',lat:30.3207155,lng:120.1331645,radius:150,source_url:'https://www.openstreetmap.org/way/345074150',reason:'游览拱宸桥后，可在桥西一侧的桥弄街周边寻找午餐，再继续历史街区的行程。'},
 'd5-meal':{name:'深潭口—河渚街周边',lat:30.2741947,lng:120.0665378,radius:160,source_url:'https://www.openstreetmap.org/node/7309303306',reason:'可在湿地游览与河渚街安排之间留出午餐时间，结合园区实际开放路线选择餐馆。'},
};

export function diningAreaFor(activity:Activity,mode:Plan['mode'],destination:string):DiningArea|undefined{
 if(mode!=='demo'||destination!=='杭州'||activity.category!=='food'||!activity.source_ids.includes('sample-hangzhou'))return undefined;
 return areas[activity.id];
}
