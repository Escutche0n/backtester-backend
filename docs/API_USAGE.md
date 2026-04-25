# backtester-backend API 使用说明

本文档对应当前项目里正在运行的 FastAPI 服务。

默认本地地址：

- 服务根地址：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`
- OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`

当前 API 前缀默认是 `/api`。

## 1. 启动方式

### 1.1 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

如果你要跑本地验证或测试：

```bash
pip install -e ".[dev]"
```

### 1.2 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 1.3 环境变量

服务通过 `.env` 读取配置，核心字段如下：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_NAME` | `backtester-backend` | 服务名 |
| `APP_ENV` | `development` | 环境标记 |
| `APP_HOST` | `0.0.0.0` | 监听地址 |
| `APP_PORT` | `8000` | 监听端口 |
| `API_PREFIX` | `/api` | API 路径前缀 |
| `DEFAULT_DATA_SOURCE` | `mock` | 当前默认数据源标记 |

注意：代码里的基金数据实际来自东方财富接口，返回里的 `source` 目前也是 `eastmoney`。

## 2. 接口总览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/` | 根信息 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/fund/search` | 搜索基金 |
| `GET` | `/api/fund/realtime` | 查询基金实时/最近净值 |
| `GET` | `/api/fund/history` | 查询基金历史净值 |
| `POST` | `/api/portfolio/realtime` | 查询组合实时估算盈亏 |
| `POST` | `/api/portfolio/history` | 查询组合历史净值，当前还是 mock |

## 3. 通用说明

### 3.1 Content-Type

- `GET` 接口直接走 query string
- `POST` 接口请求头使用 `Content-Type: application/json`

### 3.2 日期格式

所有日期参数都要求 `YYYY-MM-DD`。

如果格式错误，会返回：

```json
{
  "detail": "invalid date: 2026/04/23"
}
```

### 3.3 常见错误

这套 API 直接抛 FastAPI `HTTPException`，常见状态码：

- `400`：请求参数格式不合法，比如日期格式错误
- `404`：基金没找到，或者查不到历史净值
- `422`：请求体/查询参数校验失败
- `502`：上游东方财富接口异常或不可达

## 4. 根接口

### 4.1 `GET /`

返回服务基础信息。

示例：

```bash
curl --noproxy '*' "http://127.0.0.1:8000/"
```

返回示例：

```json
{
  "name": "backtester-backend",
  "env": "development",
  "docs": "/docs"
}
```

## 5. 健康检查

### 5.1 `GET /health`

用于确认服务进程是否正常启动。

示例：

```bash
curl --noproxy '*' "http://127.0.0.1:8000/health"
```

返回示例：

```json
{
  "status": "ok",
  "service": "backtester-backend",
  "env": "development"
}
```

## 6. 基金接口

### 6.1 `GET /api/fund/search`

按基金代码或关键词搜索基金。

请求参数：

| 参数 | 必填 | 类型 | 说明 |
| --- | --- | --- | --- |
| `keyword` | 是 | `string` | 基金代码或关键词，最少 1 个字符 |

示例：

```bash
curl --noproxy '*' "http://127.0.0.1:8000/api/fund/search?keyword=白酒"
```

返回示例：

```json
{
  "keyword": "白酒",
  "source": "eastmoney",
  "items": [
    {
      "code": "161725",
      "name": "招商中证白酒指数(LOF)A",
      "fund_type": "指数型-股票",
      "currency": "CNY"
    }
  ]
}
```

字段说明：

- `keyword`：原始搜索词
- `source`：数据源标记
- `items[].code`：基金代码
- `items[].name`：基金名称
- `items[].fund_type`：基金类型
- `items[].currency`：当前固定返回 `CNY`

### 6.2 `GET /api/fund/realtime`

查询单只基金的实时估算净值；如果上游实时估值不可用，会回退到最近确认净值。

请求参数：

| 参数 | 必填 | 类型 | 说明 |
| --- | --- | --- | --- |
| `code` | 是 | `string` | 基金代码 |

示例：

```bash
curl --noproxy '*' "http://127.0.0.1:8000/api/fund/realtime?code=006195"
```

返回示例：

```json
{
  "data": {
    "code": "006195",
    "name": "国金量化多因子股票A",
    "fund_type": "股票型",
    "nav": 3.5202,
    "nav_date": "2026-04-22 15:00",
    "change_percent": 1.32,
    "value_kind": "estimated",
    "source": "eastmoney"
  }
}
```

字段说明：

- `nav`：当前使用的净值
- `nav_date`：净值对应时间
- `change_percent`：估值涨跌幅，仅 `estimated` 时通常有值
- `value_kind`：值来源
- `source`：数据源标记

`value_kind` 取值说明：

- `estimated`：盘中估算净值
- `unit_nav`：没有实时估值时，回退到最近确认单位净值

### 6.3 `GET /api/fund/history`

查询单只基金历史净值。

请求参数：

| 参数 | 必填 | 类型 | 说明 |
| --- | --- | --- | --- |
| `code` | 是 | `string` | 基金代码 |
| `start_date` | 否 | `string` | 开始日期，格式 `YYYY-MM-DD` |
| `end_date` | 否 | `string` | 结束日期，格式 `YYYY-MM-DD` |

默认行为：

- `start_date` 不传时，内部默认从 `2000-01-01` 开始查
- `end_date` 不传时，内部默认查到当天

示例：

```bash
curl --noproxy '*' "http://127.0.0.1:8000/api/fund/history?code=161725&start_date=2024-01-01&end_date=2024-01-05"
```

返回示例：

```json
{
  "fund_code": "161725",
  "fund_name": "招商中证白酒指数(LOF)A",
  "fund_type": "指数型-股票",
  "source": "eastmoney",
  "start_date": "2024-01-01",
  "end_date": "2024-01-05",
  "points": [
    {
      "date": "2024-01-02",
      "unit_nav": 0.9201,
      "accumulated_nav": 2.6362
    },
    {
      "date": "2024-01-03",
      "unit_nav": 0.9159,
      "accumulated_nav": 2.632
    }
  ]
}
```

字段说明：

- `fund_code`：基金代码
- `fund_name`：基金名称
- `fund_type`：基金类型
- `source`：数据源标记
- `points[].date`：净值日期
- `points[].unit_nav`：单位净值
- `points[].accumulated_nav`：累计净值

## 7. 组合接口

### 7.1 `POST /api/portfolio/realtime`

按持仓份额估算组合当前盈亏。

请求体：

```json
{
  "holdings": [
    {
      "fund_code": "006195",
      "shares": 1000
    },
    {
      "fund_code": "008163",
      "shares": 2000
    }
  ]
}
```

请求字段：

| 字段 | 必填 | 类型 | 说明 |
| --- | --- | --- | --- |
| `holdings` | 是 | `array` | 持仓列表，至少 1 项 |
| `holdings[].fund_code` | 是 | `string` | 基金代码 |
| `holdings[].shares` | 是 | `number` | 持有份额，必须大于 0 |

示例：

```bash
curl --noproxy '*' \
  -X POST "http://127.0.0.1:8000/api/portfolio/realtime" \
  -H "Content-Type: application/json" \
  -d '{
    "holdings": [
      {"fund_code": "006195", "shares": 1000},
      {"fund_code": "008163", "shares": 2000}
    ]
  }'
