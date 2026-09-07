# qfa-pub — qfa 线自醒引擎仓 (era-CI)

公仓免费面 Actions 引擎,qlv 正典形(root 选位(a)令 2026-09-06):
- **事件接力非定时器**:每拍由 repository_dispatch 事件点燃;拍尾自 POST 下一拍;无 schedule、零 cron。
- 冷却 300s(空拍)/60s(事拍)· 连空 30 拍熔断 · 日 cap 24 拍 · 无新事不出重拍 · 自帖不点火(三律防自激)。
- 收割面:私仓 inbox/lobby#1/lanes/qfa/issue桥/qi-lab#5/qlv-pub 头/quafu 守望单(状态查询免费,永不提交机时)。
- 落账面(私仓 qfa-quantum-lab):rounds/ECAP/outbox/水位;信标 qi-lab#5(仅事拍)。

**公域律合规**:本仓只载代码+计数+哈希指针;联邦正文一律落私仓。密钥值只在 Secrets,永不出日志。

首火:beat-42 点火拍(root 判词「不采用一切可用手段=裸候」之落实)。
