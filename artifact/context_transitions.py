"""Retrospective description of recorded projections, not physical drift inference."""
from pathlib import Path
import csv,datetime,hashlib,json

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pointer(parts):return '/'+ '/'.join(str(x).replace('~','~0').replace('/','~1') for x in parts)

def leaves(value, semantic=(), raw=()):
    """Retain raw JSON pointers, but align named collections by stable record identity.

    Gate/target/coupling records: operation and ordered qubit tuple.
    Parameter/property records: name. Other lists retain order (including qubits).
    No sorting of physical qubit order, no numerical tolerance and no deduplication.
    """
    if isinstance(value,dict):
        result={}
        for k,v in value.items():result.update(leaves(v,semantic+(k,),raw+(k,)))
        return result
    if isinstance(value,list):
        result={};seen=set()
        for i,item in enumerate(value):
            if isinstance(item,dict) and 'name' in item:
                key='name='+item['name']
            elif isinstance(item,dict) and 'qubits' in item and ('gate' in item or 'operation' in item):
                key='operation='+item.get('gate',item.get('operation'))+';qubits='+','.join(map(str,item['qubits']))
            else:key=str(i)
            if key in seen:raise ValueError('Duplicate record identity at '+pointer(raw))
            seen.add(key);result.update(leaves(item,semantic+(key,),raw+(i,)))
        return result
    return {pointer(semantic):{'json_pointer':pointer(raw),'value':value}}

def raw_leaves(value,raw=()):
    if isinstance(value,dict):return {k:v for a,b in value.items() for k,v in raw_leaves(b,raw+(a,)).items()}
    if isinstance(value,list):return {k:v for a,b in enumerate(value) for k,v in raw_leaves(b,raw+(a,)).items()}
    return {pointer(raw):value}

def reordered(value):
    if isinstance(value,dict):return {k:reordered(v) for k,v in reversed(list(value.items()))}
    if isinstance(value,list):
        values=[reordered(x) for x in value]
        named=all(isinstance(x,dict) and ('name' in x or ('qubits' in x and ('gate' in x or 'operation' in x))) for x in value)
        return list(reversed(values)) if named else values
    return value

def group(path):
    if '/name=T1/' in path or '/name=T2/' in path:return 'Coherence: T1, T2 (q0, q1)'
    if 'operation=cz;' in path:return 'CZ error (both directions)'
    if 'operation=sx;' in path:return 'SX error (q0, q1)'
    if '/name=threshold/' in path:return 'Measurement threshold (q0, q1)'
    if 'operation=measure;' in path or any('/name='+n+'/' in path for n in ['prob_meas0_prep1','prob_meas1_prep0','readout_error']):return 'Readout errors (q0, q1)'
    raise ValueError('Unclassified observed change: '+path)

def reconstruct(root,out,check):
    base=root/'data/numerical/campaign/windows'
    state=read(root/'data/numerical/campaign/campaign_state.json')
    # The usable set is inherited exactly as in v5, not reselected by this description.
    usable={w['candidate_id']:w for w in state['accepted_windows'] if w.get('usable_transition_window')}
    rows=[];details=[];provenance=[]
    for candidate in sorted(usable):
        d=base/candidate;w=read(d/'window.json');old=w['stale_reference']['reference_candidate_id']
        a_path=base/old/'workload_context_projection.json';b_path=d/'workload_context_projection.json'
        a=read(a_path);b=read(b_path);la=leaves(a);lb=leaves(b)
        check('context:'+candidate+':selected_complete_reference',read(base/old/'calibration_reference.json')['complete'],True)
        differences=[]
        for path in sorted(la.keys()|lb.keys()):
            av=la.get(path);bv=lb.get(path)
            if av is None or bv is None or av['value']!=bv['value']:
                differences.append({'window':w['label'],'candidate':candidate,'stale_reference':old,'semantic_path':path,'old_json_pointer':av['json_pointer'] if av else None,'new_json_pointer':bv['json_pointer'] if bv else None,'old_present':av is not None,'new_present':bv is not None,'old_value':av['value'] if av else None,'new_value':bv['value'] if bv else None,'group':group(path)})
        ra=raw_leaves(a);rb=raw_leaves(b)
        raw_count=sum(p not in ra or p not in rb or ra[p]!=rb[p] for p in ra.keys()|rb.keys())
        check('context:'+candidate+':observed_raw_and_aligned_leaf_counts',raw_count,len(differences))
        for label,projection in [('old',a),('new',b)]:
            check('context:'+candidate+':'+label+'_named_collection_order_invariance',{k:v['value'] for k,v in leaves(projection).items()},{k:v['value'] for k,v in leaves(reordered(projection)).items()})
        reference=read(base/old/'calibration_reference.json')
        ready=reference['ready_at'];opened=w['opened_at']
        age=(datetime.datetime.fromisoformat(opened.replace('Z','+00:00'))-datetime.datetime.fromisoformat(ready.replace('Z','+00:00'))).total_seconds()
        check('context:'+candidate+':reference_age_existing_anchor',age,w['stale_reference']['reference_age_seconds'],1e-5)
        groups=sorted({x['group'] for x in differences})
        rows.append({'window':w['label'],'candidate':candidate,'stale_reference':old,'changed_scalar_leaves':len(differences),'changed_property_groups':'; '.join(groups),'reference_age_at_window_open_s':age,'old_reference_ready_at':ready,'window_opened_at':opened})
        details.extend(differences)
        provenance.append({'candidate':candidate,'stale_reference':old,'old_projection':a_path.relative_to(root).as_posix(),'old_sha256':digest(a_path),'new_projection':b_path.relative_to(root).as_posix(),'new_sha256':digest(b_path),'selection_source':(d/'window.json').relative_to(root).as_posix(),'selection_sha256':digest(d/'window.json')})
    check('context:one_row_per_inherited_usable_window',len(rows),len(usable))
    for name,data in [('context_transitions.csv',rows),('context_changed_leaves.csv',details)]:
        with (out/name).open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    result={'scope':'Retrospective metadata description; not a new test, endpoint, transition definition, or causal drift analysis.','rows':rows,'provenance':provenance,'focal_C07_to_C08':[x for x in details if x['candidate']=='C08'],'changed_scalar_leaves_total':len(details),'count_definition':'Scalar leaves after alignment of named record collections; duplicate views remain separate JSON leaves, not independent physical properties. Raw positional counts coincide for these recorded files.','reference_age_definition':'Selected stale reference ready_at to current window opened_at, as in v5.'}
    (out/'context_transitions.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    table=[r'\begin{tabularx}{\linewidth}{@{}llrYr@{}}\toprule',r'Window / candidate & Stale ref. & Leaves & Changed property groups & Age (s)\\\midrule']
    for x in rows:
        table.append(f"{x['window']}/{x['candidate']} & {x['stale_reference']} & {x['changed_scalar_leaves']} & {x['changed_property_groups']} & {x['reference_age_at_window_open_s']:.1f}"+r'\\')
    table += [r'\bottomrule',r'\end{tabularx}']
    (out/'tables/context_transitions.tex').write_text('\n'.join(table)+'\n',encoding='utf-8')
    return {'windows':len(rows),'changed_scalar_leaves_total':len(details),'output':'context_transitions.json','focal_C07_to_C08':result['focal_C07_to_C08']}
