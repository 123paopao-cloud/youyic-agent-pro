import sys, time
sys.path.insert(0, '/home/user/Doubao/chats/38444935270158338/youyic-agent-pro')

def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

log('开始诊断')

# 1. 直接调用方舟 responses API（不走 search_web 包装）
log('步骤1: 直接调 OpenAI responses.create')
from openai import OpenAI
from app.config import get_settings
s = get_settings()
log(f'模型: {s.ark_model}')
client = OpenAI(api_key=s.ark_api_key, base_url=s.ark_base_url, timeout=20.0)
t0 = time.time()
try:
    resp = client.responses.create(
        model=s.ark_model,
        input=[{'role': 'user', 'content': '请联网搜索"国庆 年轻人 热点"并列出3条结果'}],
        tools=[{'type': 'web_search', 'max_keyword': 2}],
        timeout=20.0,
    )
    log(f'成功，耗时 {time.time()-t0:.1f}s')
    texts = [c.text for item in resp.output for c in getattr(item, 'content', []) if getattr(c, 'text', '')]
    log(f'输出片段数: {len(texts)}, 首段长度: {len(texts[0]) if texts else 0}')
except Exception as e:
    log(f'失败，耗时 {time.time()-t0:.1f}s: {type(e).__name__}: {str(e)[:300]}')

# 2. 通过 search_web 调用
log('步骤2: 走 search_web')
from app.tools.search import search_web
t0 = time.time()
try:
    items, backend = search_web('国庆 年轻人 热点', max_results=5)
    log(f'成功，耗时 {time.time()-t0:.1f}s, backend={backend}, 结果={len(items)}')
except Exception as e:
    log(f'失败，耗时 {time.time()-t0:.1f}s: {type(e).__name__}: {str(e)[:300]}')

log('诊断结束')
