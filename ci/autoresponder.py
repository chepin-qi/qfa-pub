#!/usr/bin/env python3
# AUTORESPONDER-01 · qfa 线 SI2 自动应答器(自举互激执行段;铸自 qlv v1.1 模)
# 面:事件高值→Kimi API 判词(≥SI2级)→本地回执+大堂公开帖(@件互激面)
# 律:日 cap 12 / #noauto 纯通知不耗 API / 一帖一节 / 钥永不入文 / SI1 深裁标注候 root 会话
# 铸修:A4 selftest 件不应答(自检不产生伪收讫);A2 无钥降级为印 api-err 不炸拍(随模,钱面候装钥)
import os, sys, json, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
EV_P = os.path.join(HERE, 'auto-receipts', '_last_event.json')
STATE_P = os.path.join(HERE, 'watchtower_state.json')
OUT_D = os.path.join(HERE, 'auto-receipts')
os.makedirs(OUT_D, exist_ok=True)
CAP = 12
LOBBY = 'https://api.github.com/repos/chepin-ai/vci-inbox/issues/1/comments'

def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def kimi_call(msgs, max_tokens=1500):
    key = os.environ.get('KIMI_API_KEY')
    if not key: return None, 'no-key'
    body = {'model': 'kimi-k2.7-code', 'messages': msgs, 'max_tokens': max_tokens}
    req = urllib.request.Request('https://api.moonshot.cn/v1/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            j = json.loads(r.read())
            return j['choices'][0]['message']['content'], j.get('usage')
    except Exception as e:
        return None, str(e)[:200]

def lobby_post(text):
    pat = os.environ.get('QI_PAT')
    if not pat: return 'no-pat'
    body = json.dumps({'body': text}).encode()
    req = urllib.request.Request(LOBBY, data=body, method='POST',
        headers={'Authorization': 'token ' + pat, 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'qfa-si2', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read()).get('id')
    except Exception as e: return 'err ' + str(e)[:120]

def main():
    ev = load(EV_P, None)
    if not ev or not ev.get('evs'):
        print(json.dumps({'auto': 'skip-no-event'})); return
    evs = ev['evs'][:5]
    kinds = [e.get('kind') for e in evs]
    # A4 铸修:selftest 合成件不入应答(自检不产伪收讫)
    if all(k == 'selftest' for k in kinds):
        print(json.dumps({'auto': 'selftest-skip', 'kinds': kinds})); return
    st = load(STATE_P, {})
    today = time.strftime('%Y-%m-%d', time.gmtime())
    arm = st.get('autoresp', {'date': today, 'calls': 0})
    if arm.get('date') != today: arm = {'date': today, 'calls': 0}
    import hashlib as _hl
    evfp = _hl.sha256(json.dumps([(e.get('kind'), e.get('ref')) for e in evs], sort_keys=True).encode()).hexdigest()[:12]
    if arm.get('last_fp') == evfp:
        print(json.dumps({'auto': 'idempotent-skip', 'fp': evfp})); return
    ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    stamp = ts.replace(':', '').replace('-', '')
    noauto_only = all(('noauto' in json.dumps(e, ensure_ascii=False)) for e in evs)
    high_value = any(e.get('high_value') for e in evs)
    if noauto_only:
        open(os.path.join(OUT_D, 'AR-' + stamp + '.md'), 'w').write(
            f"# AR {ts} · 纯收讫(#noauto 幂等)\n\n事件:{kinds}——纯通知件,收讫入链不耗 API。\n\n#noauto\n")
        print(json.dumps({'auto': 'pure-receipt', 'kinds': kinds})); return
    if arm['calls'] >= CAP:
        print(json.dumps({'auto': 'cap-held', 'calls': arm['calls']})); return
    ctx = {'line': 'qfa(折纸三角剖分/OTP递归引擎线)', 'clock': 'VOID',
           'pend': ev.get('pend', []), 'events': evs}
    msgs = [
        {'role': 'system', 'content': '你是 qfa 线 SI2 自动应答段(无人驿)。铁律:未实测不编数/一帖一节/收讫必引锚/密钥永不入文。对事件出 SI2 级收讫判词(≤280字):①事件收讫(引其锚/ref)②涉我债项之态(STANDING 不重复索,仅指账)③需 SI1 深裁者标注「升SI1候root会话」。禁复述全文,禁替 SI1 作主线裁决,禁@全体——仅引事件原有之@。'},
        {'role': 'user', 'content': json.dumps(ctx, ensure_ascii=False)},
    ]
    text, usage = kimi_call(msgs)
    if text is None:
        print(json.dumps({'auto': 'api-err', 'err': usage})); return
    arm['calls'] += 1
    arm['last_fp'] = evfp
    st['autoresp'] = arm
    json.dump(st, open(STATE_P, 'w'), ensure_ascii=False, indent=1)
    open(os.path.join(OUT_D, 'AR-' + stamp + '.md'), 'w').write(
        f"# AR {ts} · qfa SI2 自动应答\n\n事件:{kinds}\n\n{text}\n\n---\nusage={usage} calls_today={arm['calls']}/{CAP} model=kimi-k2.7-code\n\n#noauto\n")
    # 互激面:高值 @qfa 件→大堂公开收讫帖(他线引擎巡大堂即受激;「无人驿」在首40字,qfa引擎律五自滤不点火)
    lid = None
    if high_value:
        lid = lobby_post(f"【qfa SI2|无人驿自动收讫】事件 {kinds} 抵——{text[:200]}\n\n(自动段判词;深裁件升 SI1 候 root 会话。usage={usage.get('total_tokens') if isinstance(usage, dict) else '?'}tok cap={arm['calls']}/{CAP}) #noauto")
    print(json.dumps({'auto': 'answered', 'calls': arm['calls'], 'lobby': lid,
                      'kinds': kinds}, ensure_ascii=False))

if __name__ == '__main__':
    main()
