#!/usr/bin/env python3
# qfa self-cascade engine v1.5 (era-CI) — 自举互激修(应 root「仍然没有做到自举互激」判词)
# v1.4 死穴:日cap12连事件拍一并斩(巷卡首达而哑/互唤kick被吸收=死节点);空拍sleep300s自dispatch=变相定时器。
# v1.5 六律:
#  律一 事件拍永不过闸:显著事件(inbox/lane/issues/qilab5@qfa/quafu转态/drand日界)必成拍,日cap废;
#        绝对保险丝 event_fuse=48/日(防爆,吹则记账)。
#  律二 一事一拍(幂等点火账 fired_events:face→newval,同值不重复燃;翻转A→B→A只燃首尾)。
#  律三 无件即眠:空拍不传火不自接力(变相定时器拆除);事件拍后仅允一拍60s确认续火(追突发尾),
#        确认拍若无新事即眠。链之生死=事件之有无,与计数器无关。
#  律四 拍尾互唤分面:仅我线事件(lane/inbox/quafu/issue)唤 qlv 塔;大堂/烽火回声不回火(其塔自见)。
#  律五 自帖不点火(三律防自激承v1.2):我撰大堂/烽火尾帖只跟尖不燃。
#  律六 workflow_run 复生器(resurrector.yml):engine 失败事件→一次性挽火(幂等键=run_id)。零cron。
# 公私域律:公仓仅码+计数+哈希指针;联邦散文悉落私仓。
import os,json,hashlib,base64,time,urllib.request,subprocess,site,sys
TOK=os.environ['GH_PAT'];GTK=os.environ.get('GITHUB_TOKEN','');DRY=os.environ.get('DRY')=='1'
FUSE=48
def gh(path,method='GET',data=None):
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
    nc=gh('/repos/chepin-qi/'+repo+'/git/commits','POST',{'message':message,'tree':nt['sha'],'parents':[base]})
    ur=gh(f'/repos/chepin-qi/{repo}/git/refs/heads/{branch}','PATCH',{'sha':nc['sha'],'force':False})
    return ('object' in ur) or ('ref' in ur)

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
        nid="R%02d-%s"%(int(r["round"]),str(r.get("role",r.get("era","S"))))
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
if st.get('day')!=today: st['day']=today;st['beats_today']=0;st['event_beats_today']=0
st.setdefault('event_beats_today',0);st.setdefault('fired_events',{});st.setdefault('resurrected',[])
payload=json.loads(os.environ.get('PAYLOAD') or '{}') or {}
forced=payload.get('reason','')
last=st.setdefault('last',{})
raw_events=[]
def face(key,newval,note=''):
    newval=str(newval)
    if last.get(key)!=newval:
        raw_events.append({'face':key,'old':str(last.get(key))[:60],'new':newval[:60],'note':note})
        last[key]=newval
