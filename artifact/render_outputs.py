"""Vector grayscale figures and TeX tables from reconstructed v5 quantities."""
import csv,json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
def render(root,out,summary,probes,outcomes,flow,refdistributions):
 for d in ['figures','tables']:(out/d).mkdir(exist_ok=True)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 def save(fig,name):
  fig.savefig(out/'figures'/f'{name}.pdf',bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None});fig.savefig(out/'figures'/f'{name}.png',bbox_inches='tight',dpi=160);plt.close(fig)
 def table(name,head,rows,fmt):
  (out/'tables'/name).write_text('\\begin{tabular}{'+fmt+'}\\toprule\n'+' & '.join(head)+r'\\\midrule'+'\n'+'\n'.join(' & '.join(map(str,r))+r'\\' for r in rows)+'\n\\bottomrule\n\\end{tabular}\n')
 wr=[];fig,ax=plt.subplots(figsize=(7.1,3.6))
 for i,w in enumerate(outcomes):
  ps=[p for p in probes if p['candidate']==w['candidate_id']];ls=[p['T0_T3_s'] for p in ps]
  wr.append([w['label']+'/'+w['candidate_id'],f'{min(ls):,.1f}',f'{max(ls):,.1f}',str(w['retained_result_count'])+'/'+str(w['fallback_count']),'Yes' if w['window_recovery_success'] else 'No: deadline'])
  for j,p in enumerate(ps):
   held=p['p5_source']=='held_physical_result';ax.scatter(p['T0_T3_s']/60,i+(j-2.5)*.075,marker='o' if held else 's',s=25,facecolor='black' if held else 'white',edgecolor='black',zorder=3)
 ax.set_xscale('log');ax.set_xlim(8,550);ax.axvline(30,color='.35',ls='--');ax.text(32,-.35,'30 min deadline',fontsize=8)
 ax.set_yticks(range(len(outcomes)),[w['label']+'/'+w['candidate_id'] for w in outcomes]);ax.invert_yaxis();ax.set_xticks([10,30,60,120,240,480],['10','30','60','120','240','480']);ax.set_xlabel('HOLD-to-service time (minutes; logarithmic scale)');ax.grid(axis='x',alpha=.2)
 ax.scatter([],[],s=25,c='black',label='Retained physical');ax.scatter([],[],s=25,facecolor='white',edgecolor='black',marker='s',label='Classical fallback');ax.legend(loc='lower right',fontsize=8,frameon=False);fig.tight_layout();save(fig,'window_latency')
 table('windows.tex',['Window','Min (s)','Max (s)','R/F','Success'],wr,'lrrcl')
 table('flow_v5.tex',['Candidate','Role','Held','Bound cal.','Usable','Success'],[[f['candidate'],'Bootstrap' if f['role']=='bootstrap attempt' else 'Transition',f['held_probes'],str(f['bound_calibration'])+'/39','Yes' if f['usable'] else 'No','Yes' if f['window_success'] else ('No' if f['usable'] else '--')] for f in flow],'llrrcc')
 j=summary['joint'];table('comparison_v5.tex',['P2 replay','P5 retained','P5 fallback','Row total'],[['Serve',j['P2_serve/P5_retained'],j['P2_serve/P5_fallback'],j['P2_serve/P5_retained']+j['P2_serve/P5_fallback']],['Reject',j['P2_reject/P5_retained'],j['P2_reject/P5_fallback'],j['P2_reject/P5_retained']+j['P2_reject/P5_fallback']]],'lrrr')
 table('power_v5.tex',['Hypothetical $\\pi$','Power $P(X\\geq9)$'],[[f"{r['hypothetical_pi']:.2f}",f"{r['power']:.6f}"] for r in summary['design_power']],'rr')
 with (root/'data/candidates_accounting.csv').open() as f:candidates=list(csv.DictReader(f))
 table('candidate_flow.tex',['Candidate','Role','Jobs$^a$','Bound','Unbound','Reference','Ledger'],[[c['candidate_id'],'Bootstrap' if c['bootstrap'].lower()=='true' else ('Usable' if c['usable_transition_window'].lower()=='true' else 'Incomplete'),c['physical_submissions'],c['units_bound'],c['units_unbound'],c['calibration_units_bound']+'/39',c['ledger_entries']] for c in candidates],'llrrrrr')
 sec=json.loads((root/'data/analysis.json').read_text())['secondary'];rates=[]
 def rate(label,r):rates.append([label,str(r['numerator'])+'/'+str(r['denominator']),f"[{r['lower']:.4f}, {r['upper']:.4f}]"])
 rate('P2 primary assurance-invalid',sec['p2_assurance_invalid_continuation']);rate('P5 assurance-invalid, both phases',sec['p5_assurance_invalid_continuation']);rate('Retained outputs, primary',sec['retained_result_rate']);rate('Fallback outputs, primary',sec['fallbacks']['fraction_of_served_primary_probes'])
 for key,label in [('incorrect_service_continuation','Incorrect among served'),('service_availability','Mixed-clock availability'),('verification_probe_behavior','Verification correct services')]:
  for policy,r in sec[key].items():rate(policy.split('-')[0]+': '+label,r)
 from dataclasses import asdict
 from athena_aegis.analysis.metrics import wilson_rate
 missing=summary['count_reproduction']['missing_by_terminal_state'];unbound=missing.get('UNBOUND_AUDIT_ONLY',0)
 rate('Binding failure, DONE units',asdict(wilson_rate(unbound,summary['count_reproduction']['with_counts']+unbound,'unit')))
 rate('Retained-only window success',asdict(wilson_rate(summary['confirmatory']['retained_only_windows'],summary['confirmatory']['usable_windows'],'window')))
 table('secondary_rates.tex',['Endpoint / scope','Count','Nominal Wilson 95\\%'],rates,'lrr')
 fig,axes=plt.subplots(1,2,figsize=(7.1,3.15))
 for p in probes:
  changed=p['p2_would_serve']!=(p['p5_source']=='held_physical_result');axes[0].scatter(p['p2_rank'],p['p5_rank'],marker='x' if changed else 'o',s=35 if changed else 19,color='black',alpha=1 if changed else .5)
 axes[0].plot([0,1],[0,1],ls=':',c='.4');axes[0].axhline(.05,ls='--',c='.5');axes[0].axvline(.05,ls='--',c='.5');axes[0].set(xlabel='P2 rank (old reference)',ylabel='P5 rank (renewed reference)',title='Paired rank values');axes[0].annotate('W02 probe 06',(.075,.05),(.25,.19),arrowprops={'arrowstyle':'->'},fontsize=8)
 ordered=sorted(probes,key=lambda x:x['relative_error'])
 for i,p in enumerate(ordered):axes[1].scatter(i+1,p['relative_error'],marker='s' if p['p5_source']=='classical_fallback' else 'o',facecolor='white' if p['p5_source']=='classical_fallback' else 'black',edgecolor='black',s=19)
 axes[1].axhline(.15,c='.35',ls='--');axes[1].set(xlabel='Physical probe (sorted by error)',ylabel='Relative Frobenius error',title='Correct physical results');axes[1].text(2,.155,'Frozen threshold 0.15',fontsize=8);axes[1].set_ylim(0,.17);fig.tight_layout();save(fig,'comparison_v5')
 fig,ax=plt.subplots(figsize=(7.1,4.05));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
 def box(x,y,w,h,title,body):
  ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008',facecolor='white',edgecolor='black',lw=.8));ax.text(x+.012,y+h-.03,title,fontweight='bold',va='top',fontsize=9);ax.text(x+.012,y+h-.09,body,va='top',fontsize=8.2,linespacing=1.4)
 box(.02,.73,.57,.24,'1  Acquire and bind in NEW context','Counts, context comparisons and recorded integrity.\nExact oracle computed before sealing.\nEach held result starts its own local clock T0.')
 box(.02,.41,.57,.23,'2  Renew the shared reference','T1: first calibration submission.\nT2: all 39 context-bound calibration units ready.\nIncomplete or expired evidence remains ineligible.')
 box(.02,.10,.57,.22,'3  Re-evaluate retained results','Rank acceptance: retain the physical matrix.\nRank rejection: permitted classical fallback.\nT3: service or terminal decision; no probe rerun.')
 box(.66,.56,.31,.30,'Distinct predicates','Context binding\nRelative conformity\nAbsolute correctness\nPhysical or classical source\nHOLD-to-service deadline')
 box(.66,.10,.31,.32,'Endpoint, not a theorem','Six correct, valid services;\nat least five retained;\nat most one fallback;\neach within 1800 seconds.\nLate service can occur.')
 for x,y,xx,yy in [(.305,.716,.305,.654),(.305,.396,.305,.334),(.604,.21,.646,.21)]:ax.annotate('',xy=(xx,yy),xytext=(x,y),arrowprops={'arrowstyle':'-|>','lw':1,'color':'black','mutation_scale':10,'shrinkA':0,'shrinkB':0})
 fig.tight_layout(pad=.1);save(fig,'mechanism')
 # Contextual whole-window partition retained from the documented historical export.
 with (root/'data/retrospective/B_clock_partitions.csv').open() as f:clocks=list(csv.DictReader(f))
 fig,ax=plt.subplots(figsize=(7.1,2.8));left=[0.,0.]
 fields=[('open_to_first_hold_s','Before first HOLD','white','///'),('first_hold_to_cal_start_s','HOLD to calibration','.8','xxx'),('cal_start_to_reference_s','Calibration to reference','.3',None),('reference_to_last_service_s','Reference to last service','.6','...'),('last_service_to_close_s','Last service to close','.92','\\\\')]
 for key,label,color,hatch in fields:
  vals=[float(c[key])/3600 for c in clocks];ax.barh([0,1],vals,left=left,label=label,color=color,hatch=hatch,edgecolor='black',lw=.5,height=.45);left=[a+b for a,b in zip(left,vals)]
 ax.set_yticks([0,1],['W03 / C04','W04 / C06']);ax.invert_yaxis();ax.set_xlabel('Elapsed time from window opening (hours)');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.33),ncol=2,frameon=False,fontsize=8);fig.subplots_adjust(bottom=.36,left=.14,right=.98,top=.95);save(fig,'clock_partitions')
