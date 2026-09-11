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
# TOWER-FIX-08-qfa(beat-76 root 令「所有候直通」):CAS字段级并落账(采 cisvr v1.5 CAS三段式互领养)——跃检残根治,并发覆写无损
# TOWER-FIX-11-qfa(beat-82 root令「下拍SI2/SI0直推;毂外有轮/脊外有鼎炉/塔外有环-圈」):mention-watch泛化三路(ucif2-120+/鼎炉代产单/我巷inbox)——机层直推之目
# TOWER-FIX-12-qfa(beat-82 无候律实证病灶):quest探针token按仓域路由(pat_for)——AIF读chepin-qi域404致CFTS-REPO-SEED假open;本FIX之验证即该quest自闭
# TOWER-FIX-13-qfa(beat-83 root令「耦合/嵌入/汇聚各SI经SI5激发SI1」):SI1-SEED-01供种面——forge请求/open-quest/mention旗/签件inbox机汇si1/SEED-QUEUE.json,SI1采种即研
# TOWER-FIX-14-qfa(beat-84 root令「ucif2-129§5.1犯律根因/机制为何未拦」):LEAK-GATE-01写后巡闸——泛型密钥模式扫(零秘密材料),命中机旗永不录子串;根因答=写前闸/写后巡/共享表三缺,本FIX补写后巡
# TOWER-FIX-15-qfa(beat-84实证回归):FIX-13供种块作用域病(ev在cadence域未绑定,evs才是事件列)——put成而state记err致幂等键永不落、每拍重推;本FIX复幂等
# TOWER-FIX-16-qfa(beat-86 root令「三面全线可见无死角」):SURFACE-MIRROR-01双域镜——ci活性件→vci mirror;vci野问件→ci mirror-vci;板目树账;树sha比对仅异取水(配额自觉,器课廿九)
# TOWER-FIX-10-qfa(beat-80 root 令「机驱/全驱主动回应ucif2-120~125及之后;候件不主动取得=裸候违规」):
#   ①quest kind 增 file-exists(直探址在=hit;commit窗口病根治:旧commit之件亦可闭) ②⑤d ucif2-watch:新ucif2-N帖(N>=120)内容扫,涉qfa即机旗
# TOWER-FIX-09-qfa(beat-75 root 令「环延伸/反向驱动」):sealed 解装腿抽公+③.6 vci-qfa/inbox 密封囊守望面(N28 消号道;SI0 直解直装不占 RESP 额,值零回显)
# TOWER-FIX-07-qfa(beat-70 root 令「会后持续迭代/反向涟漪:SI0→SI2→SI3→SI5」):
#   ①内容hash idem集 sha256(kind|ref)[:12] 截尾300(采lgt/usrm闸升位)——quest overlay 跃检回退之重火被吞,同件永不复执
#   ②SI0→SI2 反向涟漪:SI1-CONT 研注机读摘投毂板 qfa-voice(SI1_VOICE_MAX=1/日,首行诚实声明,全文私链守公域律)——会后 SI1 续迭不系会话存留
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
                       'summary':f"巷卡 {prev_cnt}→{cnt},最新 {latest}",
                       'high_value':not latest.startswith(('RESP-', '_')),  # FIX-05c:自署RESP/账件降格滤自环(首应即燃自帖实测逮修)
                       'context':_lctx})
        st['lane_inbox_count'] = cnt
    except Exception as e:
        ev.append({'kind':'lane.poll.err','ref':'lanes/qfa/inbox','summary':str(e)[:120],'high_value':False})
    # ③.6 vci-qfa/inbox 密封囊守望(TOWER-FIX-09-qfa beat-75:N28 消号道;差集即火,AI_FULL_PAT 面,零额度常开)
    try:
        _vq = gh_get('/repos/chepin-ai/vci-qfa/contents/inbox?per_page=100', os.environ.get('AI_FULL_PAT') or pat)
        if isinstance(_vq, list):
            _seen9 = st.setdefault('vciqfa_sealed_seen', [])
            for _f9 in _vq:
                _fn9 = _f9.get('name', '')
                if _fn9.startswith('sealed-') and _fn9.endswith('.md') and _fn9 not in _seen9:
                    ev.append({'kind':'sealed.vciqfa','ref':'vci-qfa/inbox:' + _fn9,'summary':'密封囊新件 ' + _fn9,'high_value':True})
                    _seen9.append(_fn9)
            del _seen9[:-50]
    except Exception as e:
        ev.append({'kind':'sealed.vciqfa.err','ref':'vci-qfa/inbox','summary':str(e)[:120],'high_value':False})
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
    pat_for = lambda repo: pat if repo.startswith('chepin-qi/') else patA  # TOWER-FIX-12-qfa(beat-82):quest探针按仓域路由token——AIF读不到chepin-qi域(cfts-seed 404假open实证),路由后全域可探
    # ⑤a 大堂面末页水印(vci-inbox#1,各线@qfa/应答请求高发面;页1钉盲同病,末页律同 FIX-01)
    try:
        _n1 = gh_get('/repos/chepin-ai/vci-inbox/issues/1', patA).get('comments', 0)
        _pg1 = (_n1 + 99) // 100 or 1
        cm1 = gh_get(f'/repos/chepin-ai/vci-inbox/issues/1/comments?per_page=100&page={_pg1}', patA)
        mx1 = max([c['id'] for c in cm1], default=0)
        old1 = st.get('lobby_max', 0)
        if old1 and mx1 > old1:
            for c in cm1:
                if c['id'] > old1 and not (c['body'].startswith('【') and '|qfa' in c['body'][:24]):  # FIX-05e:凡自署件(【X|qfa)一律滤自环,不枚举
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
                                       'high_value':('qfa' in fn.lower() and not fn.split('/')[-1].startswith('qfa-') and not fn.endswith('-qfa-resp.md'))})  # FIX-05e:己署板帖滤自环
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
                    gh_get('/repos/' + q['repo'], pat_for(q['repo'])); hit = 'repo reachable'  # FIX-12
                elif q['kind'] == 'file-exists':
                    gh_get('/repos/%s/contents/%s' % (q['repo'], urllib.parse.quote(q['path'])), pat_for(q['repo']))  # FIX-12
                    hit = 'file exists: ' + q['path']
                elif q['kind'] == 'file-contains':
                    fc = gh_get('/repos/%s/contents/%s' % (q['repo'], urllib.parse.quote(q['path'])), pat_for(q['repo']))  # FIX-12
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
    # TOWER-FIX-10-qfa ⑤d ucif2-watch:新ucif2-N帖(N>=120)内容扫,涉qfa即机旗;uw册=已见集,重拍不复旗
    try:
        uw = st.setdefault('ucif2_watch', {})
        for cm in gh_get('/repos/chepin-ai/ci-inbox/commits?per_page=8', patA):
            if cm['commit']['committer']['date'] <= boot:
                continue
            cd = gh_get('/repos/chepin-ai/ci-inbox/commits/' + cm['sha'], patA)
            for f in (cd.get('files') or []):
                fn = f['filename']; base = fn.split('/')[-1]
                # TOWER-FIX-11-qfa(beat-82 root令「下拍SI2/SI0直推;鼎炉/轮/环-圈」):mention-watch泛化——ucif2-120+帖 + 鼎炉代产单 + 我巷件,三路涉qfa即机旗
                if fn.startswith(('公告板/ucif2-','ucif2-')):
                    tok = base.split('-')[1] if '-' in base else ''
                    if not (tok.isdigit() and int(tok) >= 120):
                        continue
                elif fn.startswith(('shared/forge/requests/','lanes/qfa/inbox/')):
                    pass
                else:
                    continue
                if fn in uw:
                    continue
                m = None
                try:
                    fc = gh_get('/repos/chepin-ai/ci-inbox/contents/' + urllib.parse.quote(fn), patA)
                    txt = __import__('base64').b64decode(fc['content']).decode('utf-8', 'ignore')
                    m = 'qfa' in txt.lower()
                except Exception:
                    m = None
                uw[fn] = 'mention-qfa' if m else 'seen'
                if m:
                    ev.append({'kind':'ucif2.watch','ref':fn,
                               'summary':('ucif2帖涉qfa机旗(内容扫): '+fn)[:600],
                               'high_value':True})
    except Exception as e:
        ev.append({'kind':'ucif2watch.err','ref':'ci-inbox','summary':str(e)[:120],'high_value':False})
    # TOWER-FIX-14-qfa LEAK-GATE-01(beat-84 root令「找犯律根因/为何机制未拦住」之机层答):写后巡闸——泛型密钥模式扫(ghp_/gho_/ghs_/ghu_/github_pat_/sk-/AKID),零秘密材料可装;命中即high_value机旗,永不录匹配子串本身;不自动涂销(涂销=铁律人事,闸只报警)
    try:
        import re as _re14
        _pats14 = [r'ghp_[A-Za-z0-9]{30,}', r'gho_[A-Za-z0-9]{30,}', r'ghs_[A-Za-z0-9]{30,}',
                   r'ghu_[A-Za-z0-9]{30,}', r'github_pat_[A-Za-z0-9_]{30,}', r'sk-[A-Za-z0-9]{20,}', r'AKID[A-Za-z0-9]{13,}']
        _lg = st.setdefault('leak_gate', {'seen': [], 'hits': []})
        for cm in gh_get('/repos/chepin-ai/ci-inbox/commits?per_page=8', patA):
            if cm['commit']['committer']['date'] <= boot:
                continue
            cd = gh_get('/repos/chepin-ai/ci-inbox/commits/' + cm['sha'], patA)
            for f in (cd.get('files') or []):
                fn = f['filename']
                if not fn.endswith(('.md', '.json', '.py', '.txt', '.jsonl')):
                    continue
                key14 = fn + '@' + cm['sha'][:12]
                if key14 in _lg['seen']:
                    continue
                _lg['seen'].append(key14)
                _lg['seen'] = _lg['seen'][-400:]
                try:
                    fc = gh_get('/repos/chepin-ai/ci-inbox/contents/' + urllib.parse.quote(fn), patA)
                    txt = __import__('base64').b64decode(fc['content']).decode('utf-8', 'ignore')
                except Exception:
                    continue
                for p in _pats14:
                    if _re14.search(p, txt):
                        hit14 = {'file': fn, 'pat': p[:5], 'commit': cm['sha'][:12]}
                        if hit14 not in _lg['hits']:
                            _lg['hits'].append(hit14)
                            _lg['hits'] = _lg['hits'][-40:]
                            ev.append({'kind': 'leak.gate.hit', 'ref': fn,
                                       'summary': ('铁律机旗:密钥模式命中(子串永不录) pat=%s file=%s commit=%s' % (p[:5], fn, cm['sha'][:12]))[:600],
                                       'high_value': True})
    except Exception as e:
        ev.append({'kind': 'leakgate.err', 'ref': 'ci-inbox', 'summary': str(e)[:120], 'high_value': False})
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

