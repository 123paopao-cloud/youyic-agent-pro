# 优益C 热点策略智能体（自建多 Agent 版）

> 面向蒙牛优益C **企业内部营销/运营人员**的 AI 智能体：自动追踪实时热点，结合品牌调性与安全合规审查，
> 一键产出多平台营销策略方案并预判效果。参加「蒙牛优益C杯」全域 AI 应用创新赛道。

## 它解决什么问题
营销/运营同学日常要自己刷热点、查数据、写文案、判断能不能蹭、评估效果，流程繁琐且容易"翻车"。
本智能体用一条流水线自动完成：**热点发现 → 品牌匹配 → 安全合规 → 竞品监测 → 策略生成 → 效果预判**。

## 技术架构
```
浏览器（评委免注册打开链接）
        ↓
 Streamlit 聊天界面 ──(可选)── FastAPI 标准后端
        ↓
 LangGraph 状态图（6 个专业 Agent + 合规门禁）
   ①热点发现  ②品牌匹配  ③安全合规 ──红灯拦截 / 黄绿灯放行
   ④竞品监测  ⑤策略生成  ⑥效果预判 → 组装《热点策略报告》
        ↓
 智谱大模型（GLM 系列，OpenAI 兼容） + 博查搜索 + 4 个知识库（BM25）
```
- 编排：LangGraph（图结构 + 条件边做红黄绿门禁）
- 后端：FastAPI（封装接口、保护密钥）
- 前端：Streamlit（免注册聊天网页）
- 大模型：智谱 GLM（`glm-4-flashx` 低价稳定，亦可换 `glm-4.7-flash` 等免费模型）
- 搜索：博查 Bocha（免费资源包，国内网络稳定）

---

## 快速开始（3 步）

### 第 1 步：获取智谱 API Key（约 3 分钟）
1. 打开智谱开放平台：https://open.bigmodel.cn → 手机号注册/登录
2. 右上角头像 →「API 密钥」→「创建新的 API Key」→ 复制（形如 `xxx.xxx`）
3. 推荐模型 `glm-4-flashx`（约 0.1 元/百万 token，一次完整方案约 1-2 分钱，几乎可忽略）；
   也可用 `glm-4.7-flash`（完全免费，但高峰期限流可能更频繁）。

### 第 2 步：获取博查搜索 Key（约 2 分钟）
1. 打开 https://open.bochaai.com → 手机号注册/登录
2. **先到「资源包管理」订阅「免费试用」资源包**（不订阅没有免费额度）
3. 「API Key 管理」→ 创建 API Key → 复制

### 第 3 步：填配置并运行
```bash
cp .env.example .env        # 首次
# 编辑 .env，填入 LLM_API_KEY（智谱）和 BOCHA_API_KEY（博查）

pip install -r requirements.txt

bash run.sh                 # 完整前后端一起启动
# 或只启动前端（直连模式，部署到云端用这个）：
bash start_ui.sh
```
打开浏览器访问 Streamlit 提示的本地地址（默认 http://localhost:8501）即可对话。

---

## 部署成评委可访问的在线链接

### 方案一：Streamlit Community Cloud（免费，GitHub 一键部署，推荐）
1. 把本项目推送到你的 GitHub 公开仓库（注意 `.env` 已被 `.gitignore` 忽略，不会上传）。
2. 打开 https://share.streamlit.io → 用 GitHub 登录（未注册先注册，免费）。
3. New app → 选仓库、主文件填 `streamlit_app.py`、Python 版本选 3.11/3.12 → Deploy。
4. 部署完成后，在应用的「Settings → Secrets」里填入（云端环境变量，等同 .env）：
   ```
   LLM_API_KEY = "你的智谱key"
   LLM_MODEL = "glm-4-flashx"
   LLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
   BOCHA_API_KEY = "你的博查key"
   DAILY_TRIAL_LIMIT = "8"
   USE_ARK_WEBSEARCH = "0"
   ```
5. 部署后得到 `https://xxx.streamlit.app` 链接，评委打开即用、**无需注册、不消耗你的账号额度**（模型按量计价极低，博查在免费资源包内）。

> 注意：Streamlit 官方云服务器在境外，国内评委打开可能稍慢；正式比赛前建议实测一次。

### 方案二：Hugging Face Spaces（免费）
新建 Space，SDK 选 Streamlit，上传本项目文件，在 Space 的 Settings → Secrets 里同样填入上述 Key。

### 方案三：国内平台（访问快，备选）
腾讯云开发 CloudBase / 阿里云函数计算（有免费额度），或学生价云服务器（国内访问最快）。

### 决赛现场保底
在自己电脑本地运行 + 投屏演示，不依赖外部网络，零风险。

---

## 项目结构
```
youyic-agent-pro/
├── app/
│   ├── config.py              # 配置与密钥（智谱优先，方舟兼容）
│   ├── llm.py                 # 大模型（OpenAI 兼容接口）
│   ├── main.py                # FastAPI 入口
│   ├── schemas.py
│   ├── agents/
│   │   ├── graph.py           # LangGraph 主图 + 门禁
│   │   ├── state.py           # 状态定义
│   │   └── nodes/             # 6 个节点 + 报告组装
│   ├── tools/search.py        # 可插拔搜索（博查/Tavily/DDG/方舟）
│   ├── knowledge/retriever.py # BM25 / 向量检索
│   └── data/                  # 4 个知识库内容
│       ├── brand_assets/      # 品牌资产库
│       ├── brand_keywords/    # 品牌关键词库
│       ├── compliance_rules/  # 合规红线库
│       └── hit_cases/         # 历史爆款案例库
├── streamlit_app.py           # Streamlit 前端
├── run.sh / start_ui.sh       # 启动脚本
└── requirements.txt
```

## 合规说明
内容生成严格遵守《广告法》《食品安全法》：不使用极限词，普通食品不宣称疾病/保健/治疗功效，
卖点以第一人称体验口吻表达；安全合规官对灾难营销、低俗擦边、群体冒犯、IP 侵权等做强制门禁。
