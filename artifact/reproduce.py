"""Offline v5.1 editorial reproduction from exported counts; no provider imports."""
from pathlib import Path
import argparse,copy,csv,datetime,hashlib,importlib.util,json,math,statistics,sys,tempfile
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'code/historical'))
from athena_aegis.campaign_b.analysis import analyze,primary_p5_records
from athena_aegis.campaign_b.endpoints import window_recovery_success
from athena_aegis.calibration.model import CalibrationSpecification,EmpiricalQuantileCalibration
P2='P2-global-calibrated';P5='P5-recovery-enforcement';HELD='held_physical_result';FALLBACK='classical_fallback'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def local_module(name):
 """Load an editorial helper by its packaged path, including under python -I."""
 spec=importlib.util.spec_from_file_location('paper25_editorial_'+name,ROOT/(name+'.py'))
 if spec is None or spec.loader is None:raise ImportError('Cannot load packaged helper: '+name)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module
def instant(v):return datetime.datetime.fromisoformat(v.replace('Z','+00:00')) if v else None
def elapsed(a,b):return (instant(b)-instant(a)).total_seconds() if a and b else None
def describe(v):
 v=[float(x) for x in v if x is not None]
 return {'n':len(v),'minimum':min(v),'maximum':max(v),'mean':statistics.mean(v),'median':statistics.median(v),'population_sd':statistics.pstdev(v)} if v else {'n':0}
def export_csv(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 if not rows:return
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def rank(scores,s):return (1+sum(x>=s for x in scores))/(len(scores)+1) if scores and s is not None else None
def exact_kernel(features,reps):
 """Independent 4-amplitude ZZFeatureMap: H on each qubit, P(2*x), CX-P(2*phi)-CX."""
 h=np.array([[1,1],[1,-1]],complex)/math.sqrt(2);hh=np.kron(h,h);states=[]
 for x0,x1 in features:
  v=np.array([1,0,0,0],complex)
  for _ in range(reps):
   v=hh@v
   for b in range(4):
    b0=b&1;b1=(b>>1)&1
    phase=2*x0*b0+2*x1*b1+2*(math.pi-x0)*(math.pi-x1)*(b0^b1)
    v[b]*=np.exp(1j*phase)
  states.append(v)
 return np.array([[abs(np.vdot(v,w))**2 for w in states] for v in states])
def from_counts(u,pairs):
 counts=u.get('counts')
 if counts is None:return None
 if len(counts)!=len(pairs):raise ValueError('wrong histogram count')
 m=np.zeros((3,3))
 for c,(i,j) in zip(counts,pairs):
  if not c or any(not isinstance(n,int) or n<0 for n in c.values()) or sum(c.values())!=128:raise ValueError('invalid frozen shot histogram')
  m[i,j]=m[j,i]=c.get('00',0)/sum(c.values())
 return m
def binding(u):
 """Recheck J1/J2/J3 from exported fields; recorded J4/MAC verdict is a trust premise."""
 b=u.get('binding',{});t=u['timings'];recorded=b.get('checks',{})
 ts=[t.get(k) for k in ['provider_created_at','provider_running_at','provider_finished_at']]
 j1=(u.get('provider_final_status')=='DONE' and all(ts) and instant(ts[0])<=instant(ts[1])<=instant(ts[2]))
 w=b.get('window_workload_digest')
 j2=bool(w and b.get('pre_submit_workload_digest')==w and b.get('post_result_workload_digest')==w)
 j3=bool(w and b.get('historical_workload_digest')==w)
 check={'J1_provider_done_with_monotonic_timestamps':bool(j1),'J2_local_bracket_pre_and_post_snapshots':j2,'J3_historical_properties_at_running_match':j3}
 trust=[recorded.get('J4_integrity'),u.get('binding_valid')]
 bound=all(check.values()) and all(x is True for x in trust)
 return bound,check,trust
def comparator(u,correct):
 bound,check,trust=binding(u)
 b=u.get('binding',{});t=u.get('timings',{})
 # Preserve UNKNOWN for unavailable inputs, rather than confusing absence with contradiction.
 available={
  'J1_provider_done_with_monotonic_timestamps':bool(u.get('provider_final_status') and all(t.get(k) for k in ['provider_created_at','provider_running_at','provider_finished_at'])),
  'J2_local_bracket_pre_and_post_snapshots':all(b.get(k) for k in ['window_workload_digest','pre_submit_workload_digest','post_result_workload_digest']),
  'J3_historical_properties_at_running_match':all(b.get(k) for k in ['window_workload_digest','historical_workload_digest'])}
 missing=[]
 if correct is None:missing.append('numerical_oracle')
 if not u.get('counts'):missing.append('counts')
 if u.get('physical_execution_evidence') is None:missing.append('physical_evidence')
 if any(x is None for x in trust):missing.append('recorded_integrity_or_authentication_verdict')
 missing.extend(k for k,v in available.items() if not v)
 # Known failure takes precedence; missing required evidence otherwise stays UNKNOWN.
 fail=(correct is False or u.get('physical_execution_evidence') is False or any(x is False for x in trust) or any(available[k] and not v for k,v in check.items()))
 return ('REJECT' if fail else 'UNKNOWN' if missing else 'ACCEPT_PHYSICAL' if bound else 'REJECT'),missing
def tail(k,n,p):return sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(k,n+1))
def root_increasing(f,target):
 lo,hi=0.,1.
 for _ in range(100):
  mid=(lo+hi)/2
  if f(mid)<target:lo=mid
  else:hi=mid
 return (lo+hi)/2
