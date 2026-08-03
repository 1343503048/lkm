#!/bin/bash
KB_ID=$(grep 'kb_id' sched/.config | sed 's/.*= //')
IMA_VER=1.1.8
IMA_DIR=/home/zq/.qoder/skills/腾讯ima
PREFLIGHT=$IMA_DIR/knowledge-base/scripts/preflight-check.cjs
COS_UPLOAD=$IMA_DIR/knowledge-base/scripts/cos-upload.cjs
API=$IMA_DIR/ima_api.cjs
OK=0; FAIL=0
for f in sched/2026/08/sched-20260801-{002,003,004,005,006,007,008,009,010}-*.md; do
  echo "=== $(basename $f) ==="
  PF=$(node $PREFLIGHT --file "$f" 2>/dev/null | tail -1)
  FNAME=$(echo "$PF" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['file_name'])")
  FSIZE=$(echo "$PF" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['file_size'])")
  CT=$(echo "$PF" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['content_type'])")
  FEXT=$(echo "$PF" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['file_ext'])")
  CM=$(IMA_SKILL_VERSION=$IMA_VER node $API "openapi/wiki/v1/create_media" "{\"file_name\":\"$FNAME\",\"file_size\":$FSIZE,\"content_type\":\"$CT\",\"knowledge_base_id\":\"$KB_ID\",\"file_ext\":\"$FEXT\"}" 2>/dev/null | tail -1)
  MEDIA_ID=$(echo "$CM" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['data']['media_id'])" 2>/dev/null)
  if [ -z "$MEDIA_ID" ]; then echo "FAIL: create_media"; FAIL=$((FAIL+1)); continue; fi
  SEC=$(echo "$CM" | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['data']['cos_credential'];print(c['secret_id'])")
  SEK=$(echo "$CM" | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['data']['cos_credential'];print(c['secret_key'])")
  TOK=$(echo "$CM" | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['data']['cos_credential'];print(c['token'])")
  BKT=$(echo "$CM" | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['data']['cos_credential'];print(c['bucket_name'])")
  REG=$(echo "$CM" | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['data']['cos_credential'];print(c['region'])")
  CK=$(echo "$CM" | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['data']['cos_credential'];print(c['cos_key'])")
  ST=$(echo "$CM" | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['data']['cos_credential'];print(c['start_time'])")
  ET=$(echo "$CM" | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['data']['cos_credential'];print(c['expired_time'])")
  COS_OUT=$(node $COS_UPLOAD --file "$f" --secret-id "$SEC" --secret-key "$SEK" --token "$TOK" --bucket "$BKT" --region "$REG" --cos-key "$CK" --content-type "$CT" --start-time "$ST" --expired-time "$ET" 2>&1 | tail -1)
  echo "COS: $COS_OUT"
  TITLE=$(head -5 "$f" | grep '^title:' | sed 's/^title: *//')
  AK=$(IMA_SKILL_VERSION=$IMA_VER node $API "openapi/wiki/v1/add_knowledge" "{\"media_type\":7,\"media_id\":\"$MEDIA_ID\",\"title\":\"$TITLE\",\"knowledge_base_id\":\"$KB_ID\",\"file_info\":{\"cos_key\":\"$CK\",\"file_size\":$FSIZE}}" 2>/dev/null | tail -1)
  CODE=$(echo "$AK" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('code',''))" 2>/dev/null)
  if [ "$CODE" = "0" ]; then echo "OK"; OK=$((OK+1)); else echo "FAIL: add_knowledge code=$CODE"; echo "$AK" | head -c 200; echo; FAIL=$((FAIL+1)); fi
done
echo "=== Done: $OK OK, $FAIL FAIL ==="
