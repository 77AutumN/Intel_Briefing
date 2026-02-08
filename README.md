# Intel Briefing Engine

自动化情报采集引擎，聚合多源技术、金融、学术数据并生成中文晨报。

## 数据源

| 模块 | 数据源 |
|:--|:--|
| 技术趋势 | Hacker News, GitHub Trending |
| 资本动向 | 36Kr, WallStreetCN |
| 学术前沿 | ArXiv AI/ML |
| 产品精选 | Product Hunt |
| 深度洞察 | HN Top Blogs (全文分析) |

## 使用

```bash
# 安装依赖
pip install -r requirements.txt

# 生成每日晨报
python run_mission.py

# 输出: reports/daily_briefings/Morning_Report_YYYY-MM-DD.md
```

## 环境变量

参见 `.env.example`