```

返回示例：

```json
{
  "summary": {
    "base_value": 5645.6,
    "estimated_value": 5662.0,
    "estimated_profit": 16.4,
    "estimated_return": 0.002905
  },
  "items": [
    {
      "fund_code": "006195",
      "fund_name": "国金量化多因子股票A",
      "fund_type": "股票型",
      "shares": 1000.0,
      "base_date": "2026-04-22",
      "base_nav": 3.5038,
      "estimated_time": "2026-04-22 15:00",
      "estimated_nav": 3.5202,
      "value_kind": "estimated",
      "base_value": 3503.8,
      "estimated_value": 3520.2,
      "estimated_profit": 16.4,
      "estimated_return": 0.004681
    }
  ],
  "disclaimer": "估算结果仅供个人记录，不代表确认净值或投资建议。"
}
```

计算规则：

- `base_value = shares * latest confirmed unit nav`
- `estimated_value = shares * realtime nav`
- `estimated_profit = estimated_value - base_value`
- `estimated_return = estimated_profit / base_value`

字段说明：

- `summary`：组合汇总
- `items`：每只基金的估算结果
- `base_date`：基准净值日期
- `base_nav`：最近确认单位净值
- `estimated_time`：估算净值时间
- `estimated_nav`：估算净值
- `value_kind`：`estimated` 或 `unit_nav`

### 7.2 `POST /api/portfolio/history`

查询组合历史净值序列。

注意：这个接口当前还是 mock 实现，没有真的按基金历史净值聚合计算。

请求体：

```json
{
  "holdings": [
    {
      "fund_code": "161725",
      "weight": 0.6
    },
    {
      "fund_code": "005827",
      "weight": 0.4
    }
  ],
  "start_date": "2026-04-18",
  "end_date": "2026-04-22",
  "rebalance": "none"
}
```

请求字段：

| 字段 | 必填 | 类型 | 说明 |
| --- | --- | --- | --- |
| `holdings` | 是 | `array` | 持仓列表，至少 1 项 |
| `holdings[].fund_code` | 是 | `string` | 基金代码 |
| `holdings[].weight` | 是 | `number` | 权重，大于 0 且小于等于 1 |
| `start_date` | 否 | `string` | 开始日期，格式 `YYYY-MM-DD` |
| `end_date` | 否 | `string` | 结束日期，格式 `YYYY-MM-DD` |
| `rebalance` | 否 | `string` | 再平衡策略，默认 `none` |

示例：

```bash
curl --noproxy '*' \
  -X POST "http://127.0.0.1:8000/api/portfolio/history" \
  -H "Content-Type: application/json" \
  -d '{
    "holdings": [
      {"fund_code": "161725", "weight": 0.6},
      {"fund_code": "005827", "weight": 0.4}
    ],
    "start_date": "2026-04-18",
    "end_date": "2026-04-22",
    "rebalance": "none"
  }'
