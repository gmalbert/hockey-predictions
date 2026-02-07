from pathlib import Path
from bs4 import BeautifulSoup
import re

html = Path('data_files/cache/cbs_injuries.html').read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html.parser')

# Find links starting with /nhl/teams/ (relative links, not absolute)
links = soup.find_all('a', href=re.compile(r'^/nhl/teams/\w+'))
print(f'Found {len(links)} relative team links\n')

# Filter to just TeamName links (one per team)
team_name_links = [link for link in links if 'TeamName' in link.parent.get('class', [])]
print(f'Filtered to {len(team_name_links)} TeamName links\n')

for i, link in enumerate(team_name_links[:10]):
    href = link.get('href')
    match = re.search(r'/nhl/teams/(\w+)/', href)
    team = match.group(1) if match else 'Unknown'
    
    # Navigate up to find a container, then look for a table within it
    container = link.parent  # span.TeamName
    for level in range(5):  # Go up 5 levels max
        container = container.parent
        if not container:
            break
        
        # Look for table within this container
        table = container.find('table', class_='TableBase-table')
        if table:
            rows = len(table.find_all('tr')) - 1  # Minus header
            print(f'{team}: Found table at level {level} with {rows} injuries')
            print(f'   Container: <{container.name}> classes={container.get("class",[])}')
            break
    else:
        print(f'{team}: No table found')
    print()
