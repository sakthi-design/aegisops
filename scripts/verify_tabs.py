import re
from bs4 import BeautifulSoup

with open('frontend/public/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
buttons = soup.select('.subnav-tab-btn')
print(f"Total buttons found: {len(buttons)}")

all_ok = True
for b in buttons:
    tab_id = b.get('data-tab')
    target = soup.find(id=tab_id)
    exists = target is not None
    classes = target.get('class', []) if exists else []
    is_pane = 'tab-pane' in classes
    print(f"Tab: {b.text.strip():<32} | ID: {tab_id:<28} | Exists: {exists} | is tab-pane: {is_pane}")
    if not exists or not is_pane:
        all_ok = False

print(f"\nAll tabs matched correctly to .tab-pane: {all_ok}")
