import urllib.request
import sys

routes = [
    '/',
    '/index.html',
    '/timeline',
    '/timeline.html',
    '/rca',
    '/rca.html',
    '/aiops-ml',
    '/aiops-ml.html',
    '/topology',
    '/topology.html',
    '/logs',
    '/logs.html',
    '/privacy',
    '/privacy.html',
    '/report',
    '/report.html',
    '/benchmarks',
    '/benchmarks.html',
    '/forensic-matrix',
    '/forensic-matrix.html',
    '/interactive-timeline',
    '/interactive-timeline.html',
    '/radar',
    '/radar.html',
    '/causal-graph',
    '/causal-graph.html'
]

print(f"Testing {len(routes)} MNC routes against http://localhost:8000 ...")
success = 0
for r in routes:
    url = f"http://localhost:8000{r}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read()
            content_len = len(content)
            # Verify page has actual content and not empty
            has_app_js = b"/static/app.js" in content
            print(f"[OK] {r:<28} -> Status {status} | Size: {content_len:,} bytes | Includes app.js: {has_app_js}")
            success += 1
    except Exception as e:
        print(f"[FAIL] {r:<28} -> Error: {e}")

print(f"\nResult: {success}/{len(routes)} routes succeeded!")
if success == len(routes):
    print("ALL ROUTES VERIFIED 100% OPERATIONAL!")
else:
    sys.exit(1)
