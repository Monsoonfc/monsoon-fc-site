import json
posts = json.load(open('data/posts.json', encoding='utf-8'))
posts.sort(key=lambda x: x['timestamp'], reverse=True)
print(f"Total: {len(posts)} posts")
print("\nUltimos 5 posts:")
for p in posts[:5]:
    print(f"  {p['date_display']} | {p['shortcode']} | {p.get('caption','')[:70]}")
