import json
shortcode = "DXzqymlRuaL"
posts = json.load(open('data/posts.json', encoding='utf-8'))
found = [p for p in posts if p.get('shortcode') == shortcode]
if found:
    print(f"ENCONTRADO: {found[0]['date_display']} | {found[0].get('caption','')[:80]}")
else:
    print(f"NAO ENCONTRADO no site! Shortcode: {shortcode}")
    print(f"Total de posts: {len(posts)}")
    print(f"Post mais recente: {sorted(posts, key=lambda x: x['timestamp'], reverse=True)[0]['date_display']}")