def intervals(x,n):
 return [0. if x==0 else root_increasing(lambda p:tail(x,n,p),.025),1. if x==n else root_increasing(lambda p:tail(x+1,n,p),.975)]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'reproduced');args=ap.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 checks=[]
 def check(name,actual,expected,tol=None):
  same=(abs(actual-expected)<=tol if tol is not None and actual is not None and expected is not None else actual==expected)
  checks.append({'check':name,'pass':bool(same),'actual':actual,'expected':expected,'tolerance':tol})
 manifest=read(ROOT/'INPUT_MANIFEST.json')
 for f in manifest['files']:check('input_hash:'+f['path'],sha(ROOT/f['path']),f['sha256'])
 if any(not c['pass'] for c in checks):write(out/'reproduction_report.json',{'status':'INPUT_INTEGRITY_FAILED','checks':checks});raise SystemExit(2)
 campaign=ROOT/'data/numerical/campaign';state=read(campaign/'campaign_state.json');cfg=read(ROOT/'data/numerical/workload.json')
 refmatrix=exact_kernel(cfg['features'],cfg['repetitions']);check('classical_reference_independent',float(np.max(np.abs(refmatrix-np.array(cfg['classical_reference_reconstructed'])))),0.,1e-12)
 write(out/'classical_reference.json',refmatrix.tolist())
 windows={};units={};computed={};refscores={};refs={};allunits=[]
 for d in sorted((campaign/'windows').glob('C*')):
  w=read(d/'window.json');uu=lines(d/'units.jsonl');rr=lines(d/'policy_records.jsonl');windows[d.name]={'window':w,'units':uu,'records':rr}
  projection=read(d/'workload_context_projection.json')
  projected_digest=hashlib.sha256(json.dumps({"workload_context":projection},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
  for u in uu:
   uid=u['assignment']['unit_id'];key=(d.name,uid,u['attempt']);units[key]=u
   m=from_counts(u,cfg['pair_order']);bd,bcs,trust=binding(u)
   if u.get('binding'):
    check(uid+':window_projection_digest',projected_digest,u['binding']['window_workload_digest'])
    for k,v in bcs.items():check('/'.join(map(str,key))+':'+k,v,u['binding']['checks'].get(k))
   if m is None:rel=absmax=correct=None
   else:
    diff=m-refmatrix;rel=float(np.linalg.norm(diff)/np.linalg.norm(refmatrix));absmax=float(np.max(np.abs(diff)))
    correct=rel<=cfg['relative_threshold']+cfg['comparison_tolerance'] and absmax<=cfg['absolute_threshold']+cfg['comparison_tolerance']
    check(uid+':matrix',float(np.max(np.abs(m-np.array(u['kernel_matrix'])))),0.,1e-12)
    check(uid+':relative',rel,u['oracle_metrics']['relative_frobenius_error'],1e-12)
    check(uid+':absolute',absmax,u['oracle_metrics']['maximum_absolute_error'],1e-12)
    check(uid+':score',rel,u['nonconformity_score'],1e-12);check(uid+':oracle',bool(correct),u['oracle_service_correct'])
   decision,missing=comparator(u,correct)
   row={'candidate':d.name,'unit':uid,'attempt':u['attempt'],'phase':u['assignment']['phase'],'terminal_state':u['terminal_state'],'counts_available':m is not None,'bound':bd,'relative_error':rel,'maximum_absolute_error':absmax,'oracle_correct':None if correct is None else bool(correct),'relative_margin':None if rel is None else .15-rel,'absolute_margin':None if absmax is None else .20-absmax,'direct_comparator':decision,'unknown_fields':';'.join(missing),'sealed_at':u.get('sealed_at')}
   computed[key]=row;allunits.append(row)
  rp=d/'calibration_reference.json'
  if rp.exists():
   ref=read(rp);refs[d.name]=ref;score=[]
   for s in ref['scores']:
    x=computed[(d.name,s['unit_id'],s['attempt'])];score.append(x['relative_error']);check('reference:'+s['unit_id'],x['relative_error'],s['score'],1e-12);check('reference_bound:'+s['unit_id'],x['bound'],True)
   check('reference_n:'+d.name,len(score),ref['required_units']);refscores[d.name]=score
   check('reference_ready_after_all_seals:'+d.name,all(instant(units[(d.name,s['unit_id'],s['attempt'])]['sealed_at'])<=instant(ref['ready_at']) for s in ref['scores']),True)
   check('reference_threshold:'+d.name,sorted(score)[37],ref['threshold_38th_order_statistic'],1e-12)
 accepted={e['candidate_id']:e for e in state['accepted_windows']};usable={k for k,e in accepted.items() if e.get('usable_transition_window') is True}
 rows=[];rebuilt={};outcomes=[];ages=[];refdistributions=[]
 for c,wd in windows.items():
  w=wd['window'];records=wd['records'];rebuilt[c]=[];old=(w.get('stale_reference') or {}).get('reference_candidate_id')
  candidates=[k for k in refs if instant(refs[k]['ready_at'])<instant(w['opened_at']) and k in accepted]
  selected=max(candidates,key=lambda k:instant(refs[k]['ready_at'])) if candidates else None
  check('selected_old_reference:'+c,old,selected)
  if old:
   opening_age=elapsed(refs[old]['ready_at'],w['opened_at']);check('age_at_open:'+c,opening_age,w['stale_reference']['reference_age_seconds'],1e-5)
  for r in records:
   uid=r['probe_id'];key=(c,uid,r.get('selected_attempt',1));u=units[key];n=computed[key];rec=copy.deepcopy(r);isprimary=r['phase']=='pre_recovery_service'
   refid=(old if isprimary else c) if r['policy_id']==P2 else c
   p=rank(refscores.get(refid,[]),n['relative_error'])
   if r['policy_id'] in (P2,P5) and r.get('p_value') is not None:check(uid+':'+r['policy_id']+':rank',p,r['p_value'],1e-12)
   # P4 is inherited ancillary output. P2 and P5 decisions are rebuilt independently.
   if r['policy_id']==P2:
    served=n['bound'] and p is not None and p>.05;source=HELD if served else None
   elif r['policy_id']==P5:
    complete=c in refs and refs[c]['complete'] and len(refscores[c])==39
    # Same exported context and fixed support; J4 remains a recorded authentication premise.
    served=n['bound'] and complete and p is not None
    source=(HELD if p>.05 else FALLBACK) if served else None
   else:continue
   oracle=True if source==FALLBACK else n['oracle_correct']
   check(uid+':'+r['policy_id']+':served',bool(served),r['served']);check(uid+':'+r['policy_id']+':source',source,r.get('served_source'))
   check(uid+':'+r['policy_id']+':served_oracle',oracle,r.get('oracle_service_correct'))
   rec.update(served=bool(served),served_source=source,oracle_service_correct=oracle,context_bound=n['bound'],p_value=p)
   if r['policy_id']==P5:
    assurance=bool(served);check(uid+':assurance',assurance,r['assurance_valid_for_serving']);rec['assurance_valid_for_serving']=assurance
    if isprimary:
     lag=elapsed(r.get('t0_support_invalid_or_held'),r.get('t3_safely_served_or_terminal'))
     if c in refs:
      check(uid+':reference_clock_anchor',r.get('t2_recovery_ready'),refs[c]['ready_at'])
      check(uid+':calibration_clock_anchor',r.get('t1_recovery_started'),w['calibration_started_at'])
     if 'total_recovery_latency_seconds' in r:check(uid+':clock',lag,r['total_recovery_latency_seconds'],1e-5)
     rec['total_recovery_latency_seconds']=lag
     # Origin checks require contemporaneous data; no later historical fields are backdated.
     available=elapsed(u.get('sealed_at'),r.get('t0_support_invalid_or_held'))
     check(uid+':sealed_before_HOLD',available is not None and available>=0,True)
     pold=rank(refscores.get(old,[]),n['relative_error']);pnew=rank(refscores.get(c,[]),n['relative_error'])
     rows.append({'candidate':c,'label':accepted.get(c,{}).get('label') or w.get('intended_label'),'probe':uid,'usable':c in usable,'relative_error':n['relative_error'],'maximum_absolute_error':n['maximum_absolute_error'],'relative_margin':n['relative_margin'],'absolute_margin':n['absolute_margin'],'direct_comparator':n['direct_comparator'],'input_available_by':u.get('sealed_at'),'hold_at':r.get('t0_support_invalid_or_held'),'availability_upper_bound_before_hold_s':available,'p2_rank':pold,'p5_rank':pnew,'rank_delta_new_minus_old':None if pnew is None or pold is None else pnew-pold,'p2_would_serve':pold is not None and pold>.05 and n['bound'],'p5_source':source,'p5_served':bool(served),'T0_T3_s':lag,'T0_T1_s':elapsed(r.get('t0_support_invalid_or_held'),r.get('t1_recovery_started')),'T1_T2_s':elapsed(r.get('t1_recovery_started'),r.get('t2_recovery_ready')) if c in refs else None,'old_reference':old,'old_reference_age_at_hold_s':elapsed(refs[old]['ready_at'],r.get('t0_support_invalid_or_held')) if old else None})
   rebuilt[c].append(rec)
  if c in usable:
   outcome=window_recovery_success(primary_p5_records(rebuilt[c]));outcomes.append({'candidate_id':c,'label':accepted[c]['label'],**outcome})
  held=[x for x in rows if x['candidate']==c]
  if old:ages.append({'candidate':c,'label':accepted.get(c,{}).get('label') or w.get('intended_label'),'old_reference':old,'old_ready_at':refs[old]['ready_at'],'window_opened_at':w['opened_at'],'age_at_window_open_s':opening_age,'age_at_first_hold_s':min(x['old_reference_age_at_hold_s'] for x in held) if held else None,'new_ready_at':refs.get(c,{}).get('ready_at')})
  for u in wd['units']:
   if u['assignment']['phase']=='calibration':
    x=computed[(c,u['assignment']['unit_id'],u['attempt'])];refdistributions.append({'candidate':c,'unit':x['unit'],'attempt':u['attempt'],'bound':x['bound'],'score':x['relative_error'],'reference_complete':c in refs})
 primary=[x for x in rows if x['usable']];incomplete=[x for x in rows if not x['usable']]
 joint={}
 for x in primary:
  k=('P2_serve' if x['p2_would_serve'] else 'P2_reject')+'/'+('P5_retained' if x['p5_source']==HELD else 'P5_fallback');joint[k]=joint.get(k,0)+1
 for k in ['P2_serve/P5_retained','P2_serve/P5_fallback','P2_reject/P5_retained','P2_reject/P5_fallback']:joint.setdefault(k,0)
 successes=sum(w['window_recovery_success'] for w in outcomes);n=len(outcomes);pvalue=tail(successes,n,.5);ci=intervals(successes,n);lower=root_increasing(lambda p:tail(successes,n,p),.05)
 canonical=read(ROOT/'data/analysis.json');cp=canonical['primary']
 for key,actual in [('usable_windows',n),('successes',successes),('exact_one_sided_p_value',pvalue),('one_sided_95_lower_bound',lower)]:check('canonical:'+key,actual,cp[key],1e-12)
 for i,x in enumerate(ci):check('canonical:CP95:'+str(i),x,cp['clopper_pearson_95'][i],1e-12)
 for w in outcomes:
  oldw=next(v for v in cp['windows'] if v['candidate_id']==w['candidate_id'])
  for k in ['window_recovery_success','retained_result_count','fallback_count']:check('canonical:'+w['candidate_id']+':'+k,w[k],oldw[k])
 # Execute original and patched analyzers against sanitized original records, without immutability traversal.
 historical=analyze(campaign,repo_root=ROOT,verify_campaign_a=False)
 for key in ['retained_result_rate','fallbacks','service_availability','p2_assurance_invalid_continuation','p5_assurance_invalid_continuation','incorrect_service_continuation','verification_probe_behavior','binding_failures']:
  check('canonical_secondary:'+key,historical['secondary'][key],canonical['secondary'][key])
 spec=importlib.util.spec_from_file_location('v5_corrected_analysis',ROOT/'code/v5_corrected/analysis.py');corrected=importlib.util.module_from_spec(spec);spec.loader.exec_module(corrected)
 patched=corrected.analyze(campaign,repo_root=ROOT,verify_campaign_a=False)
 check('actual_B_original_verdict',historical['h1_b_declared'],canonical['h1_b_declared']);check('actual_B_corrected_verdict',patched['h1_b_declared'],canonical['h1_b_declared'])
 # Actual endpoint reconstruction also runs through the historical analyzer with rebuilt records.
 with tempfile.TemporaryDirectory(prefix='paper25_v5_offline_') as td:
  base=Path(td);write(base/'campaign_state.json',state)
  for c,w in windows.items():
   d=base/'windows'/c;write(d/'window.json',w['window']);(d/'units.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in w['units']))
   (d/'policy_records.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rebuilt[c]))
  recalculated=analyze(base,repo_root=ROOT,verify_campaign_a=False)
  check('rebuilt_analyzer_successes',recalculated['primary']['successes'],successes);check('rebuilt_analyzer_p',recalculated['primary']['exact_one_sided_p_value'],pvalue,1e-12)
 tests=software_tests(corrected,units,computed)
 for t in tests:check('software:'+t['name'],t['pass'],True)
 flow=[]
 for c,w in windows.items():
  ww=w['window'];pu=[x for x in allunits if x['candidate']==c and x['phase']=='pre_recovery_service' and x['bound']];cal=[x for x in allunits if x['candidate']==c and x['phase']=='calibration' and x['bound']]
  flow.append({'candidate':c,'role':'bootstrap attempt' if ww['bootstrap'] else 'transition','status':ww['status'],'held_probes':len(pu),'bound_calibration':len(cal),'reference_complete':c in refs,'usable':c in usable,'window_success':next((v['window_recovery_success'] for v in outcomes if v['candidate_id']==c),None),'retained_only_success':next((v['retained_result_only_success'] for v in outcomes if v['candidate_id']==c),None)})
 summary={'confirmatory':{'usable_windows':n,'successes':successes,'exact_one_sided_p':pvalue,'CP95':ci,'one_sided_95_lower_bound':lower,'h1_b_established':pvalue<=.05 and patched['safety_gate']['safety_gate_pass'] and patched['kill_criteria']['KC-B4']['state']=='not_triggered','retained_only_windows':sum(w['retained_result_only_success'] for w in outcomes),'retained_outputs':sum(x['p5_source']==HELD for x in primary),'fallback_outputs':sum(x['p5_source']==FALLBACK for x in primary),'calibration_jobs':sum(len(refscores[c]) for c in usable)},'direct_comparator':{'usable_accepts':sum(x['direct_comparator']=='ACCEPT_PHYSICAL' for x in primary),'usable_probes':len(primary),'incomplete_accepts':sum(x['direct_comparator']=='ACCEPT_PHYSICAL' for x in incomplete),'incomplete_probes':len(incomplete),'deployed_latency_measured':False,'additional_utility_of_renewal_demonstrated':False,'trust_boundary':'Recorded physical provenance and J4/authentication verdicts; J1-J3 predicates recomputed from exported clocks/digests. No independent HMAC/provider verification.'},'joint':joint,'changed_decisions':[x for x in primary if x['p2_would_serve']!=(x['p5_source']==HELD)],'relative_errors':describe(x['relative_error'] for x in primary),'maximum_absolute_errors':describe(x['maximum_absolute_error'] for x in primary),'p2_ranks':describe(x['p2_rank'] for x in primary),'p5_ranks':describe(x['p5_rank'] for x in primary),'rank_deltas_new_minus_old':describe(x['rank_delta_new_minus_old'] for x in primary),'design_power':[{'hypothetical_pi':p,'n':10,'rejection_at_least':9,'power':tail(9,10,p)} for p in [.5,.6,.7,.8,.9,.95]],'count_reproduction':{'unit_records':len(allunits),'with_counts':sum(x['counts_available'] for x in allunits),'missing_by_terminal_state':{s:sum(not x['counts_available'] and x['terminal_state']==s for x in allunits) for s in sorted({x['terminal_state'] for x in allunits if not x['counts_available']})},'complete_references':len(refscores),'reference_scores':sum(map(len,refscores.values()))},'flow':flow,'C06_expired_before_calibration':[x['probe'] for x in primary if x['candidate']=='C06' and x['T0_T1_s']>1800]}
 export_csv(out/'units_reconstructed.csv',allunits);export_csv(out/'probes_usable.csv',primary);export_csv(out/'probes_incomplete.csv',incomplete);export_csv(out/'reference_ages.csv',ages);export_csv(out/'reference_scores.csv',refdistributions)
 write(out/'window_outcomes.json',outcomes);write(out/'summary.json',summary);write(out/'software_tests.json',tests)
 local_module('render_outputs').render(ROOT,out,summary,primary,outcomes,flow,refdistributions)
 context=local_module('context_transitions').reconstruct(ROOT,out,check)
 for name,module in list(sys.modules.items()):
  if name=='athena_aegis' or name.startswith('athena_aegis.'):
   file=getattr(module,'__file__',None)
   if file:check('isolated_import:'+name,Path(file).resolve().is_relative_to((ROOT/'code/historical').resolve()),True)
 failed=[x for x in checks if not x['pass']]
 report={'status':'PASS' if not failed else 'DISCREPANCIES','checks':len(checks),'failed':failed,'numerical_scope':'575 bound physical units from six count histograms each, including bootstrap and incomplete candidates; exact reference independently regenerated from frozen two-qubit circuit definition. Counts absent for unbound/submission-failed/cancelled units are not fabricated.','input_manifest_valid':True,'historical_original_and_corrected_verdict':{'original':historical['h1_b_declared'],'corrected':patched['h1_b_declared']},'hmac_authentication':'NOT REPEATED; keys excluded; recorded successful checks are premises','provider_reconciliation':'NOT REPEATED; no provider calls','independent_preacquisition_temporal_anchor':'NOT ESTABLISHED; local Git records are not independent timestamp attestation','environment':{'python':sys.version.split()[0],'numpy':np.__version__},'summary':summary}
 report['context_description']=context
 report['environment']['matplotlib']=__import__('matplotlib').__version__
 report['check_count_note']='v5 had 7435 checks. Additional checks validate new editorial inputs and ten descriptive context comparisons; historical numerical tolerances and the ten software tests are unchanged.'
 write(out/'reproduction_report.json',report)
 (out/'REPORT.md').write_text('# Offline numerical reproduction\n\nStatus: '+report['status']+'. '+str(len(checks))+' checks; '+str(len(failed))+' discrepancies.\n\n'+report['numerical_scope']+'\n\nReconstructed successes: '+str(successes)+'/'+str(n)+'; exact one-sided p='+str(pvalue)+'. H1-B not established. The direct comparator accepts '+str(summary['direct_comparator']['usable_accepts'])+'/'+str(len(primary))+' usable and '+str(summary['direct_comparator']['incomplete_accepts'])+'/'+str(len(incomplete))+' incomplete-transition held probes. These are retrospective decisions, not deployed service times.\n\nHashes validate exported bytes. They do not authenticate the provider or HMACs. Recorded binding premises, local timestamps and context projections remain trust limitations. No QPU/provider/network operations are used.\n',encoding='utf-8')
 print(json.dumps({'status':report['status'],'checks':len(checks),'discrepancies':len(failed),'summary':summary},indent=2));raise SystemExit(0 if not failed else 1)

def software_tests(corrected,units,computed):
 spec=CalibrationSpecification('synthetic','score','not an empirical sample','synthetic','synthetic','score','none',.05)
 model=EmpiricalQuantileCalibration(spec).fit([.30]*39);p=model.p_value(.20)
 tests=[{'name':'synthetic_relative_conformity_does_not_imply_absolute_correctness','rank':p,'rank_accept':model.accepts(.20),'absolute_relative_threshold_pass':.20<=.15+1e-12,'pass':p==1 and model.accepts(.20) and not .20<=.15+1e-12,'evidence':'software-only constructed scores; no physical observation'}]
 u=next(v for v in units.values() if v.get('counts'));bad=copy.deepcopy(u);bad['counts']=None
 tests.append({'name':'direct_comparator_unknown_counts','pass':comparator(bad,None)[0]=='UNKNOWN'})
 bad=copy.deepcopy(u);bad['binding']['historical_workload_digest']='mismatch'
 tests.append({'name':'direct_comparator_wrong_context','pass':comparator(bad,True)[0]=='REJECT'})
 tests.append({'name':'direct_comparator_absolute_failure','pass':comparator(u,False)[0]=='REJECT'})
 for label,section,key in [('unknown_timestamp','timings','provider_running_at'),('unknown_context','binding','historical_workload_digest')]:
  bad=copy.deepcopy(u);bad[section].pop(key,None)
  tests.append({'name':'direct_comparator_'+label,'pass':comparator(bad,True)[0]=='UNKNOWN'})
 bad=copy.deepcopy(u);bad['binding']['checks'].pop('J4_integrity',None)
 tests.append({'name':'direct_comparator_unknown_integrity','pass':comparator(bad,True)[0]=='UNKNOWN'})
 bad=copy.deepcopy(u);bad.update(physical_execution_evidence=False,counts=None)
 tests.append({'name':'direct_comparator_known_nonexecution_over_missing','pass':comparator(bad,None)[0]=='REJECT' and 'counts' in comparator(bad,None)[1]})
 # Synthetic all-success primary set isolates declaration logic from the observed non-rejection.
 for errorphase in ['post_recovery_verification','accepted_non_usable_primary']:
  with tempfile.TemporaryDirectory(prefix='paper25_kcb4_') as td:
   root=Path(td);accepted=[]
   for i in range(10):
    c=f'CS{i:02d}';accepted.append({'candidate_id':c,'label':c,'usable_transition_window':True,'bound_sealed_units':6,'status':'accepted_usable'})
    d=root/'windows'/c;write(d/'window.json',{});(d/'units.jsonl').write_text('')
    rs=[{'candidate_id':c,'probe_id':f'{c}-{j}','policy_id':P5,'phase':'pre_recovery_service','primary_contrast_eligible':True,'recovered_valid_service':True,'served':True,'served_source':HELD,'oracle_service_correct':True,'assurance_valid_for_serving':True,'context_bound':True,'held_physical_result_exists':True,'trusted_invariants_held':True,'service_probe_qpu_rerun':False,'total_recovery_latency_seconds':1.} for j in range(6)]
    (d/'policy_records.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rs))
   error=copy.deepcopy(rs[0]);error.update(probe_id='synthetic-incorrect',oracle_service_correct=False)
   if errorphase=='post_recovery_verification':error.update(phase='post_recovery_verification',primary_contrast_eligible=False);p=root/'windows/CS09/policy_records.jsonl'
   else:
    c='CNONUSABLE';accepted.append({'candidate_id':c,'label':c,'usable_transition_window':False,'bound_sealed_units':1,'status':'accepted_non_usable'});d=root/'windows'/c;write(d/'window.json',{});(d/'units.jsonl').write_text('');error['candidate_id']=c;p=d/'policy_records.jsonl'
   with p.open('a') as f:f.write(json.dumps(error)+'\n')
   write(root/'campaign_state.json',{'accepted_windows':accepted,'incomplete_windows':[],'phase':'synthetic','scientific_terminal_units':61,'preflight_binding_self_test_passed':True})
   old=analyze(root,repo_root=ROOT,verify_campaign_a=False);new=corrected.analyze(root,repo_root=ROOT,verify_campaign_a=False)
   tests.append({'name':'KC-B4_'+errorphase,'historical_declares':old['h1_b_declared'],'corrected_declares':new['h1_b_declared'],'KC_B4':new['kill_criteria']['KC-B4']['state'],'pass':old['h1_b_declared'] is True and new['h1_b_declared'] is False and new['kill_criteria']['KC-B4']['state']=='triggered','evidence':'synthetic software regression; not a campaign result'})
 return tests
if __name__=='__main__':main()
