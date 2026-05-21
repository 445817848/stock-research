# Output Example

```json
{
  "code": "sh688182",
  "name": "灿勤科技",
  "summary": "高端先进电子陶瓷元器件研发生产销售+主要产品核心技术自主可控+产品应用于通信基站+星网计划+商业航天+智能电网+2025年营收7.24亿元同比增长76.14%+净利润1.20亿元同比增长107.84%+2026年一季报营收同比增98%接近翻倍+5月19日涨停+银河航天大口径可展开伞天线下线催化商业航天概念",
  "concepts": [
    "电子陶瓷元器件",
    "HTCC陶瓷封装",
    "光模块",
    "星网计划",
    "商业航天",
    "智能电网",
    "毫米波雷达天线"
  ],
  "content": "【业务】高端先进电子陶瓷元器件研发生产销售+产品应用于通信基站+星网计划+商业航天+智能电网+半导体散热基板+3C终端壳体边框+新能源汽车轻量化制动系统+毫米波雷达天线小批量生产阶段领先国内同行+核心技术自主可控\n【近期事件】\n2026-05-19 20%涨停+收盘价43.84元创历史新高+3分钟封涨停+龙虎榜营业部净买入4530.30万元+银河航天自主研制大口径可展开伞天线近日下线催化商业航天概念\n2026-04-30 披露2026年一季报+营收同比增98%接近翻倍+扣非净利润同比增4.3%+存货增63%+合同负债增2.66倍\n2026-04-21 2025年年报正式披露+营收7.24亿元同比增76.14%+净利润1.20亿元同比增107.84%",
  "research_date": "2026-05-19",
  "_raw": {
    "websearch": "(full WebSearch output text here)",
    "eastmoney": "(full East Money NewsBulletin extracted text here)"
  }
}
```

## Rules Applied

- `summary` is exactly one sentence with `+` separators.
- No price/valuation data in `summary`.
- `concepts` are extracted directly from news.
- `content` starts with `【业务】` followed by `【近期事件】` in reverse chronological order.
- `_raw.websearch` contains the complete WebSearch output.
- `_raw.eastmoney` contains the complete FetchURL extracted text.
- No guiding language, no subjective adjectives.
