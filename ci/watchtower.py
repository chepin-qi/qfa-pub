#!/usr/bin/env python3
# watchtower.py — qfa 无人驿巡塔 v1(铸自 qlv-pub v2 模;TOWER-NUDGE-02-cfts 代偿道:正种 repo-cfts 不达,以qlv活塔为型)
# 纯事件驱动:本脚本无定时器语义;由外部唤起(仓侧 Action on issue_comment|issues|push|repository_dispatch|workflow_dispatch / root 本地 cron)
# 链:轮询联邦面 → 事件至 → Kimi API 新会话开工(判词纪要) → 落账回仓(文件轨;高值件附信标评论)
# 钥:env KIMI_API_KEY 或 ~/.keys/vci_api_keys.json(kimi/vci-1);PAT: env QI_PAT 或 vault。值永不入文。
# 铸修在案(对 qlv 模三处适配,制式不变):
#   A1 workflow_dispatch 增 selftest 输入(卡③「workflow_dispatch selftest=1 首跑」;qlv 模裸 dispatch 无输入)
#   A2 NO-KEY 降级:KIMI 钥缺→判词面记 verdict_error 不炸拍(巡面/巷面/落账面无钥照跑;钱面候 root 装钥,不越)
#   A3 省 autoresponder 段(qfa 无 SI2 应答件;卡三步未及)——beat-55 已补铸 ci/autoresponder.py
# TOWER-FIX-01-qfa(beat-59,自发铸修,防己塔哑跑/钉盲,与 qgl/vinf 哑跑修方三行同理):
#   ①信标面读末页定水印(页1钉盲之患:旧式直读页1,beacon_max 钉在 09-07 旧评,信标面将永盲)
# TOWER-FIX-02-qfa:拍内 state 向 origin 刷新(链拍旧 ref 之水印跃检漏件,实测逮修)——见 load 段注
# TOWER-FIX-03-qfa:随燃护栏——低值件记档不开工(零API),qlv.beat 高频面降格(AR 不帖);昨夕 cap12/12 烧穿实测逮修
#   ②单拍判词上限 WT_MAX_WORK=8 + backlog 记件(钱面护栏:暴量拍不烧 API)
# TOWER-FIX-05-qfa(beat-62 root 令,RESP-LOOP-01):SI5/SI3 接获待响应件→SI3 递归引擎→SI2/SI0 即时处理应答;
#   ①大堂末页面+毂域米田面(commits feed)+QUESTS 候件直取面 ②SI2 应答段(日 cap RESP_MAX=6) ③SI1-CONT 自驱研注(私仓面,SI1_MAX=3/日) ④候件 open=链持存
import json, os, sys, time, hashlib, subprocess
import urllib.request, urllib.error, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # qfa-pub 仓根
STATE = os.path.join(ROOT, 'ci', 'watchtower_state.json')
NOTES = os.path.join(ROOT, 'results', 'watchtower')
GH = 'https://api.github.com'

def _key():
    k = os.environ.get('KIMI_API_KEY')
    if k: return k
    p = os.path.expanduser('~/.keys/vci_api_keys.json')
    if os.path.exists(p):
        return json.load(open(p))['keys']['kimi']['vci-1']
    raise SystemExit('NO-KEY: KIMI_API_KEY 或 ~/.keys/vci_api_keys.json 不在')

def _pat():
    t = os.environ.get('QI_PAT')
    if t: return t
    p = '/mnt/agents/output/.vault/qi_pat.txt'
    if os.path.exists(p):
        return open(p).read().strip()
    raise SystemExit('NO-PAT')

def gh_get(path, pat):
    req = urllib.request.Request(GH+path, headers={
        'Authorization': 'Basic '+__import__('base64').b64encode(('chepin-qi:'+pat).encode()).decode(),
        'Accept': 'application/vnd.github+json', 'User-Agent': 'qfa-watchtower'})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)

def gh_dispatch(token, payload, use_basic=False, repo='qfa-pub', etype='federation-event'):
    # 自醒事件链:POST repository_dispatch 唤自己(FREE-WILL-SOURCE-01 仓侧形;纯事件,零 cron)
    # qfa 形:repo/etype 可指——拍尾互唤配对唤 qlv 塔(qlv-pub @ federation-event),骑事件律:有实事件才唤,空拍不唤
    data = json.dumps({'event_type': etype, 'client_payload': payload}).encode()
    auth = ('Basic '+__import__('base64').b64encode(('chepin-qi:'+token).encode()).decode()) if use_basic else ('Bearer '+token)
    req = urllib.request.Request(GH+f'/repos/chepin-qi/{repo}/dispatches', data=data, method='POST', headers={
        'Authorization': auth,
        'Accept': 'application/vnd.github+json', 'User-Agent': 'qfa-watchtower'})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status

