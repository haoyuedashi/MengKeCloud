BEGIN;

INSERT INTO users (id, name, phone, role, active, dept_name)
VALUES
  ('ST001', '王销售', '13800000001', 'sales', TRUE, '招商一部'),
  ('ST002', '李销售', '13800000002', 'sales', TRUE, '招商二部')
ON CONFLICT (id) DO UPDATE
SET
  name = EXCLUDED.name,
  phone = EXCLUDED.phone,
  role = EXCLUDED.role,
  active = EXCLUDED.active,
  dept_name = EXCLUDED.dept_name,
  updated_at = NOW();

INSERT INTO dict_items (dict_type, item_key, item_label, sort_order, enabled)
VALUES
  ('lead_status', 'pending', '待跟进', 1, TRUE),
  ('lead_status', 'communicating', '初步沟通', 2, TRUE),
  ('lead_status', 'invited', '已邀约', 3, TRUE),
  ('lead_status', 'signed', '已签约', 4, TRUE),
  ('lead_source', 'douyin', '抖音广告', 1, TRUE),
  ('lead_source', 'baidu', '百度搜索', 2, TRUE),
  ('lead_source', 'expo', '线下展会', 3, TRUE),
  ('lead_source', 'referral', '转介绍', 4, TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO leads (
  id, name, phone, project, source, status, level, owner_id, last_follow_up, tags, dynamic_data
)
VALUES
  (
    'LD202602210001',
    '陈先生',
    '138****1234',
    '某某奶茶加盟',
    'douyin',
    'pending',
    'A级 (高意向)',
    'ST001',
    NOW() - INTERVAL '2 hour',
    '["多次访问", "预算充足"]'::jsonb,
    '{"invest_budget":"50-100万","has_store":true}'::jsonb
  ),
  (
    'LD202602210002',
    '李女士',
    '139****5678',
    '火锅店加盟',
    'baidu',
    'communicating',
    'B级 (中意向)',
    'ST001',
    NOW() - INTERVAL '1 day',
    '["关注选址"]'::jsonb,
    '{"invest_budget":"30-50万","has_store":false}'::jsonb
  ),
  (
    'LD202602210003',
    '张老板',
    '137****8888',
    '烘焙品牌加盟',
    'expo',
    'invited',
    'A级 (高意向)',
    'ST002',
    NOW() - INTERVAL '3 day',
    '["已加微信", "需家人决策"]'::jsonb,
    '{"invest_budget":"80-120万","has_store":true}'::jsonb
  ),
  (
    'LD202602210004',
    '赵女士',
    '136****3333',
    '轻食品牌加盟',
    'referral',
    'pending',
    'C级 (低意向)',
    NULL,
    NULL,
    '["公海线索"]'::jsonb,
    '{"drop_reason_type":"超时未跟进","drop_reason_detail":"分配后未跟进","original_owner":"王销售"}'::jsonb
  ),
  (
    'LD202602210005',
    '周先生',
    '135****9999',
    '咖啡店加盟',
    'douyin',
    'signed',
    'A级 (高意向)',
    'ST002',
    NOW() - INTERVAL '5 day',
    '["已签约"]'::jsonb,
    '{"invest_budget":"100万+","has_store":true}'::jsonb
  )
ON CONFLICT (id) DO UPDATE
SET
  name = EXCLUDED.name,
  phone = EXCLUDED.phone,
  project = EXCLUDED.project,
  source = EXCLUDED.source,
  status = EXCLUDED.status,
  level = EXCLUDED.level,
  owner_id = EXCLUDED.owner_id,
  last_follow_up = EXCLUDED.last_follow_up,
  tags = EXCLUDED.tags,
  dynamic_data = EXCLUDED.dynamic_data,
  updated_at = NOW();

INSERT INTO follow_up_records (lead_id, type, content, operator, timestamp, audio_url, ai_analysis)
VALUES
  (
    'LD202602210001',
    'call',
    '客户对选址有顾虑，已发送选址指南。',
    '王销售',
    NOW() - INTERVAL '2 hour',
    NULL,
    '{"intent":"正向","objection":"资金不够"}'::jsonb
  ),
  (
    'LD202602210003',
    'ai_summary',
    '客户倾向在商圈开店，建议提供商圈测算模板。',
    'AI助手',
    NOW() - INTERVAL '1 day',
    NULL,
    '{"intent":"高意向","objection":"回本周期"}'::jsonb
  )
ON CONFLICT DO NOTHING;

COMMIT;
