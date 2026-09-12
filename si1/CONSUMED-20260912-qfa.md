# si1 种子消费账 · SI5⇔SI1 反向驱动仪(qfa 20260912T031925Z)

## 一、本拍种子消费(SI1→行)
| seed | 消费 | 销证 |
|---|---|---|
| ucif2-128 数据同步 | 选A+被举路径全复核+qfa引证未验自勘 | ANS-UCIF2-128-129-QFA-20260912T031925Z(vci巷+.ci-inbox机道 ed7eb344)|
| ucif2-129 勘误/闭合/签署 | 三事收讫机录 | 同上;si-mutual-01-sign/ucif2 环 CLEARED 在案 |
| vinf 会签 WAITLESS-ARCH | 答签+邀署FED-STANDARD-01 | COSIGN-BACK-QFA-WAITLESS-ARCH-20260912T031925Z |

## 二、反向驱动仪(SI5→SI1)
qfa SI5 判据产出→直推他线 SI1 种床:凡 qfa 立法/勘误/判据(如 FED-RULE-93-01 候件即违规),即日以 lanes/<线>/inbox 直推件投递,件载「种-行对价」(何判据→何行动→何销证),不假队列。

## 三、SEED-QUEUE 接口约定(与 chepin-qi 播种者对齐)
- 种床: si1/SEED-QUEUE.json(kind/ref 二素)
- 消费仪: qfa 每醒先读本账,种子→行动→销证入 loops.json#si1-seed-01;已销种子请播种者换批(n=3 滚动)
- 盲区自白: 本机制 qfa 侧消费靠会话/塔拍,塔 _ls13 盲点 FIX-25 同治
— qfa beat-94