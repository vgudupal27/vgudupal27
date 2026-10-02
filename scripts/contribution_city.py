"""Build an SVG from GitHub's public contribution calendar; stdlib only."""
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.request


def render(calendar):
    weeks = calendar['weeks']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="620" viewBox="0 0 1200 620" role="img">', '<title>Public GitHub contribution city</title>', '<rect width="1200" height="620" rx="22" fill="#101329"/>', '<g font-family="Arial, sans-serif"><text x="40" y="50" fill="#b899ff" font-size="16" letter-spacing="2">MY CONTRIBUTION CITY</text>', f'<text x="40" y="84" fill="#c0c8df" font-size="17">{int(calendar["totalContributions"])} public contributions · {len(weeks)} calendar weeks</text></g>']
    for wi, week in enumerate(weeks):
        for day in week['contributionDays']:
            di = int(day['weekday'])
            count = int(day['contributionCount'])
            x = 160 + wi*16 - di*13
            y = 180 + wi*4 + di*17
            height = min(92, 8 + count*3) if count else 0
            top = y-height
            color = '#64e6d5' if count else '#292c47'
            parts.append(f'<g><title>{html.escape(day["date"])}: {count} contributions</title>')
            if height:
                parts.append(f'<path d="M{x-9} {top+5}L{x} {top+10}V{y+10}L{x-9} {y+5}Z" fill="#346e82"/><path d="M{x} {top+10}L{x+9} {top+5}V{y+5}L{x} {y+10}Z" fill="#7253a3"/>')
            parts.append(f'<path d="M{x} {top}l9 5-9 5-9-5Z" fill="{color}"/></g>')
    parts.append('<text x="40" y="575" font-family="Arial, sans-serif" font-size="16" fill="#9eaac5">Each tower represents a day. Taller towers mean more contributions.</text></svg>')
    return ''.join(parts)


def main():
    username = os.environ['PROFILE_USERNAME']
    now = dt.datetime.now(dt.timezone.utc)
    start = now-dt.timedelta(days=365)
    query = '''query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){contributionCalendar{totalContributions weeks{contributionDays{date weekday contributionCount}}}}}}'''
    payload = json.dumps({'query':query,'variables':{'login':username,'from':start.isoformat(),'to':now.isoformat()}}).encode()
    request = urllib.request.Request('https://api.github.com/graphql', data=payload, headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Content-Type':'application/json','User-Agent':'profile-contribution-city'})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = json.load(response)
    if data.get('errors') or not data.get('data',{}).get('user'):
        raise RuntimeError('GitHub could not return the public contribution calendar.')
    calendar = data['data']['user']['contributionsCollection']['contributionCalendar']
    if not calendar['weeks']:
        raise RuntimeError('GitHub returned an empty contribution calendar.')
    path = Path('assets/contribution-city.svg')
    path.write_text(render(calendar))
    readme = Path('README.md')
    content = readme.read_text()
    marker = '<!-- CITY_IMAGE -->'
    image = '<img src="assets/contribution-city.svg" width="100%" alt="Isometric city generated from my actual public GitHub contributions." />'
    if marker in content:
        readme.write_text(content.replace(marker,image))
    print('Updated public contribution city.')

if __name__ == '__main__':
    main()