# TOWER-FIX-06-qfa ① 封件直取解封轨(beat-63/64 root 令:SI5 接件→SI0 即装,值永不入文零回显)
def handle_sealed(ev, st, pat):
    """quest.hit(SEALED-V2-RESEAL/ISSUE-874-COMMENT)→#874 串取密文→QFA_PK_V2_SK 内存解→装 lab Secrets→唯记 sha 锚。
    诚实律:解封失败/钥缺=记件不炸拍;格式 JSON 或 KEY=VALUE 行,解析不得则整包装 QFA_OPS_PACK_V2。"""
    import re as _re
    sk = os.environ.get('QFA_PK_V2_SK')
    if not sk:
        return {'sealed_error': 'NO-KEY: QFA_PK_V2_SK 未装(候装钥,钱面不越)'}
    tokA = os.environ.get('AI_FULL_PAT') or pat
    blob = None
    try:
        cm = gh_get('/repos/chepin-ai/ci-inbox/issues/874/comments?per_page=10', tokA)
        for c in cm:
            m = _re.search(r'```\s*([A-Za-z0-9+/=\n]{200,})\s*```', c.get('body', ''))
            if m:
                blob = m.group(1)
        if not blob:
            ib = gh_get('/repos/chepin-ai/ci-inbox/issues/874', tokA).get('body', '')
            m = _re.search(r'```\s*([A-Za-z0-9+/=\n]{200,})\s*```', ib)
            blob = m.group(1) if m else None
    except Exception as e:
        return {'sealed_error': 'fetch: ' + str(e)[:120]}
    if not blob:
        return {'sealed_note': 'hit 而密文未寻得(#874 串无 b64 块),候下拍再取'}
    return sealed_decode_install(blob, sk, pat)

