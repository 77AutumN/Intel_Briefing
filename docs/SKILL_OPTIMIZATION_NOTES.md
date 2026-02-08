# 🔧 情报系统优化笔记

> 记录 AIA 情报系统运行中发现的问题和解决方案，用于持续优化 Skills 工作区的情报技能。

---

## 📅 2026-01-21: Product Hunt 抓取失败修复

### 问题描述
- **症状**: 周报中 Product Hunt 部分显示 "*未获取到数据*"
- **日志**: `⚠️ Could not find __NEXT_DATA__ on page.`

### 根因分析
- Product Hunt 启用了 **Cloudflare Turnstile** 人机验证
- httpx 请求被拦截，无法获取真实页面内容
- Next.js hydration 方式失效

### 解决方案

#### 方案 A: Grok Sensor 绕过 (临时)
- 实现 `_fetch_via_grok()` 函数
- 利用 Grok 的网络搜索能力间接获取数据
- **缺点**: 消耗 Grok API 额度

#### 方案 B: 官方 API Token (推荐) ✅
- 申请地址: https://api.producthunt.com/v2/oauth/applications
- 配置 `.env` 中的 `PRODUCTHUNT_TOKEN`
- **优点**: 免费、数据准确、不消耗 Grok 额度

### 代码修改
- **文件**: `src/sensors/product_hunt.py`
- **改动**: 
  1. 修复 `.env` 路径查找逻辑 (支持多级目录)
  2. 添加 `_fetch_via_grok()` 作为 fallback

### 经验总结
> 当网站启用反爬时，优先考虑官方 API，其次考虑 Grok Sensor 作为备选。

---

## 📋 待优化事项

### 高优先级
- [ ] 减少舆情核查的 Grok 调用次数
  - ✅ PH 产品列表：已改用官方 API，不消耗 Grok
  - ⚠️ PH 舆情核查：每个产品 1 次 Grok 调用 (10 次/报告)
  - ⚠️ 战略情报总结：1 次 Grok 调用
  - ⚠️ Alpha Radar：1-2 次 Grok 调用
  - **当前总计**: ~12 次 Grok 调用/报告
- [ ] 考虑将舆情核查改为可选功能 (减少 10 次调用)

### 中优先级
- [ ] V2EX 扫描器优化 (当前经常返回 0 结果)
- [ ] 小红书关键词扩展覆盖更多商机

### 低优先级
- [ ] 添加报告生成时间统计
- [ ] 实现增量报告 (只显示新内容)

---

## 🧰 Skill 优化清单

当优化情报 Skill 时，检查以下要点：

### 数据源健康
- [ ] API Token 是否有效？
- [ ] 网站结构是否变化？
- [ ] 是否有新的反爬措施？

### 性能优化
- [ ] API 调用是否可以合并？
- [ ] 是否有不必要的重复请求？
- [ ] 缓存策略是否合理？

### 输出质量
- [ ] 报告格式是否清晰？
- [ ] 信息是否有重复？
- [ ] 中文本地化是否完整？

---

## 📚 相关文件

| 文件 | 作用 |
|------|------|
| `run_mission.py` | 战略情报入口 |
| `run_bounty_hunter.py` | 战术情报入口 |
| `run_alpha_radar.py` | Web3 情报入口 |
| `src/sensors/product_hunt.py` | PH 数据获取 |
| `src/sensors/x_grok_sensor.py` | Grok 情报获取 |
| `.env` | API 密钥配置 |
