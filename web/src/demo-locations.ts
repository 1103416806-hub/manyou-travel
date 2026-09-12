import coordinateData from '../../manyou/demo_locations.json';
import type {Activity,Plan} from './types';

type Location = {lat:number;lng:number;source_url:string;note:string};
const locations=coordinateData.locations as Record<string,Location>;
export function demoLocationFor(activity:Activity,mode:Plan['mode']):Location|undefined{return mode==='demo'&&activity.source_ids.includes('sample-hangzhou')?locations[activity.title]:undefined;}

// Migrate only the bundled Hangzhou example. Preserve user dates, order and edits.
export function normalizeDemoLocations<T extends Plan|null>(plan:T):T{
 if(!plan||plan.mode!=='demo'||!plan.id.startsWith('demo-')||plan.destination!=='杭州')return plan;
 return {...plan,days:plan.days.map(day=>({...day,activities:day.activities.map(activity=>{
  if(!activity.source_ids.includes('sample-hangzhou'))return activity;
  const location=locations[activity.title];
  return {...activity,lat:location?.lat??null,lng:location?.lng??null};
 })}))} as T;
}