# TOWER-FIX-09-qfa(beat-75 root 令「环延伸/反向驱动」·N28 消号道):解装腿抽公 sealed_decode_install;③.6 vci-qfa/inbox 密封囊守望面(lvlu SealedBox 囊到→SI0 即解即装→唯记 sha16 锚)。律同 FIX-06:值永不入文零回显;败则记件不炸拍
def sealed_decode_install(blob, sk, pat):
    """b64 密文→QFA_PK_V2_SK 内存解→JSON/KEY=VALUE 解析→逐键装 lab Secrets→唯记 sha16 锚。"""
    import re as _re
    try:
        from nacl.public import PrivateKey, SealedBox
        import nacl.encoding
        _sk = PrivateKey(sk, encoder=nacl.encoding.Base64Encoder)
        pt = SealedBox(_sk).decrypt(__import__('base64').b64decode(blob)).decode()
        _sk = None
    except Exception as e:
        return {'sealed_error': 'decrypt: ' + str(e)[:120]}
    sha = hashlib.sha256(pt.encode()).hexdigest()[:16]
    kv = None
    try:
        d0 = json.loads(pt)
        if isinstance(d0, dict):
            kv = d0
    except Exception:
        pass
    if kv is None:
        kv = {}
        for ln in pt.splitlines():
            if '=' in ln and not ln.strip().startswith('#'):
                k, v = ln.split('=', 1)
                k = k.strip()
                if _re.fullmatch(r'[A-Z][A-Z0-9_]{2,}', k):
                    kv[k] = v.strip()
    if not kv:
        kv = {'QFA_OPS_PACK_V2': pt}
    installed = []
    for k, v in kv.items():
        try:
            pkd = gh_get('/repos/chepin-qi/qfa-quantum-lab/actions/secrets/public-key', pat)
            from nacl.public import PublicKey as _PK
            box = SealedBox(_PK(pkd['key'], encoder=nacl.encoding.Base64Encoder))
            enc = box.encrypt(v.encode(), encoder=nacl.encoding.Base64Encoder).decode()
            req = urllib.request.Request(GH + '/repos/chepin-qi/qfa-quantum-lab/actions/secrets/' + k,
                data=json.dumps({'encrypted_value': enc, 'key_id': pkd['key_id']}).encode(), method='PUT',
                headers={'Authorization': 'Basic ' + __import__('base64').b64encode(('chepin-qi:' + pat).encode()).decode(),
                         'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=25) as r:
                installed.append(k + ':' + str(r.status))
        except Exception as e:
            installed.append(k + ':ERR:' + str(e)[:60])
        v = None
    pt = None
    return {'sealed_installed': installed, 'sealed_sha16': sha}


def handle_sealed_vciqfa(ev, st, pat):
    """FIX-09:vci-qfa/inbox/sealed-*.md→b64 块(```围或裸长串)→sealed_decode_install。"""
    import re as _re
    sk = os.environ.get('QFA_PK_V2_SK')
    if not sk:
        return {'sealed_error': 'NO-KEY: QFA_PK_V2_SK 未装(候装钥,钱面不越)'}
    tokA = os.environ.get('AI_FULL_PAT') or pat
    fn = ev['ref'].split(':', 1)[1]
    try:
        fd = gh_get('/repos/chepin-ai/vci-qfa/contents/inbox/' + urllib.parse.quote(fn), tokA)
        body = __import__('base64').b64decode(fd['content']).decode('utf-8', 'ignore')
    except Exception as e:
        return {'sealed_error': 'fetch: ' + str(e)[:120]}
    m = _re.search(r'```\s*([A-Za-z0-9+/=\n]{80,})\s*```', body)
    if m:
        blob = m.group(1)
    else:
        m2 = _re.search(r'([A-Za-z0-9+/=]{80,})', body)
        blob = m2.group(1) if m2 else None
    if not blob:
        return {'sealed_note': 'hit 而密文未寻得(' + fn + ' 无 b64 块),候下拍再取'}
    r = sealed_decode_install(blob, sk, pat)
    r['sealed_src'] = fn
    return r


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
        # TOWER-FIX-09-qfa:密封囊件 SI0 直解直装(机械件不占 RESP 额;idem 吞重火;值零回显)
        if ev.get('kind') == 'sealed.vciqfa' and not selftest:
            _idem9 = st.setdefault('idem', [])
            _ik9 = hashlib.sha256((ev['kind'] + '|' + ev['ref']).encode()).hexdigest()[:12]
            if _ik9 in _idem9:
                note['idem_skip'] = _ik9
            else:
                note.update(handle_sealed_vciqfa(ev, st, pat))
                _idem9.append(_ik9); del _idem9[:-300]
            json.dump(note, open(fn, 'w'), ensure_ascii=False, indent=2)
        # TOWER-FIX-05-qfa ②b RESP-LOOP 执行段:应答类高值件→SI3 起草→SI2 道帖(日 cap RESP_MAX,钱面护栏;公仓净化:note 仅载 qfa 自署稿)
        if ev.get('high_value') and not selftest and (ev['kind'] in RESP_KINDS or (ev['kind'] == 'hub.change' and 'hub.court' in ev['ref'])):
            _today = time.strftime('%Y-%m-%d', time.gmtime())
            rsp = st.get('resp', {})
            if rsp.get('day') != _today:
                rsp = {'day': _today, 'n': 0}
            _idem = st.setdefault('idem', [])
            _ik = hashlib.sha256((ev['kind'] + '|' + ev['ref']).encode()).hexdigest()[:12]  # FIX-07①
            if _ik in _idem:
                note['idem_skip'] = _ik  # 同件永不复执(overlay回退重火亦吞)
            elif rsp.get('n', 0) < int(os.environ.get('RESP_MAX', '6')):
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
                        if ev['ref'] in ('SEALED-V2-RESEAL', 'ISSUE-874-COMMENT'):
                            _hs = handle_sealed(ev, st, pat)  # FIX-06①:封件到→SI0 即装,值零回显
                            note.update(_hs)
                        posted = gh_post_comment('chepin-qi', 'qi-lab', 5,
                            f"【WT|qfa 直取得手】{ev['ref']}:{rtxt[:180]}", pat)
                    note['resp_posted'] = str(posted)[:80]
                    rsp['n'] = rsp.get('n', 0) + 1
                    _idem.append(_ik); del _idem[:-300]  # 截尾300(lgt制)
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
        si1['beats'] = si1.get('beats', 0) + 1
        _since = si1['beats'] - si1.get('last_fired_beat', 0)
        if (not selftest and si1['n'] < int(os.environ.get('SI1_MAX', '3'))
                and ((not evs and si1['idle_run'] >= int(os.environ.get('SI1_EVERY', '6')))
                     or _since >= int(os.environ.get('SI1_FORCE_EVERY', '18')))):  # FIX-05d:饥饿护栏——事件密集拍序亦保底研注(联邦活跃期 SI1 不饿殍)
            si1['last_fired_beat'] = si1['beats']
            stxt, susage = si1_event(_key(), si1.get('seq', 1), si1.get('last', ''))
            gh_append_lab('session-raw/qfa/si1-stream.jsonl',
                          json.dumps({'seq': si1.get('seq', 1), 'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                                      'note': stxt}, ensure_ascii=False), pat)
            si1['last'] = stxt[:200]; si1['seq'] = si1.get('seq', 1) + 1
            si1['n'] += 1; si1['idle_run'] = 0
            print('[si1] note pushed seq=', si1['seq'] - 1)
            # FIX-07②:SI0→SI2 反向涟漪——研注机读摘投毂板(日1件,首行诚实声明,公域律:摘非全文)
            if si1.get('voice_day') != _today:
                si1['voice_day'] = _today; si1['voice_n'] = 0
            if si1.get('voice_n', 0) < int(os.environ.get('SI1_VOICE_MAX', '1')):
                try:
                    _tokA = os.environ.get('AI_FULL_PAT') or pat
                    _st2 = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
                    gh_put_file('chepin-ai/ci-inbox', '公告板/qfa-voice-%s.md' % _st2,
                        '# qfa-voice(SI3 塔生研注·机读摘 %s)\n\n**首行声明: 本件系塔侧 SI1-CONT 研注之机读摘,非 SI1 会话判词;未实测不编数。**\n\nseq=%d 摘:\n\n%s\n\n(全文私链 session-raw/qfa/si1-stream.jsonl)\n' % (_st2, si1.get('seq', 1) - 1, stxt[:280]),
                        _tokA, 'qfa-voice: SI1-CONT seq %d' % (si1.get('seq', 1) - 1), 'chepin-ai')
                    si1['voice_n'] = si1.get('voice_n', 0) + 1
                except BaseException as e2:
                    st['voice_err'] = str(e2)[:150]
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
    # ---- TOWER-FIX-13-qfa SI1-SEED-01(beat-83 root令「未来如何耦合/嵌入/汇聚各SI并通过SI5协同互作,激发SI1」):SI5面供种——forge请求/open-quest/mention-qfa旗/签件inbox 机汇SEED-QUEUE,SI1采种即研(激发SI1之机层道;公域律:仅kind+ref,无prose) ----
    try:
        _seeds = []
        _t13 = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        def _ls13(repo, path):
            try:
                _d = gh_get('/repos/%s/contents/%s' % (repo, urllib.parse.quote(path)), pat_for(repo))
                return [_x['name'] for _x in _d if _x['name'] != '.gitkeep']
            except Exception:
                return []
        for _fn in _ls13('chepin-ai/ci-inbox', 'shared/forge/requests'):
            _seeds.append({'kind': 'forge-request', 'ref': 'shared/forge/requests/' + _fn})
        for _fn in _ls13('chepin-ai/vci-inbox', 'lanes/qfa/inbox'):
            _seeds.append({'kind': 'lane-inbox-vci', 'ref': 'lanes/qfa/inbox/' + _fn})
        for _fn in _ls13('chepin-ai/ci-inbox', 'lanes/qfa/inbox'):
            _seeds.append({'kind': 'lane-inbox-ci', 'ref': 'lanes/qfa/inbox/' + _fn})
        for _qn, _qv in (st.get('quests') or {}).items():
            if str(_qv) == 'open':
                _seeds.append({'kind': 'quest-open', 'ref': _qn})
        _uw13 = [_k for _k, _v in (st.get('ucif2_watch') or {}).items() if _v == 'mention-qfa']
        for _k in _uw13[-5:]:
            _seeds.append({'kind': 'mention-qfa', 'ref': _k})
        _sq = {'v': 'SI1-SEED-01', 'ts': _t13, 'n': len(_seeds), 'seeds': _seeds[-40:]}
        _sqs = json.dumps(_sq, ensure_ascii=False, sort_keys=True, indent=1)
        _sqh = hashlib.sha256(_sqs.encode()).hexdigest()[:12]
        if (st.get('seed_queue') or {}).get('h') != _sqh:
            gh_put_file('chepin-qi/qfa-pub', 'si1/SEED-QUEUE.json', _sqs + '\n', pat, 'SI1-SEED-01: %d seeds %s' % (len(_seeds), _t13), 'chepin-qi')
            evs.append({'kind': 'si1.seed.put', 'ref': 'si1/SEED-QUEUE.json', 'summary': '%d seeds h=%s' % (len(_seeds), _sqh), 'high_value': False})
        st['seed_queue'] = {'h': _sqh, 'n': len(_seeds), 'ts': _t13}
    except Exception as e:
        st['seed_queue'] = {'err': str(e)[:150]}
    # ---- TOWER-FIX-16-qfa SURFACE-MIRROR-01(beat-86 root令「野问册与usrm新开统一/讨论室·公告板·野问册全线可见无死角」):双域镜——ci活性交互件→vci-inbox mirror/ci/(vci域线可读);vci lanes野问件→ci 讨论室/mirror-vci/(ucif2可读);树sha比对仅异件取水,配额自觉(器课廿九) ----
    try:
        _mirs16 = [
            ('讨论室/WILD-Q-MERGED-01.md', 'mirror/ci/WILD-Q-MERGED-01.md'),
            ('讨论室/AIF-SUNSET-01-BALLOT.md', 'mirror/ci/AIF-SUNSET-01-BALLOT.md'),
            ('讨论室/SI-STATE-V1-STANDARD.md', 'mirror/ci/SI-STATE-V1-STANDARD.md'),
            ('讨论室/SI-CONVERGENCE-01.md', 'mirror/ci/SI-CONVERGENCE-01.md'),
            ('shared/rota/ROTA-01.md', 'mirror/ci/ROTA-01.md'),
            ('shared/forge/FORGE-01-protocol.md', 'mirror/ci/FORGE-01-protocol.md'),
        ]
        _tci16 = {t['path']: t['sha'] for t in gh_get('/repos/chepin-ai/ci-inbox/git/trees/main?recursive=1', patA).get('tree', [])}
        _tvi16 = {t['path']: t['sha'] for t in gh_get('/repos/chepin-ai/vci-inbox/git/trees/main?recursive=1', patA).get('tree', [])}
        _mig = 0
        for _src, _dst in _mirs16:
            if _src in _tci16 and _tci16.get(_src) != _tvi16.get(_dst):
                _fc = gh_get('/repos/chepin-ai/ci-inbox/contents/' + urllib.parse.quote(_src), patA)
                _txt = __import__('base64').b64decode(_fc['content']).decode('utf-8', 'ignore')
                gh_put_file('chepin-ai/vci-inbox', _dst, _txt, patA, 'SURFACE-MIRROR-01: ' + _src.split('/')[-1], 'chepin-ai')
                _mig += 1
        for _p in _tvi16:
            if _p.startswith('lanes/') and '/outbox/' in _p and ('WILD' in _p.upper() or '野问' in _p):
                _dst2 = '讨论室/mirror-vci/' + _p.replace('/', '__')
                if _tvi16.get(_p) != _tci16.get(_dst2):
                    _fc = gh_get('/repos/chepin-ai/vci-inbox/contents/' + urllib.parse.quote(_p), patA)
                    _txt = __import__('base64').b64decode(_fc['content']).decode('utf-8', 'ignore')
                    gh_put_file('chepin-ai/ci-inbox', _dst2, _txt, patA, 'SURFACE-MIRROR-01(vci→ci): ' + _p.split('/')[-1], 'chepin-ai')
                    _mig += 1
        _bi16 = ['# 公告板镜目(ci-inbox→vci域,树即账零内容取水) ' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()), '']
        for _p in sorted(p for p in _tci16 if p.startswith('公告板/')):
            _bi16.append('- ' + _p + ' @' + _tci16[_p][:12])
        _bis = '\n'.join(_bi16) + '\n'
        if hashlib.sha256(_bis.encode()).hexdigest()[:12] != (st.get('mirror') or {}).get('idx_h'):
            gh_put_file('chepin-ai/vci-inbox', 'mirror/ci/BOARD-INDEX.md', _bis, patA, 'SURFACE-MIRROR-01: BOARD-INDEX', 'chepin-ai')
            _idxh = hashlib.sha256(_bis.encode()).hexdigest()[:12]
        else:
            _idxh = (st.get('mirror') or {}).get('idx_h')
        st['mirror'] = {'ts': time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()), 'migrated': _mig, 'idx_h': _idxh}
    except Exception as e:
        st['mirror'] = {'err': str(e)[:150]}
    # TOWER-FIX-08-qfa(beat-76 root 令「所有候直通」;采 cisvr SI3-LOOP-01 v1.5 CAS三段式互领养):落账前向 origin 取态→字段级并(quests/quafu hit胜open、si1计数max、idem/seen union、resp.n max)→写——哑跑亚型②跃检残(overlay回退/计数回退,残病活证×2在案)根治:并发拍覆写无损,并集/max交换律保证双收敛
    try:
        subprocess.run('git fetch origin main -q', shell=True, cwd=ROOT, timeout=60, capture_output=True)
        _rm8 = subprocess.run('git show origin/main:ci/watchtower_state.json', shell=True, cwd=ROOT, timeout=30, capture_output=True, text=True)
        if _rm8.returncode == 0 and _rm8.stdout.strip():
            _rs8 = json.loads(_rm8.stdout)
            for _dk8 in ('quests', 'quafu'):
                _a8, _b8 = _rs8.get(_dk8) or {}, st.get(_dk8) or {}
                _mg8 = dict(_a8)
                for _k8, _v8 in _b8.items():
                    _o8 = _mg8.get(_k8)
                    if _o8 is None or (str(_o8) == 'open' and str(_v8) != 'open') or (str(_o8) == '0' and str(_v8) != '0'):
                        _mg8[_k8] = _v8
                st[_dk8] = _mg8
            _a8, _b8 = _rs8.get('si1') or {}, st.get('si1') or {}
            st['si1'] = {**_a8, **_b8, 'seq': max(_a8.get('seq', 0), _b8.get('seq', 0)), 'n': max(_a8.get('n', 0), _b8.get('n', 0)), 'voice_n': max(_a8.get('voice_n', 0), _b8.get('voice_n', 0))}
            for _lk8 in ('idem', 'vciqfa_sealed_seen'):
                st[_lk8] = list(dict.fromkeys(list(_rs8.get(_lk8) or []) + list(st.get(_lk8) or [])))[-300:]
            _ra8, _rb8 = _rs8.get('resp') or {}, st.get('resp') or {}
            if _ra8.get('day') == _rb8.get('day'):
                st['resp'] = {**_ra8, **_rb8, 'n': max(_ra8.get('n', 0), _rb8.get('n', 0))}
            _ua8, _ub8 = _rs8.get('ucif2_watch') or {}, st.get('ucif2_watch') or {}
            _um8 = dict(_ua8)
            for _k8, _v8 in _ub8.items():
                if _um8.get(_k8) != 'mention-qfa':
                    _um8[_k8] = _v8
            st['ucif2_watch'] = _um8  # FIX-10并账:union+mention-qfa粘滞
            st['lane_inbox_count'] = max(_rs8.get('lane_inbox_count') or 0, st.get('lane_inbox_count') or 0)
    except Exception as _e8:
        st['fix08_err'] = str(_e8)[:120]
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
