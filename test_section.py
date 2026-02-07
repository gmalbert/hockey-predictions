from pathlib import Path
from bs4 import BeautifulSoup

html = Path('data_files/cache/cbs_injuries.html').read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html.parser')

# Get table 5 (should be a different team than ANA)
table = soup.find_all('table', class_='TableBase-table')[5]
wrapper = table.find_parent('div', class_='TableBaseWrapper')
section = wrapper.parent

print(f'Section tag: {section.name}')
print(f'Section classes: {section.get("class", [])}')
print(f'Section has {len(section.find_all("a"))} total links')

# Get all direct child elements
print('\nDirect children of section:')
for i, child in enumerate(list(section.children)[:10]):
    if hasattr(child, 'name') and child.name:
        print(f'  {i}: <{child.name}> classes={child.get("class",[])}')

import re
team_links = section.find_all('a', href=re.compile(r'/nhl/teams/'))
print(f'\n{len(team_links)} team links found in section')
for link in team_links[:3]:
    print(f'  - {link.get("href")}')

# Look at what comes before the wrapper
prev = wrapper.find_previous_sibling()
print(f'\nPrevious sibling of wrapper:')
if prev and hasattr(prev, 'name'):
    print(f'  Tag: <{prev.name}> classes={prev.get("class", [])}')
    print(f'  Text: {prev.get_text()[:100]}')

# Look two siblings back
prev2 = prev.find_previous_sibling() if prev else None
print(f'\nTwo siblings back:')
if prev2 and hasattr(prev2, 'name'):
    print(f'  Tag: <{prev2.name}> classes={prev2.get("class", [])}')
    print(f'  Text: {prev2.get_text()[:100]}')
    # Check for team link here
    team_link = prev2.find('a', href=re.compile(r'/nhl/teams/'))
    if team_link:
        print(f'  Team link found: {team_link.get("href")}')