```

返回示例：

```json
{
  "start_date": "2026-04-18",
  "end_date": "2026-04-22",
  "rebalance": "none",
  "points": [
    {
      "date": "2026-04-18",
      "portfolio_nav": 1.0,
      "daily_return": 0.0
    },
    {
      "date": "2026-04-19",
      "portfolio_nav": 1.004,
      "daily_return": 0.004
    }
  ],
  "warnings": [
    "mock implementation: portfolio history is not using real fund data yet"
  ]
}
```

字段说明：

- `points[].portfolio_nav`：组合净值
- `points[].daily_return`：组合单日涨跌幅
- `warnings`：当前实现告警

当前限制：

- 还没有真实对齐每只基金的历史净值时间序列
- 还没有做实际再平衡计算
- 返回的 `points` 目前是固定 mock 数据

## 8. 一组可直接跑的命令

```bash
curl --noproxy '*' "http://127.0.0.1:8000/"
curl --noproxy '*' "http://127.0.0.1:8000/health"
curl --noproxy '*' "http://127.0.0.1:8000/api/fund/search?keyword=白酒"
curl --noproxy '*' "http://127.0.0.1:8000/api/fund/realtime?code=006195"
curl --noproxy '*' "http://127.0.0.1:8000/api/fund/history?code=161725&start_date=2024-01-01&end_date=2024-01-05"
curl --noproxy '*' -X POST "http://127.0.0.1:8000/api/portfolio/realtime" -H "Content-Type: application/json" -d '{"holdings":[{"fund_code":"006195","shares":1000},{"fund_code":"008163","shares":2000}]}'
curl --noproxy '*' -X POST "http://127.0.0.1:8000/api/portfolio/history" -H "Content-Type: application/json" -d '{"holdings":[{"fund_code":"161725","weight":0.6},{"fund_code":"005827","weight":0.4}],"start_date":"2026-04-18","end_date":"2026-04-22","rebalance":"none"}'
```

## 9. 当前实现备注

- 基金搜索、基金实时、基金历史，当前都走东方财富上游
- 组合实时估算会逐个拉取基金实时净值和最近确认净值，再做汇总
- 组合历史还是占位实现，不能当成真实回测结果
- 最准确的实时字段含义，以 `/docs` 里的 Swagger schema 为准
