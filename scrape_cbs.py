"""Full CBS Sports injury scraper."""
from pathlib import Path
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

html = Path('data_files/cache/cbs_injuries.html').read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html.parser')

# Find all team links (filter to TeamName links)
all_links = soup.find_all('a', href=re.compile(r'^/nhl/teams/\w+'))
team_name_links = [link for link in all_links if 'TeamName' in link.parent.get('class', [])]

print(f'Found {len(team_name_links)} teams\n')

all_injuries = {}

for link in team_name_links:
    href = link.get('href', '')
    match = re.search(r'/nhl/teams/(\w+)/', href)
    if not match:
        continue
    team = match.group(1)
    
    # Navigate up 5 levels from span.TeamName to div.TableBase
    container = link.parent  # span.TeamName
    for _ in range(5):
        container = container.parent
        if not container:
            break
    
    if not container:
        continue
    
    # Find table in this container
    table = container.find('table', class_='TableBase-table')
    if not table:
        continue
    
    # Parse injury rows
    rows = table.find_all('tr')[1:]  # Skip header row
    injuries = []
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 5:
            # Get player name
            player_cell = cells[0]
            player_link = player_cell.find('a')
            player_name = player_link.get_text().strip() if player_link else 'Unknown'
            
            # Get position
            position = cells[1].get_text().strip()
            
            # Get injury type
            injury_type = cells[3].get_text().strip()
            
            # Get status description
            status_desc = cells[4].get_text().strip()
            
            # Map status to our format  
            if 'LTIR' in status_desc:
                status = 'ltir'
            elif 'IR' in status_desc:
                status = 'ir'
            elif 'Day-To-Day' in status_desc or 'day-to-day' in status_desc.lower():
                status = 'day-to-day'
            else:
                status = 'out'
            
            # Estimate tier (default to medium, user can adjust)
            tier = 'medium'
            if position == 'G':
                tier = 'high'  # Goalies important
            
            injuries.append({
                'player_name': player_name,
                'team': team,
                'position': position,
                'status': status,
                'injury_type': injury_type,
                'player_tier': tier,
                'updated': datetime.now().strftime('%Y-%m-%d')
            })
    
    if injuries:
        all_injuries[team] = injuries

# Display results
total_injuries = sum(len(inj_list) for inj_list in all_injuries.values())
print(f"Parsed {total_injuries} injuries across {len(all_injuries)} teams\n")

# Show first 5 teams
for team, injuries in list(all_injuries.items())[:5]:
    print(f"{team}: {len(injuries)} injuries")
    for inj in injuries[:3]:  # Show first 3 per team
        print(f"  - {inj['player_name']} ({inj['position']}): {inj['injury_type']} - {inj['status']}")

# Save to file
output = Path('data_files/injuries.json')
output.write_text(json.dumps(all_injuries, indent=2))
print(f"\nSaved {total_injuries} injuries to {output}")