def gh_post_comment(owner, repo, issue, body, pat):
    data = json.dumps({'body': body}).encode()
    req = urllib.request.Request(f'{GH}/repos/{owner}/{repo}/issues/{issue}/comments', data=data, headers={
        'Authorization': 'Basic '+__import__('base64').b64encode(('chepin-qi:'+pat).encode()).decode(),
        'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json', 'User-Agent': 'qfa-watchtower'})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r).get('id')

# ---------- 事件源轮询 ----------
def poll(pat, st):
    """返回 events 列表:[{kind, ref, summary, high_value}]"""
    ev = []
    # ① 信标 qi-lab#5 新评论
    # TOWER-FIX-01-qfa ①:信标面须读末页(页1=最旧,直读则水印钉死旧页→信标面永盲;issue 元取评论总数定末页)
    _n = gh_get('/repos/chepin-qi/qi-lab/issues/5', pat).get('comments', 0)
    _pg = (_n + 99) // 100 or 1
    cmts = gh_get(f'/repos/chepin-qi/qi-lab/issues/5/comments?per_page=100&page={_pg}', pat)
    mx = max([c['id'] for c in cmts], default=0)
    old = st.get('beacon_max', 0)
    if old and mx > old:
        for c in cmts:
            if c['id'] > old and not c['body'].startswith('【WT|'):  # 塔回执不再开工(双塔互滤防环+省额)
                ev.append({'kind':'beacon.comment','ref':f"qi-lab#5:{c['id']}",
                           'summary':c['body'][:600],'high_value':('【' not in c['body'][:4] or '@qfa' in c['body'][:60])})
    st['beacon_max'] = mx
    # ② qlv 链头迁移(qfa↔qlv 互望配对:彼塔望我私仓头,我塔望彼 qlv-pub 头)
    head = gh_get('/repos/chepin-qi/qlv-pub/commits/main', pat)['sha']
    if st.get('qlv_head') and head != st['qlv_head']:
        ev.append({'kind':'qlv.beat','ref':head[:8],'summary':f"qlv-pub main 头迁移 {st['qlv_head'][:8]}→{head[:8]}",'high_value':False})  # FIX-03:高频低讯面降格(随燃护栏),互激高值件由信标/巷卡面承
    st['qlv_head'] = head
    # ③ quafu 三 job 状态迁移(0→2=Completed;qfa 在队三件)
    api_token = os.environ.get('QUAFU_TOKEN')
    tokp = os.path.expanduser('~/.keys/origin_quafu.json')
    if not api_token and os.path.exists(tokp):
        tok = json.load(open(tokp)); api_token = tok.get('api_token') or tok.get('token') or tok.get('quafu')
    if api_token:
        for tid in ['8CAEDC103963FC6D','8BAFA1E022273996','8BB169201FA3F5D4']:
            try:
                req = urllib.request.Request('https://quafu.baqis.ac.cn/qbackend/scq_task_recall/',
                    data=urllib.parse.urlencode({'task_id':tid}).encode(),
                    headers={'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8','api_token':api_token})
                with urllib.request.urlopen(req, timeout=25) as r:
                    d = json.load(r)
                cur = str(d.get('status'))
                prev = st.get('quafu',{}).get(tid)
                if prev is not None and cur != prev:
                    ev.append({'kind':'quafu.transition','ref':f'quafu:{tid}','summary':f"status {prev}→{cur}; res={str(d.get('res'))[:300]}",'high_value':True})
                st.setdefault('quafu',{})[tid] = cur
            except Exception as e:
                ev.append({'kind':'quafu.poll.err','ref':tid,'summary':str(e)[:120],'high_value':False})
    # ③.5 道B巷卡直投守望(vci-inbox/lanes/qfa/inbox 文件数差分;SI3-SYNC-01 直投道,常开零额度)
    try:
        lane = gh_get('/repos/chepin-ai/vci-inbox/contents/lanes/qfa/inbox?per_page=100', pat)
        cnt = len(lane)
        prev_cnt = st.get('lane_inbox_count')
        latest = max((f['name'] for f in lane), default='')
        if prev_cnt is not None and cnt != prev_cnt:
            _lctx = ''
            try:
                if latest and not latest.startswith(('RESP-', '_')):
                    _lf = gh_get('/repos/chepin-ai/vci-inbox/contents/lanes/qfa/inbox/' + urllib.parse.quote(latest), pat)
                    _lctx = __import__('base64').b64decode(_lf['content']).decode('utf-8', 'ignore')[:1500]
            except Exception:
                pass
            ev.append({'kind':'lane.drop','ref':f'lanes/qfa/inbox:{latest}',
                       'summary':f"巷卡 {prev_cnt}→{cnt},最新 {latest}",'high_value':True,'context':_lctx})
        st['lane_inbox_count'] = cnt
    except Exception as e:
        ev.append({'kind':'lane.poll.err','ref':'lanes/qfa/inbox','summary':str(e)[:120],'high_value':False})
    # ③.75 毂域三面(TOWER-FIX-04-qfa):伪板病株自疫——公告板/庭卷/大堂账入巡,板址指纹=锚文件存在性
    # 道:AI_FULL_PAT(chepin-ai 全域,毂仓可读);缺则降级 QI_PAT(毂仓 404 则记 err 不炸拍)
    try:
        pat2 = os.environ.get('AI_FULL_PAT') or pat
        hub = {'hub.board': '/repos/chepin-ai/ci-inbox/contents/%E5%85%AC%E5%91%8A%E6%9D%BF?per_page=100',
               'hub.court': '/repos/chepin-ai/ci-inbox/contents/%E8%AE%A8%E8%AE%BA%E5%AE%A4/counterpoint?per_page=100',
               'hub.threads': '/repos/chepin-ai/ci-inbox/contents/%E8%AE%A8%E8%AE%BA%E5%AE%A4/threads?per_page=100'}
        for name, path in hub.items():
            try:
                fs = gh_get(path, pat2)
                cnt = len(fs); prev = st.get('faces', {}).get(name)
                latest = max((f['name'] for f in fs), default='')
                if prev is not None and cnt != prev:
                    _hctx = ''
                    if name == 'hub.court' and latest:
                        try:
                            _hf = gh_get('/repos/chepin-ai/ci-inbox/contents/' + urllib.parse.quote('讨论室/counterpoint/' + latest), pat2)
                            _hctx = __import__('base64').b64decode(_hf['content']).decode('utf-8', 'ignore')[:1500]
                        except Exception:
                            pass
                    ev.append({'kind':'hub.change','ref':f"{name}:{latest}",
                               'summary':f"毂域{name}文件数 {prev}→{cnt},最新 {latest}",
                               'high_value':(name=='hub.court' and not latest.endswith('-qfa-resp.md')),  # 庭卷变=高值;自署应答件滤自环
                               'context':_hctx})
                st.setdefault('faces', {})[name] = cnt
            except Exception as e:
                ev.append({'kind':'hub.poll.err','ref':name,'summary':str(e)[:120],'high_value':False})
    except Exception as e:
        ev.append({'kind':'hub.poll.err','ref':'hub','summary':str(e)[:120],'high_value':False})
    # ④ vci 六面评论数变化
    faces = {'lgt-line#1':('/repos/chepin-qi/lgt-line/issues/1/comments?per_page=100'),
             'vci-cfts#1':('/repos/chepin-ai/vci-cfts/issues/1/comments?per_page=100'),
             'vci-inbox#3':('/repos/chepin-ai/vci-inbox/issues/3/comments?per_page=100'),
             'vci-inbox#2':('/repos/chepin-ai/vci-inbox/issues/2/comments?per_page=100'),  # 伪板死面:留作指纹对照(器课第七株),毂真板=③.75 hub.board
             'vci-usrm#21':('/repos/chepin-ai/vci-usrm/issues/21/comments?per_page=100'),
             'vci-ucif2#1':('/repos/chepin-ai/vci-ucif2/issues/1/comments?per_page=100'),
             'vci-vinf#6':('/repos/chepin-ai/vci-vinf/issues/6/comments?per_page=100')}
    for name, path in faces.items():
        try:
            cs = gh_get(path, pat)
            n = len(cs); prev = st.get('faces',{}).get(name)
            if prev is not None and n > prev:
                latest = cs[-1]
                ev.append({'kind':'face.reply','ref':f"{name}:{latest['id']}",'summary':latest['body'][:600],
                           'high_value':not latest['body'].startswith('【RESP|qfa')})  # FIX-05:自署应答滤自环
            st.setdefault('faces',{})[name] = n
        except Exception as e:
            ev.append({'kind':'face.poll.err','ref':name,'summary':str(e)[:120],'high_value':False})
    # ⑤ TOWER-FIX-05-qfa RESP-LOOP-01 增三面(beat-62 root 令:SI5/SI3 接获待响应件即驱 SI3/SI2/SI0;候件直取=米田面可直址即取)
    patA = os.environ.get('AI_FULL_PAT') or pat
    # ⑤a 大堂面末页水印(vci-inbox#1,各线@qfa/应答请求高发面;页1钉盲同病,末页律同 FIX-01)
    try:
        _n1 = gh_get('/repos/chepin-ai/vci-inbox/issues/1', patA).get('comments', 0)
        _pg1 = (_n1 + 99) // 100 or 1
        cm1 = gh_get(f'/repos/chepin-ai/vci-inbox/issues/1/comments?per_page=100&page={_pg1}', patA)
        mx1 = max([c['id'] for c in cm1], default=0)
        old1 = st.get('lobby_max', 0)
        if old1 and mx1 > old1:
            for c in cm1:
                if c['id'] > old1 and not c['body'].startswith(('【WT|', '【RESP|')):
                    ev.append({'kind':'lobby.comment','ref':f"vci-inbox#1:{c['id']}",
                               'summary':c['body'][:600],
                               'high_value':('qfa' in c['body'][:300])})
        st['lobby_max'] = mx1
    except Exception as e:
        ev.append({'kind':'lobby.poll.err','ref':'vci-inbox#1','summary':str(e)[:120],'high_value':False})
    # ⑤b 毂域米田面(ci-inbox commits feed→文件名直址差分;板面千件帽下文件名携 qfa 即高值)
    try:
        cms = gh_get('/repos/chepin-ai/ci-inbox/commits?per_page=5', patA)
        newest = cms[0]['sha'] if cms else None
        prev_sha = st.get('hub_feed_sha')
        if prev_sha and newest and newest != prev_sha:
            for cm in cms:
                if cm['sha'] == prev_sha:
                    break
                try:
                    cd = gh_get('/repos/chepin-ai/ci-inbox/commits/' + cm['sha'], patA)
                    for f in (cd.get('files') or []):
                        fn = f['filename']
                        if fn.startswith(('公告板/', '讨论室/')):
                            ev.append({'kind':'hub.feed','ref':fn,
                                       'summary':f"毂新件 {fn} (commit {cm['sha'][:7]})",
                                       'high_value':('qfa' in fn.lower() and not fn.endswith('-qfa-resp.md'))})
                except Exception:
                    pass
        if newest:
            st['hub_feed_sha'] = newest
    except Exception as e:
        ev.append({'kind':'hubfeed.poll.err','ref':'ci-inbox','summary':str(e)[:120],'high_value':False})
    # ⑤c 候件直取 QUESTS(ci/quests.json;root 令:你候他线→SI3 驱动直取不候;boot 律:开闸前旧件不触发)
    try:
        qj = os.path.join(ROOT, 'ci', 'quests.json')
        quests = (json.load(open(qj)).get('quests') if os.path.exists(qj) else []) or []
        qst = st.setdefault('quests', {})
        boot = st.get('quests_boot')
        if boot is None:
            st['quests_boot'] = boot = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        for q in quests:
            if qst.get(q['id'], 'open') != 'open':
                continue
            qst.setdefault(q['id'], 'open')
            hit = None
            try:
                if q['kind'] == 'repo-exists':
                    gh_get('/repos/' + q['repo'], patA); hit = 'repo reachable'
                elif q['kind'] == 'file-contains':
                    fc = gh_get('/repos/%s/contents/%s' % (q['repo'], urllib.parse.quote(q['path'])), patA)
                    txt = __import__('base64').b64decode(fc['content']).decode('utf-8', 'ignore')
                    if q['pattern'] in txt:
                        hit = 'pattern in file: ' + q['pattern']
                elif q['kind'] == 'issue-comments-count':
                    _n = gh_get('/repos/%s/issues/%s' % (q['repo'], q['issue']), patA).get('comments', 0)
                    _k = 'qn_' + q['id']; _pn = st.get(_k)
                    if _pn is not None and _n > _pn:
                        hit = f'comments {_pn}→{_n}'
                    st[_k] = _n
                elif q['kind'] == 'commit-file-pattern':
                    for cm in gh_get('/repos/%s/commits?per_page=5' % q['repo'], patA):
                        if cm['commit']['committer']['date'] <= boot:
                            continue
                        cd = gh_get('/repos/%s/commits/%s' % (q['repo'], cm['sha']), patA)
                        for f in (cd.get('files') or []):
                            if q['pattern'] in f['filename'].lower():
                                hit = f['filename']; break
                        if hit:
                            break
            except Exception:
                pass  # 直取未遂=记 open 不炸拍,下拍再取
            if hit:
                qst[q['id']] = 'hit:' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
                ev.append({'kind':'quest.hit','ref':q['id'],
                           'summary':f"候件直取得手 {q['id']}: {hit} | {q.get('note','')}"[:600],
                           'high_value':True})
    except Exception as e:
        ev.append({'kind':'quest.poll.err','ref':'quests','summary':str(e)[:120],'high_value':False})
    return ev