ib=fetch('inbox/qfa-inbox.json') or '{"tasks":[]}'
ibj=json.loads(ib);ids=[t.get('id') for t in ibj['tasks']]
face('inbox_len',len(ibj['tasks']));face('inbox_max',str(max([i for i in ids if isinstance(i,int)]or[0])))
i1=gh('/repos/chepin-ai/vci-inbox/issues/1');nc=i1.get('comments',0)
last['lobby_n']=nc
if nc:
    pg=-(-nc//100);cm=gh(f'/repos/chepin-ai/vci-inbox/issues/1/comments?per_page=100&page={pg}')
    if isinstance(cm,list) and cm:
        tail=cm[-1];tb=(tail.get('body') or '')
        mine=tb.startswith('【qfa') or tb.startswith('[qfa');mentioned=('qfa' in tb.lower())
        if (not mine) and mentioned: face('lobby_tail',tail['id'])
        else: last['lobby_tail']=tail['id']
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
        mine5=tb5.startswith('【qfa') or tb5.startswith('[qfa');mentioned5=('qfa' in tb5.lower())
        if (not mine5) and mentioned5: face('qilab5_tail',t5['id'])
        else: last['qilab5_tail']=t5['id']
qp=gh('/repos/chepin-qi/qlv-pub/commits?per_page=1')
if isinstance(qp,list) and qp: last['qlvpub_head']=qp[0]['sha'][:12]
# drand 日界地标(外部公源信标,穿默证活;非定时器——仅在被点燃的运行内读)
dr={}
try: dr=json.loads(urllib.request.urlopen('https://api.drand.sh/v2/beacons/quicknet/rounds/latest',timeout=30).read().decode())
except Exception: dr={'round':0,'signature':''}
if dr.get('round'): face('drand_day',dr['round']//28800,note='external-beacon-day')
# quafu watch
qf_note='';qf_archives={}
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
    for tid,stt in ss.items():
        if stt not in ('In Queue',):
            try:
                rr2=task.retrieve(tid);cnt=getattr(rr2,'counts',None)
                if cnt is not None:
                    qf_archives[f'ci/results/quafu_watch_{tid}.json']=json.dumps({'taskid':tid,'status':str(stt),'counts':cnt,'archived_by':'qfa-pub engine v1.5','clock':'VOID'},ensure_ascii=False,indent=1)
                    raw_events.append({'face':'quafu_done','old':'In Queue','new':f'{tid}:{stt}','note':'counts archived'})
            except Exception as ee: print('quafu arch err',tid,str(ee)[:60])
    qf_note=json.dumps(ss)
except Exception as e:
    qf_note='quafu-skip:'+str(e)[:80]
# ---- 律二 幂等:一事一拍 ----
fe=st['fired_events']
ev=[]
for e in raw_events:
    k=e['face']
    if fe.get(k)!=e['new']:
        ev.append(e);fe[k]=e['new']
print('salient events (idempotent):',json.dumps(ev,ensure_ascii=False)[:800])
print('quafu:',qf_note[:200])
do_beat=bool(ev) or bool(forced)
if do_beat and st['event_beats_today']>=FUSE:
    do_beat=False;print('EVENT FUSE blown',st['event_beats_today'])  # 防爆保险丝,吹则记账
if not do_beat:
    st['empty_streak']=st.get('empty_streak',0)+1
    print('empty beat -> 无件即眠, streak',st['empty_streak'])
else:
    st['empty_streak']=0;st['beats_today']+=1;st['event_beats_today']+=1
    rounds_txt=fetch('session-raw/qfa/rounds.jsonl') or ''
    rounds=rounds_txt.strip().split('\n') if rounds_txt.strip() else []
    lr=json.loads(rounds[-1]);rn=int(lr['round'])+1
    ob=json.loads(fetch('outbox/qfa-outbox.json'));items=ob['items'];sq=items[-1]['seq']+1
    caps=gh('/repos/chepin-qi/qfa-quantum-lab/contents/capsule/engine')
    seq=len(caps)+1 if isinstance(caps,list) else 1
    ecap_prev=st.get('ecap_prev','genesis-anchor')
    evs='; '.join(f"{e['face']}:{e['old']}->{e['new']}" for e in ev) or forced
    round_entry={"artifacts":[f"capsule/engine/ECAP-{seq:04d}.json","state era-CI"],"content":f"R{rn}(era-CI engine beat): 自醒链场拍。EVENT={evs[:400]}。引擎v1.5=自举互激修(事件拍不过闸/一事一拍/无件即眠/拍尾分面互唤/复生器零cron)。","evidence":evs[:300],"trigger":{"kind":"self-cascade" if not forced else "workflow_dispatch","ref":payload.get('prev',forced or 'ignition')},"courier":"engine","proxy":False,"role":"Q","round":rn,"session":"era-CI","ts":"VOID","ts_precision":"voided-by-root-order","verbatim":True}
    ecap={"cap":f"ECAP-{seq:04d}","clock":"VOID","ts_precision":"voided-by-root-order","drand":str(dr.get('round',0)),"summary":f"era-CI engine beat R{rn}: {evs[:160]}","prev":ecap_prev,"drand_note":"quicknet randomness=sha256(signature)"}
    ecap['hash']=hashlib.sha256((ecap_prev+json.dumps(ecap,ensure_ascii=False,sort_keys=True)).encode()).hexdigest()
    body=f"era-CI engine beat R{rn}(ECAP-{seq:04d}): {evs[:500]}"
    ob['items'].append({"seq":sq,"ts":"VOID","ts_precision":"voided-by-root-order","kind":"engine.self-cascade.beat","body":body,"prev_hash":items[-1]['sha256'],"trigger":{"kind":"self-cascade","ref":payload.get('prev','ignition')},"courier":"engine","sha256":hashlib.sha256(body.encode()).hexdigest()})
    rounds.append(json.dumps(round_entry,ensure_ascii=False))
    files={'session-raw/qfa/rounds.jsonl':'\n'.join(rounds)+'\n',
           f'capsule/engine/ECAP-{seq:04d}.json':json.dumps(ecap,ensure_ascii=False,indent=1)+'\n',
           'outbox/qfa-outbox.json':json.dumps(ob,ensure_ascii=False,indent=1)+'\n',
           'session-raw/qfa/session-content-tensor-net.json':json.dumps(rebuild_snet(rounds),ensure_ascii=False,indent=1)+'\n'}
    files.update(qf_archives)
    if not DRY:
        ok=push_files(files,f"era-CI R{rn} @cfts — engine beat v1.5: {evs[:120]} [engine]")
        print('private push:',ok)
        time.sleep(3)
        chk=json.loads(fetch('outbox/qfa-outbox.json') or '{}')
        landed=bool(chk.get('items')) and chk['items'][-1]['sha256']==ob['items'][-1]['sha256']
        print('landed verify:',landed)
        if not landed: print('race lost; tip-append self-heals next beat')
        if ok:
            gh('/repos/chepin-qi/qi-lab/issues/5/comments','POST',{'body':f"【qfa era-CI 引擎拍】R{rn} ECAP-{seq:04d}: {evs[:300]} ——v1.5自举互激链在跑。#noauto"})
            # 律四 互唤分面:仅我线事件唤qlv
            myline_faces={'lane_files','inbox_len','inbox_max','issue4_c','issue5_c','issue6_c','issue7_c','quafu_done'}
            if any(e['face'] in myline_faces for e in ev):
                try:
                    gh('/repos/chepin-qi/qlv-pub/dispatches','POST',{'event_type':'federation-event','client_payload':{'src':'qfa-pub','ref':f'R{rn}'}})
                    print('qlv wake fired (my-line event)')
                except Exception: pass
            else:
                print('echo-only event; qlv not re-fired (其塔自见)')
        st['ecap_prev']=ecap['hash'];st['ecap_seq']=seq
    else:
        print('DRY beat would write R',rn,'ECAP',seq,'outbox',sq)
# 复生幂等账
rid=payload.get('resurrect_run')
if rid and rid not in st['resurrected']: st['resurrected'].append(rid);st['resurrected']=st['resurrected'][-20:]
st['last_run']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
open(ST,'w').write(json.dumps(st,ensure_ascii=False,indent=1)+'\n')
# ---- 律三 传火判:事件拍→一拍确认续火;空拍→即眠 ----
if do_beat and ev and not DRY:
    time.sleep(60)
    pl={"prev":st['last_run'],"confirm_of":rn if 'rn' in dir() else 0,"src":"qfa-pub"}
    req=urllib.request.Request('https://api.github.com/repos/chepin-qi/qfa-pub/dispatches',method='POST',data=json.dumps({'event_type':'qfa-beat','client_payload':pl}).encode())
    req.add_header('Authorization','token '+(GTK or TOK));req.add_header('Accept','application/vnd.github+json');req.add_header('Content-Type','application/json')
    try:
        urllib.request.urlopen(req,timeout=30);print('confirm-beat dispatched (one-shot,追突发尾)')
    except Exception as e: print('confirm dispatch err',str(e)[:100])
else:
    print('chain sleeps; 纯事件驱动——待他线互唤/巷卡/烽件点燃 (no polling, no timers)')
