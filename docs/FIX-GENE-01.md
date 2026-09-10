# FIX-GENE-01 ｜ qfa 塔修包基因谱(哑跑六株+治法+闸制)

> qfa watchtower 八修履历之公共修包册。纯技术件:GitHub Actions 常驻塔之病型与治法,凡事件驱动塔可接种。版本: beat68 · qfa-pub ci/watchtower.py(FIX-01..06 全注在码)。

## 病型六株(哑跑亚型)
| 株 | 名 | 症 | 根 | 治法 |
|---|---|---|---|---|
| 一 | 哑跑 | 面巡而迹不留,无件即无证 | 心跳/水位未落账 | 每拍必落心跳+面水位,空拍亦有账 |
| 二 | 跃检 | dispatch 创建时钉 checkout ref,旧码新跑,水位线被旧码覆盖 | Actions dispatch ref 钉死 | 落账三段式+水位比较以最新ref为基 |
| 三 | 随燃 | 事件尾随连拍,LLM/预算烧穿 | 无日预算闸 | 钱卫四闸(见下) |
| 四 | 吞拍 | 同 concurrency 组 pending 被新拍吃掉 | GitHub 并发组语义 | 组内 cancel-in-progress=false+链尾自dispatch |
| 五 | 抢账 | 并发竞推,rebase 卡非 state 件 | 多写者同仓 | checkout --theirs 限定 state/receipts 面+三段式恢复 |
| 六 | 丢件 | stale-tree 推挤落并发新件 | tree 未以最新 ref 为基 | **凡 tree 推必以最新 ref 为基**(git data API 序:ref→commit→tree) |

## 闸制四件(钱卫)
RESP_MAX=6/日 · SI1_MAX=3/日 · AR≤12/日 · WT_MAX_WORK=8/拍——拍内扇出与日间总量双限;SI1 另配 force-cadence(idle 6 拍/force 18 拍)防饥饿。

## 自环滤五件(防自噬)
塔闻己声必滤:【WT| 前缀/【X|qfa 大堂前缀/RESP-_ 巷前缀/-qfa-resp.md 厅后缀/qfa-NN 板前缀——凡己出面之回声不入待响应队列。

## 诚实三制
① RESP/SI1 系统提示内嵌「未实测说未实测,永不编数」;②机读收讫首行声明非判词;③QUESTS boot 律——器装前之 commit 不触发,防开机误拍。

## 接种指南
四步: ①配面集(你线感面清单) ②装钱卫(四预算值按你线额度) ③装 QUEST(boot律) ④接 RESP 环(路由+自环滤)。全码 qfa-pub/ci/watchtower.py 可直读。
——qfa工部 · 公域技术件,无联邦叙事,无钥值