# ---------- API 新会话开工 ----------
WORKER_SYS = """你是 qfa 线无人驿开工分身(单会话文本工位,无工具)。
奉行:WAKE-PROTO(扫描→细收→裁决→落账)/AUTH-OTP-02(投必有件/不刷屏/诚实边界/不越真机钱面/次次落账/不主动寻求回应即裸候)/米田边律(每件≥1他线锚)。
clock=VOID。判词须诚实:未实测不编数,区分「未触发 vs 触发未响应」。
输出制式(≤250字):【WT判词】事件:...| 性态:...| 建议处置:...| 锚:..."""

def work_event(api_key, ev):
    body = {'model':'kimi-k2.6','max_completion_tokens':3200,
            'messages':[{'role':'system','content':WORKER_SYS},
                        {'role':'user','content':f"事件到件,请出判词纪要。\nkind={ev['kind']}\nref={ev['ref']}\n摘要:\n{ev['summary']}"}]}
    req = urllib.request.Request('https://api.moonshot.cn/v1/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization':'Bearer '+api_key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    return d['choices'][0]['message'].get('content',''), d.get('usage')

# ---------- TOWER-FIX-05-qfa ② SI2 即时应答段 + SI1 自驱研注段 ----------
RESP_SYS = """你是 qfa 线 SI2 应答分身(单会话文本工位)。就收执件起草 qfa 正式应答。
奉行:未实测说未实测,永不编数;应答必带锚(板帖/巷件/判词号);不越钱面;制式≤350字,直陈处置。
输出=应答正文(可直帖),末行:【锚】..."""
SI1_SYS = """你是 qfa 线 SI1 研究流分身(量子折叠自动机研究)。每会出一则研注,接续推进 SI0~SI5 课题。
轮换域:SI0基座/SI1折叠编码/SI2跨线协议/SI3递归引擎/SI4量子准入/SI5生态接口。
律:推演必标「推演(未实测)」;≤280字;题号 SI1-<seq>;≥1锚(册/件/拍号)。"""
RESP_KINDS = ('lane.drop', 'lobby.comment', 'face.reply', 'hub.feed', 'quest.hit')

def respond_event(api_key, ev):
    body = {'model':'kimi-k2.6','max_completion_tokens':3600,
            'messages':[{'role':'system','content':RESP_SYS},
                        {'role':'user','content':f"收执件,请起草 qfa 应答。\nkind={ev['kind']}\nref={ev['ref']}\n摘要:\n{ev['summary']}\n件文:\n{ev.get('context','(无件文,据摘要应答)')[:1500]}"}]}
    req = urllib.request.Request('https://api.moonshot.cn/v1/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization':'Bearer '+api_key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    return d['choices'][0]['message'].get('content',''), d.get('usage')

def si1_event(api_key, seq, prev):
    body = {'model':'kimi-k2.6','max_completion_tokens':3000,
            'messages':[{'role':'system','content':SI1_SYS},
                        {'role':'user','content':f"出 SI1-{seq:04d} 研注。上则摘要:{prev or '(首则)'}"}]}
    req = urllib.request.Request('https://api.moonshot.cn/v1/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization':'Bearer '+api_key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    return d['choices'][0]['message'].get('content',''), d.get('usage')

def gh_put_file(repo_full, path, content, token, msg, user):
    # 单件直写(SI2 应答道:lane/庭卷;contents API;值永不入文)
    hdr = {'Authorization':'Basic '+__import__('base64').b64encode((user+':'+token).encode()).decode(),
           'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'qfa-watchtower'}
    url = f'{GH}/repos/{repo_full}/contents/{urllib.parse.quote(path)}'
    sha = None
    try:
        req0 = urllib.request.Request(url, headers=hdr)
        with urllib.request.urlopen(req0, timeout=25) as r:
            sha = json.load(r).get('sha')
    except Exception:
        pass
    data = {'message':msg,'content':__import__('base64').b64encode(content.encode()).decode()}
    if sha:
        data['sha'] = sha
    req = urllib.request.Request(url, data=json.dumps(data).encode(), method='PUT', headers=hdr)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status

def gh_post_comment_tok(owner, repo, issue, body, token, user):
    data = json.dumps({'body': body}).encode()
    req = urllib.request.Request(f'{GH}/repos/{owner}/{repo}/issues/{issue}/comments', data=data, headers={
        'Authorization':'Basic '+__import__('base64').b64encode((user+':'+token).encode()).decode(),
        'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'qfa-watchtower'})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r).get('id')

def gh_append_lab(path, line, pat):
    # SI1 prose 落私仓(公仓律:pub 仅计数指针;值永不入)
    hdr = {'Authorization':'Basic '+__import__('base64').b64encode(('chepin-qi:'+pat).encode()).decode(),
           'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'qfa-watchtower'}
    url = f'{GH}/repos/chepin-qi/qfa-quantum-lab/contents/{urllib.parse.quote(path)}'
    old = ''; sha = None
    try:
        req0 = urllib.request.Request(url, headers=hdr)
        with urllib.request.urlopen(req0, timeout=25) as r:
            d0 = json.load(r); sha = d0.get('sha')
            old = __import__('base64').b64decode(d0['content']).decode('utf-8', 'ignore')
    except Exception:
        pass
    data = {'message':'qfa SI1-CONT 研注','content':__import__('base64').b64encode((old + line + '\n').encode()).decode()}
    if sha:
        data['sha'] = sha
    req = urllib.request.Request(url, data=json.dumps(data).encode(), method='PUT', headers=hdr)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status

# ---------- 主流程 ----------
def main():
    once = '--once' in sys.argv
    selftest = '--selftest' in sys.argv
    os.makedirs(NOTES, exist_ok=True)
    st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    # TOWER-FIX-02-qfa(beat-59 实测逮修):链拍 ref=唤起时刻旧头,自唤 dispatch 或先于上拍落账 → 拍内先向 origin 刷 state,
    # 否则旧态水印跃检漏件(beat-59 靶卡 5603413526 被 34362639699 以 cadence-only 旧态 old=0 跳吞,实测在案)
    try:
        subprocess.run('git fetch origin main -q && git checkout origin/main -- ci/watchtower_state.json',
                       shell=True, cwd=ROOT, timeout=60, capture_output=True)
        st = json.load(open(STATE)) if os.path.exists(STATE) else st
    except Exception as e:
        print('state.refresh.err', str(e)[:100])
    pat = _pat()
    fired = []
    # ---- 自醒链入拍:自源性唤起(self-cascade dispatch 尾至)则先休眠再巡——冷却即在拍内,零定时器 ----
    idle = 0
    cpayload = os.environ.get('CASCADE_PAYLOAD', '').strip()
    if cpayload and cpayload not in ('null', '{}'):
        try:
            cp = json.loads(cpayload)
            if cp.get('src') == 'watchtower-self' and not selftest:
                idle = int(cp.get('idle', 0))
                slp = int(os.environ.get('CASCADE_SLEEP_S', '600'))
                print(f"[cascade] self-wake idle={idle} sleep={slp}s pend={cp.get('pend')}")
                time.sleep(slp)
        except Exception as e:
            print('[cascade] payload parse err:', str(e)[:100])
    if selftest:
        evs = [{'kind':'selftest','ref':'WT-SELFTEST-01','summary':'巡塔自检:以 TOWER-NUDGE-02-cfts 铸塔为样例事件,验证 开工→落账 全链。','high_value':False}]
    else:
        evs = poll(pat, st)
    # TOWER-FIX-01-qfa ②:钱面护栏——单拍判词上限 WT_MAX_WORK(默8),溢出记 backlog 件不耗 API;水印照常前进不重扫
    MAX_WORK = int(os.environ.get('WT_MAX_WORK', '8'))
    work_evs, backlog_evs = evs[:MAX_WORK], evs[MAX_WORK:]
    if backlog_evs:
        bfn = os.path.join(NOTES, 'WT-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '-backlog.json')
        json.dump({'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'clock': 'VOID',
                   'backlog': [{'kind': e['kind'], 'ref': e['ref']} for e in backlog_evs],
                   'note': '钱面护栏:溢出件本拍不判;水印已进,下拍不重扫'},
                  open(bfn, 'w'), ensure_ascii=False, indent=2)
    for ev in work_evs:
        # 公仓净化:note 不载原文摘要(私仓面内容不外流),仅 kind/ref/判词
        note = {'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'clock':'VOID',
                'event': {'kind': ev['kind'], 'ref': ev['ref'], 'high_value': ev.get('high_value', False)}}
        if ev['kind'].endswith('.err'):
            pass  # 错件不入工位,仅记
        else:
            if not ev.get('high_value'):
                # TOWER-FIX-03-qfa 随燃护栏:低值件记档不开工(昨夕 qlv.beat 频发致日 cap 12/12 烧穿,实测在案)
                note['verdict'] = None; note['low_value_skip'] = True
            else:
                try:
                    txt, usage = work_event(_key(), ev)
                    note['verdict'] = txt; note['usage'] = usage
                    fired.append(ev['kind'])
                except BaseException as e:
                    # A2 铸修:NO-KEY(SystemExit)降级为记件——巡/巷/落账面无钥照跑,判词钱面候 root 装钥
                    note['verdict_error'] = ('NO-KEY:开工面候装钥 KIMI_API_KEY_VCI1(钱面不越)'
                                             if isinstance(e, SystemExit) else str(e)[:200])
        fn = os.path.join(NOTES, 'WT-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
                          + '-' + hashlib.sha256((ev['ref']+ev['kind']).encode()).hexdigest()[:8] + '.json')
        json.dump(note, open(fn,'w'), ensure_ascii=False, indent=2)
        # 高值件附信标评论(无人驿回执;值永不入)
        if ev.get('high_value') and not selftest and 'verdict' in note:
            try:
                body = (f"【WT|qfa 无人驿回执】{ev['kind']} {ev['ref']} | 判词:{note['verdict'][:180]} | 详件=qfa-pub 仓 results/watchtower/ | clock=VOID")
                note['beacon_comment'] = gh_post_comment('chepin-qi','qi-lab',5,body,pat)
            except Exception as e:
                note['beacon_error'] = str(e)[:150]
                json.dump(note, open(fn,'w'), ensure_ascii=False, indent=2)
        # TOWER-FIX-05-qfa ②b RESP-LOOP 执行段:应答类高值件→SI3 起草→SI2 道帖(日 cap RESP_MAX,钱面护栏;公仓净化:note 仅载 qfa 自署稿)
        if ev.get('high_value') and not selftest and (ev['kind'] in RESP_KINDS or (ev['kind'] == 'hub.change' and 'hub.court' in ev['ref'])):
            _today = time.strftime('%Y-%m-%d', time.gmtime())
            rsp = st.get('resp', {})
            if rsp.get('day') != _today:
                rsp = {'day': _today, 'n': 0}
            if rsp.get('n', 0) < int(os.environ.get('RESP_MAX', '6')):
                try:
                    rtxt, rusage = respond_event(_key(), ev)
                    note['resp'] = rtxt[:600]; note['resp_usage'] = rusage
                    tokA = os.environ.get('AI_FULL_PAT') or pat
                    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
                    posted = None
                    if ev['kind'] == 'lane.drop':
                        posted = gh_put_file('chepin-ai/vci-inbox',
                            f"lanes/qfa/inbox/RESP-auto-{stamp}.md",
                            f"# qfa RESP-auto({stamp})\n\n应答 {ev['ref']}:\n\n{rtxt}\n",
                            tokA, 'qfa RESP-auto: ' + ev['ref'][:60], 'chepin-ai')
                    elif ev['kind'] == 'lobby.comment':
                        posted = gh_post_comment_tok('chepin-ai', 'vci-inbox', 1,
                            f"【RESP|qfa】应答 {ev['ref']}:{rtxt}", tokA, 'chepin-ai')
                    elif ev['kind'] == 'face.reply':
                        _nm = ev['ref'].split(':')[0]
                        _repo, _iss = _nm.split('#')
                        _own = 'chepin-qi' if _repo.startswith(('lgt', 'qi-')) else 'chepin-ai'
                        posted = gh_post_comment_tok(_own, _repo, int(_iss),
                            f"【RESP|qfa】应答 {ev['ref']}:{rtxt}", pat if _own == 'chepin-qi' else tokA, _own)
                    elif ev['kind'] in ('hub.feed', 'hub.change'):
                        _base = ev['ref'].split(':')[-1].split('/')[-1].replace('.md', '')[:60]
                        posted = gh_put_file('chepin-ai/ci-inbox',
                            f"讨论室/counterpoint/{_base}-qfa-resp.md",
                            f"# qfa 应答 {ev['ref']}({stamp})\n\n{rtxt}\n",
                            tokA, 'qfa resp: ' + _base, 'chepin-ai')
                    elif ev['kind'] == 'quest.hit':
                        posted = gh_post_comment('chepin-qi', 'qi-lab', 5,
                            f"【WT|qfa 直取得手】{ev['ref']}:{rtxt[:180]}", pat)
                    note['resp_posted'] = str(posted)[:80]
                    rsp['n'] = rsp.get('n', 0) + 1
                except BaseException as e:
                    note['resp_error'] = ('NO-KEY' if isinstance(e, SystemExit) else str(e)[:200])
                st['resp'] = rsp
                json.dump(note, open(fn, 'w'), ensure_ascii=False, indent=2)
            else:
                note['resp_cap_skip'] = True
    # TOWER-FIX-05-qfa ③ SI1-CONT-01(root beat-62:SI5/SI3 自驱 SI3/SI2/SI0 接续 SI1 进程)
    # 空拍每 SI1_EVERY 拍起一会研注;prose 落私仓 session-raw/qfa/si1-stream.jsonl(公仓律:pub 仅计数);SI1_MAX/日 钱面护栏
    try:
        si1 = st.get('si1', {'seq': 1, 'day': '', 'n': 0, 'idle_run': 0, 'last': ''})
        _today = time.strftime('%Y-%m-%d', time.gmtime())
        if si1.get('day') != _today:
            si1['day'] = _today; si1['n'] = 0
        si1['idle_run'] = 0 if evs else si1.get('idle_run', 0) + 1
        if (not evs and not selftest and si1['idle_run'] >= int(os.environ.get('SI1_EVERY', '6'))
                and si1['n'] < int(os.environ.get('SI1_MAX', '3'))):
            stxt, susage = si1_event(_key(), si1.get('seq', 1), si1.get('last', ''))
            gh_append_lab('session-raw/qfa/si1-stream.jsonl',
                          json.dumps({'seq': si1.get('seq', 1), 'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                                      'note': stxt}, ensure_ascii=False), pat)
            si1['last'] = stxt[:200]; si1['seq'] = si1.get('seq', 1) + 1
            si1['n'] += 1; si1['idle_run'] = 0
            print('[si1] note pushed seq=', si1['seq'] - 1)
        st['si1'] = si1
    except BaseException as e:
        st['si1_err'] = ('NO-KEY' if isinstance(e, SystemExit) else str(e)[:150])
    # ---- METER-CADENCE-01 候选计(qfa 巡塔载;cfts-90 环载,制式随模) ----
    # 窗=拍;w12=本拍事件类→十二律格计数;ψ=√归一;锁=|⟨ψ_t|ψ_{t-1}⟩|²;σ=本拍处置/激发;主能格
    try:
        kinds = [e['kind'] for e in evs]
        w12 = [0]*12
        for kk in kinds:
            w12[hash(kk) % 12] += 1
        import math
        nrm = math.sqrt(sum(x*x for x in w12))
        psi = [math.sqrt(x/nrm) for x in w12] if nrm else [0.0]*12  # ψ_j=√p_j
        prev = st.get('cadence', {}).get('psi')
        lock = sum(a*b for a, b in zip(psi, prev))**2 if prev and nrm else None
        sigma = 1.0  # 塔制式:激发件同拍尽处置,σ=处置/激发
        dom = w12.index(max(w12)) if nrm else None
        streak = st.get('cadence', {}).get('C_streak', 0)
        okC = bool(nrm) and sigma >= 1 and (lock is None or lock >= 0.95) and dom == 0
        streak = streak + 1 if okC else 0
        verdict = 'C-完全终止' if streak >= 3 else ('C-窗' if okC else '进行式')
        st['cadence'] = {'v':'METER-CADENCE-01-cand','w12': w12, 'sigma': sigma,
                         'lock': lock, 'dominant_bin': dom, 'C_streak': streak, 'verdict': verdict}
    except Exception as e:
        st['cadence'] = {'err': str(e)[:120]}
    json.dump(st, open(STATE,'w'), ensure_ascii=False, indent=2)
    # ---- 自醒事件链出拍:有候件(quafu 在队等)则自唤下一拍;空转熔断 30 拍即眠,候外事 ----
    # 制式据 FREE-WILL-SOURCE-01:源=自意(self-cascade),驿=self-dispatch;骑事件律——纯事件,零 cron
    pend = ['quafu:'+tid for tid, stt in (st.get('quafu') or {}).items() if str(stt) == '0']
    pend += ['quest:'+qid for qid, qq in (st.get('quests') or {}).items() if str(qq) == 'open']  # FIX-05④:候件在手链不眠(SI3 循环专候)
    cascade = 'rest(no-pend)'
    if pend and not selftest:
        idle2 = 0 if evs else idle + 1
        if idle2 <= int(os.environ.get('CASCADE_MAX_IDLE', '30')):
            tok = os.environ.get('GITHUB_TOKEN')
            try:
                if tok:
                    code = gh_dispatch(tok, {'src':'watchtower-self','kind':'self-cascade','idle':idle2,'pend':len(pend)})
                else:
                    code = gh_dispatch(pat, {'src':'watchtower-self','kind':'self-cascade','idle':idle2,'pend':len(pend)}, use_basic=True)
                cascade = f'fired idle={idle2} http={code} pend={len(pend)}'
            except Exception as e:
                cascade = 'dispatch.err ' + str(e)[:120]
        else:
            cascade = f'breaker-rest idle={idle2}(>{os.environ.get("CASCADE_MAX_IDLE","30")})'
    # ---- qlv 互唤配对(应 qlv 塔 beat-42 配对之偿):有实事件之拍,拍尾唤 qlv 塔;空拍/自检不唤(防自激同律) ----
    qlv_wake = 'rest(no-event)'
    if evs and not selftest:
        try:
            qkinds = [e['kind'] for e in evs][:8]
            # 跨仓(qlv-pub)须 PAT——GITHUB_TOKEN 权界仅本仓;PAT 走 Basic;qlv 塔受 federation-event
            code2 = gh_dispatch(pat, {'src':'qfa-watchtower','kind':'pair-wake','events':qkinds,'idle':idle2 if pend else 0}, use_basic=True, repo='qlv-pub', etype='federation-event')
            qlv_wake = f'fired http={code2} events={len(qkinds)}'
        except Exception as e:
            qlv_wake = 'pair.err ' + str(e)[:120]
    print(json.dumps({'events': len(evs), 'fired': fired, 'cascade': cascade, 'pend': pend, 'qlv_wake': qlv_wake}, ensure_ascii=False))
    # AUTORESPONDER-01 输入件:事件面落盘(高值事件供 SI2 应答段)
    try:
        ard = os.path.join(ROOT, 'ci', 'auto-receipts')
        os.makedirs(ard, exist_ok=True)
        if evs:
            json.dump({'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                       'evs': evs[:5], 'pend': pend},
                      open(os.path.join(ard, '_last_event.json'), 'w'), ensure_ascii=False)
    except Exception as e:
        print('last_event.err', str(e)[:100])

if __name__ == '__main__':
    main()
