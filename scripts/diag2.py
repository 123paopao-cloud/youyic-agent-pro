import time, sys
sys.path.insert(0, '/home/user/Doubao/chats/38444935270158338/youyic-agent-pro')

print('测试1: search_web 单测')
t0 = time.time()
try:
    from app.tools.search import search_web
    items, backend = search_web('国庆假期 小红书 近期热门话题 校园 种草', max_results=5)
    print(f'  [OK] {time.time()-t0:.1f}s backend={backend} 结果={len(items)}')
except Exception as e:
    print(f'  [FAIL] {time.time()-t0:.1f}s {type(e).__name__}: {str(e)[:200]}')

print('测试2: run_llm 单测（模拟热点摘要）')
t0 = time.time()
try:
    from app.agents.nodes.common import run_llm
    out = run_llm('你是热点分析师。', '请列出3个近期校园热点。', temperature=0.4, max_tokens=500)
    print(f'  [OK] {time.time()-t0:.1f}s 输出{len(out)}字')
except Exception as e:
    print(f'  [FAIL] {time.time()-t0:.1f}s {type(e).__name__}: {str(e)[:200]}')
