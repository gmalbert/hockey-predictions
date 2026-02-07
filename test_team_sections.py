from pathlib import Path
from bs4 import BeautifulSoup
import re

html = Path('data_files/cache/cbs_injuries.html').read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html.parser')

# Find all team links
team_links = soup.find_all('a', href=re.compile(r'/nhl/teams/(\w+)/'))

print(f'Found {len(team_links)} total team links')

# Filter to unique teams
seen_teams = set()
unique_team_links = []
for link in team_links:
    href = link.get('href', '')
    match = re.search(r'/nhl/teams/(\w+)/', href)
    if match:
        team = match.group(1)
        if team not in seen_teams:
            seen_teams.add(team)
            unique_team_links.append((team, link))

print(f'Found {len(unique_team_links)} unique teams')
print(f'First 5 teams: {[t[0] for t in unique_team_links[:5]]}')

# For each team link, find the next table
for team, link in unique_team_links[:5]:
    # Find the next sibling that contains a table
    current = link.parent
    table_found = False
    attempts = 0
    while current and attempts < 20:
        next_elem = current.find_next_sibling()
        if not next_elem:
            break
        
        # Check if element contains a table
        table = next_elem.find('table', class_='TableBase-table')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            print(f'{team}: {len(rows)} injuries')
            table_found = True
            break
        
        current = next_elem
        attempts += 1
    
    if not table_found:
        print(f'{team}: No table found')
