# Freerouting is not deterministic: retry until the DRC has no unconnected items (max 5 runs)
cd /home/claude/genGPS_RB
for i in 1 2 3 4 5; do
  bash route_all.sh > /tmp/claude-0/gpsc_route.log 2>&1
  if ! grep -q "unconnected_items\|clearance :" /tmp/claude-0/gpsc_route.log; then echo "clean after run $i"; tail -8 /tmp/claude-0/gpsc_route.log; exit 0; fi
  echo "run $i:"; grep " : @" /tmp/claude-0/gpsc_route.log | cut -c1-160
done
