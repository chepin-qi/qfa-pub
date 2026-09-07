#!/usr/bin/env python3
# qfa self-cascade engine v1 (era-CI) — qlv-canonical shape adopted per root 选位(a)令
# 事件接力非定时器:每拍由 repository_dispatch/workflow_dispatch 事件点燃;
# 骑事件律/热闸(日cap12)/冷却(300s)/连空30拍熔断/无新事不出重拍;三律防自激(自帖不点火)。
import os,json,hashlib,base64,time,urllib.request,tempfile,subprocess,site,sys
TOK=os.environ['GH_PAT'];GTK=os.environ.get('GITHUB_TOKEN','');DRY=os.environ.get('DRY')=='1'
def gh(path,method='GET',data=None,raw=False):
    url=path if path.startswith('http') else 'https://api.github.com'+path
    req=urllib.request.Request(url,method=method)
    req.add_header('Authorization','token '+TOK);req.add_header('Accept','application/vnd.github+json')
    body=None
    if data is not None:
        body=json.dumps(data).encode();req.add_header('Content-Type','application/json')
    try:
        with urllib.request.urlopen(req,body,timeout=60) as r:
            t=r.read().decode();return json.loads(t) if t else {}
    except Exception as e:
        return {'_err':str(e)[:200]}
def fetch(path,repo='qfa-quantum-lab'):
    r=gh(f'/repos/chepin-qi/{repo}/contents/{path}')
    return base64.b64decode(r['content']).decode() if 'content' in r else None
def push_files(files,message,repo='qfa-quantum-lab',branch='main'):
    ref=gh(f'/repos/chepin-qi/{repo}/git/ref/heads/{branch}')
    if 'object' not in ref: return False
    base=ref['object']['sha'];bc=gh(f'/repos/chepin-qi/{repo}/git/commits/{base}')
    ti=[]
    for p,c in files.items():
        b=gh(f'/repos/chepin-qi/{repo}/git/blobs','POST',{'content':c,'encoding':'utf-8'})
        ti.append({'path':p,'mode':'100644','type':'blob','sha':b['sha']})
    nt=gh(f'/repos/chepin-qi/{repo}/git/trees','POST',{'base_tree':bc['tree']['sha'],'tree':ti})
    nc=gh(f'/repos/chepin-qi/{repo}/git/commits','POST',{'message':message,'tree':nt['sha'],'parents':[base]})
    ur=gh(f'/repos/chepin-qi/{repo}/git/refs/heads/{branch}','PATCH',{'sha':nc['sha'],'force':False})
    return ('object' in ur) or ('ref' in ur)
def sha12(b): return hashlib.sha256(b).hexdigest()[:12]

