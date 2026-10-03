import time, sys
sys.path.insert(0, '/home/user/Doubao/chats/38444935270158338/youyic-agent-pro')

print('=== 逐节点诊断 ===')
state = {'user_request': '最近有什么热点？帮我出3条小红书营销方案', 'time_context': '国庆假期', 'steps': []}

from app.agents.nodes.hotspot import hotspot_node
t0 = time.time()
out = hotspot_node(state)
print(f'[热点发现] {time.time()-t0:.1f}s | backend={out.get("hotspot_backend")} | 摘要{len(out.get("hotspot_summary",""))}字')
state.update(out)

from app.agents.nodes.brand_match import brand_match_node
t0 = time.time()
out = brand_match_node(state)
print(f'[品牌匹配] {time.time()-t0:.1f}s | level={out.get("match_level")}')
state.update(out)

from app.agents.nodes.compliance import compliance_node
t0 = time.time()
out = compliance_node(state)
print(f'[安全合规] {time.time()-t0:.1f}s | level={out.get("compliance_level")}')
state.update(out)
print('=== 前3节点诊断完成 ===')