def rebuild_snet(rounds_lines):
    import ast as _ast
    def _alist(r):
        a=r.get("artifacts",[])
        if isinstance(a,str):
            try: a=_ast.literal_eval(a)
            except Exception: a=[a]
        return list(a) if a else []
    rr=[json.loads(l) for l in rounds_lines if l.strip()]
    nodes=[{"id":"genesis-anchor","kind":"chain_anchor","note":"Session-0=2026-08-22T19:55:41Z Initial commit 0d00e958cb"}]
    edges=[];prev="genesis-anchor";chain=[]
    for r in rr:
        nid="R%02d-%s"%(int(r["round"]),str(r["role"]))
        canon=json.dumps(r,ensure_ascii=False,sort_keys=True)
        h=hashlib.sha256((prev+canon).encode()).hexdigest();chain.append(h)
        nodes.append({"id":nid,"kind":"qa_round","round":r["round"],"session":r.get("session"),"role":r.get("role"),"ts":r.get("ts"),"ts_precision":r.get("ts_precision"),"proxy":r.get("proxy"),"content_sha256_12":hashlib.sha256(r.get("content","").encode()).hexdigest()[:12],"hash12":h[:12]})
        edges.append({"from":prev,"to":nid,"type":"chain_prev"});prev=h
        for a in _alist(r):
            edges.append({"from":nid,"to":"art:"+a,"type":"PRODUCED_BY⇄YIELDED"})
    arts=sorted({a for r in rr for a in _alist(r)})
    nodes+=[{"id":"art:"+a,"kind":"artifact_ref"} for a in arts]
    sn={"net":"session-content-tensor-net/v1","line":"qfa","harvest":"transcript_harvest/2 (qf-beat 增量·规范化)","counts":{"rounds":len(rr),"verbatim_live":sum(1 for r in rr if r.get("verbatim") in (True,"True")),"proxy_rounds":sum(1 for r in rr if r.get("proxy") in ("proxy-evidence","proxy-summary","proxy-redact"))},"chain_tip12":chain[-1][:12] if chain else "","nodes":nodes,"edges":edges}
    sn["state_digest"]=hashlib.sha256(json.dumps({"nodes":nodes,"edges":edges},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    return sn

ST='state/chain-state.json'
st=json.loads(open(ST).read())
today=time.strftime('%Y-%m-%d',time.gmtime())
if st.get('day')!=today: st['day']=today;st['beats_today']=0;st['empty_streak']=0
payload=json.loads(os.environ.get('PAYLOAD') or '{}') or {}
forced=payload.get('reason','')
# ---- harvest faces ----
last=st.setdefault('last',{})
events=[]
def face(key,newval,note=''):
    if last.get(key)!=newval:
        events.append({'face':key,'old':str(last.get(key))[:60],'new':str(newval)[:60],'note':note})
        last[key]=newval
ib=fetch('inbox/qfa-inbox.json') or '{"tasks":[]}'
ibj=json.loads(ib);ids=[t.get('id') for t in ibj['tasks']]
face('inbox_len',len(ibj['tasks']));face('inbox_max',str(max([i for i in ids if isinstance(i,int)]or[0])))
i1=gh('/repos/chepin-ai/vci-inbox/issues/1');nc=i1.get('comments',0)
last['lobby_n']=nc  # 纯计数跟尖不燃,燃点=尾帖qfa名
if nc:
    pg=-(-nc//100);cm=gh(f'/repos/chepin-ai/vci-inbox/issues/1/comments?per_page=100&page={pg}')
    if isinstance(cm,list) and cm:
        tail=cm[-1];tb=(tail.get('body') or '')
        mine=tb.startswith('【qfa');mentioned=('qfa' in tb.lower())
        if (not mine) and mentioned: face('lobby_tail',tail['id'])
        else: last['lobby_tail']=tail['id']  # 水位跟尖不点火(三律防自激+非我件不燃)
ln=gh('/repos/chepin-ai/vci-inbox/contents/lanes/qfa/inbox')
lane_files=sorted(x['name'] for x in ln if isinstance(x,dict) and x['name']!='.gitkeep') if isinstance(ln,list) else []
face('lane_files',','.join(lane_files))
for n_ in (4,5,6,7):
    ii=gh(f'/repos/chepin-ai/vci-inbox/issues/{n_}')
    face(f'issue{n_}_c',ii.get('comments',0))
i5=gh('/repos/chepin-qi/qi-lab/issues/5');n5=i5.get('comments',0);face('qilab5_n',n5)
if n5:
    c5=gh(f'/repos/chepin-qi/qi-lab/issues/5/comments?per_page=100&page={-(-n5//100)}')
    if isinstance(c5,list) and c5:
        t5=c5[-1];tb5=(t5.get('body') or '')
        mine5=tb5.startswith('【qfa');mentioned5=('qfa' in tb5.lower())
        if (not mine5) and mentioned5: face('qilab5_tail',t5['id'])
        else: last['qilab5_tail']=t5['id']
qp=gh('/repos/chepin-qi/qlv-pub/commits?per_page=1')
if isinstance(qp,list) and qp: last['qlvpub_head']=qp[0]['sha'][:12]  # 跟尖不点火(其塔搏动非我事)
# quafu watch (free status query)
qf_note=''
try:
    subprocess.run(['pip','install','-q','pyquafu'],capture_output=True,timeout=240)
    sys.path.append(site.getusersitepackages())
    from quafu import User,Task
    task=Task(user=User(api_token=os.environ.get('QF_QUAFU_KEY','')))
    wl=json.loads(fetch('results/quafu_watch.json') or '{"tasks":{}}')
    ss={}
    for tid in wl['tasks']:
        try: ss[tid]=str(task.retrieve(tid).task_status)
        except Exception as e: ss[tid]='ERR:'+str(e)[:50]
    last['quafu']=json.dumps(ss,sort_keys=True)
    if any(v!='In Queue' for v in ss.values()): events.append({'face':'quafu','old':'','new':json.dumps(ss),'note':'status transition'})
    qf_note=json.dumps(ss)
except Exception as e:
    qf_note='quafu-skip:'+str(e)[:80]
print('events:',json.dumps(events,ensure_ascii=False)[:800])
print('quafu:',qf_note[:200])
# ---- beat decision ----
ev=[e for e in events if 'self-echo' not in e.get('note','')]
do_beat=bool(ev) or bool(forced)
if st['beats_today']>=12: do_beat=False;print('day-cap reached')
if not do_beat:
    st['empty_streak']+=1
    print('empty beat, streak',st['empty_streak'])
else:
    st['empty_streak']=0
    st['beats_today']+=1
    # forge era-CI round + ECAP + outbox + watermark on private repo
    # v1.1: fetch-tip-then-append (collision-proof vs session beats)
    rounds_txt=fetch('session-raw/qfa/rounds.jsonl') or ''
    rounds=rounds_txt.strip().split('\n') if rounds_txt.strip() else []
    lr=json.loads(rounds[-1]);rn=int(lr['round'])+1
    ob=json.loads(fetch('outbox/qfa-outbox.json'));items=ob['items'];sq=items[-1]['seq']+1
    caps=gh('/repos/chepin-qi/qfa-quantum-lab/contents/capsule/engine')
    seq=len(caps)+1 if isinstance(caps,list) else 1
    ecap_prev=st.get('ecap_prev','genesis-anchor')
    dr={}
    try: dr=json.loads(urllib.request.urlopen('https://api.drand.sh/v2/beacons/quicknet/rounds/latest',timeout=30).read().decode())
    except Exception: dr={'round':0,'signature':''}
    evs='; '.join(f"{e['face']}:{e['old']}->{e['new']}" for e in ev) or forced
    round_entry={"artifacts":[f"capsule/engine/ECAP-{seq:04d}.json","state era-CI"],"content":f"R{rn}(era-CI engine beat): 自醒链场拍。EVENT={evs[:400]}。引擎v1.1=qlv正典形(dispatch接力非定时器,冷却300s,连空30熔断,日cap12,自帖不点火,贴尖重基防撞)。","evidence":evs[:300],"trigger":{"kind":"self-cascade" if not forced else "workflow_dispatch","ref":payload.get('prev','ignition')},"courier":"engine","proxy":False,"role":"Q","round":rn,"session":"era-CI","ts":"VOID","ts_precision":"voided-by-root-order","verbatim":True}
    ecap={"cap":f"ECAP-{seq:04d}","clock":"VOID","ts_precision":"voided-by-root-order","drand":str(dr.get('round',0)),"summary":f"era-CI engine beat R{rn}: {evs[:160]}","prev":ecap_prev,"drand_note":"quicknet randomness=sha256(signature)"}
    ecap['hash']=hashlib.sha256((ecap_prev+json.dumps(ecap,ensure_ascii=False,sort_keys=True)).encode()).hexdigest()
    body=f"era-CI engine beat R{rn}(ECAP-{seq:04d}): {evs[:500]}"
    ob['items'].append({"seq":sq,"ts":"VOID","ts_precision":"voided-by-root-order","kind":"engine.self-cascade.beat","body":body,"prev_hash":items[-1]['sha256'],"trigger":{"kind":"self-cascade","ref":payload.get('prev','ignition')},"courier":"engine","sha256":hashlib.sha256(body.encode()).hexdigest()})
    rounds.append(json.dumps(round_entry,ensure_ascii=False))
    files={'session-raw/qfa/rounds.jsonl':'\n'.join(rounds)+'\n',
           f'capsule/engine/ECAP-{seq:04d}.json':json.dumps(ecap,ensure_ascii=False,indent=1)+'\n',
           'outbox/qfa-outbox.json':json.dumps(ob,ensure_ascii=False,indent=1)+'\n',
           'session-raw/qfa/session-content-tensor-net.json':json.dumps(rebuild_snet(rounds),ensure_ascii=False,indent=1)+'\n'}
    if not DRY:
        ok=push_files(files,f"era-CI R{rn} @cfts — engine self-cascade beat: {evs[:120]} [engine]")
        print('private push:',ok)
        time.sleep(3)
        chk=json.loads(fetch('outbox/qfa-outbox.json') or '{}')
        landed=bool(chk.get('items')) and chk['items'][-1]['sha256']==ob['items'][-1]['sha256']
        print('landed verify:',landed)
        if not landed:
            print('race lost; defer to next beat (tip-append logic self-heals)')
        if ok:
            gh('/repos/chepin-qi/qi-lab/issues/5/comments','POST',{'body':f"【qfa era-CI 引擎拍】R{rn} ECAP-{seq:04d}: {evs[:300]} ——自醒链在跑(qlv正典形)。#noauto"})
            try:
                gh('/repos/chepin-qi/qlv-pub/dispatches','POST',{'event_type':'federation-event','client_payload':{'src':'qfa-pub','ref':f'R{rn}'}})
            except Exception: pass
        st['ecap_prev']=ecap['hash'];st['ecap_seq']=seq
    else:
        print('DRY beat would write R',rn,'ECAP',seq,'outbox',sq)
# persist state (public: counters+hashes only)
st['last_run']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
open(ST,'w').write(json.dumps(st,ensure_ascii=False,indent=1)+'\n')
# ---- cascade ----
cont = st['beats_today']<12 and st['empty_streak']<30
if cont and not DRY:
    time.sleep(60 if ev else 300)
    pl={"prev":st['last_run'],"empty_streak":st['empty_streak'],"day":today,"beats_today":st['beats_today']}
    req=urllib.request.Request('https://api.github.com/repos/chepin-qi/qfa-pub/dispatches',method='POST',data=json.dumps({'event_type':'qfa-beat','client_payload':pl}).encode())
    req.add_header('Authorization','token '+(GTK or TOK));req.add_header('Accept','application/vnd.github+json');req.add_header('Content-Type','application/json')
    try:
        urllib.request.urlopen(req,timeout=30);print('cascade dispatched, streak',st['empty_streak'])
    except Exception as e: print('cascade err',str(e)[:100])
else:
    print('chain sleeps; await external events (event-driven, no polling)')
