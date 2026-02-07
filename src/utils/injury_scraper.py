"""Automated NHL injury data scraper from CBS Sports."""
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List
from pathlib import Path
import json
import re


def scrape_cbs_injuries() -> Dict[str, List[Dict]]:
    """
    Scrape injury data from CBS Sports NHL injuries page.
    
    Returns:
        Dictionary mapping team abbreviations to list of injury dictionaries
        
    Example:
        {
            "ANA": [
                {
                    "player_name": "P. Mrazek",
                    "team": "ANA",
                    "position": "G",
                    "status": "ir",
                    "injury_type": "Lower Body",
                    "player_tier": "high",
                    "updated": "2026-02-06"
                }
            ]
        }
    """
    url = "https://www.cbssports.com/nhl/injuries/"
    
    try:
        # Fetch the page
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all team links (filter to TeamName links = one per team)
        all_links = soup.find_all('a', href=re.compile(r'^/nhl/teams/\w+'))
        team_name_links = [link for link in all_links if 'TeamName' in link.parent.get('class', [])]
        
        all_injuries = {}
        
        for link in team_name_links:
            href = link.get('href', '')
            match = re.search(r'/nhl/teams/(\w+)/', href)
            if not match:
                continue
            
            team_abbrev = match.group(1)
            
            # Navigate up 5 levels from span.TeamName to div.TableBase container
            # Path: span.TeamName → div.TeamLogoNameLockup-name → 
            #       div.TeamLogoNameLockup-nameContainer → div.TeamLogoNameLockup →
            #       h4.TableBase-title → div.TableBase
            container = link.parent  # span.TeamName
            for _ in range(5):
                container = container.parent
                if not container:
                    break
            
            if not container:
                continue
            
            # Find table within this container
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
                        tier = 'high'  # Goalies are important
                    
                    injuries.append({
                        'player_name': player_name,
                        'team': team_abbrev,
                        'position': position,
                        'status': status,
                        'injury_type': injury_type,
                        'player_tier': tier,
                        'updated': datetime.now().strftime('%Y-%m-%d')
                    })
            
            if injuries:
                all_injuries[team_abbrev] = injuries
        
        return all_injuries
        
    except httpx.HTTPError as e:
        print(f"❌ Error fetching CBS Sports injuries: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error parsing CBS Sports injuries: {e}")
        return {}


def save_injuries_to_file(injuries: Dict[str, List[Dict]], filepath: str = "data_files/injuries.json"):
    """Save injuries dictionary to JSON file."""
    output = Path(filepath)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(injuries, indent=2))
    
    total = sum(len(inj_list) for inj_list in injuries.values())
    print(f"✅ Saved {total} injuries across {len(injuries)} teams to {filepath}")


def load_injuries_from_file(filepath: str = "data_files/injuries.json") -> Dict[str, List[Dict]]:
    """Load injuries from JSON file."""
    try:
        return json.loads(Path(filepath).read_text())
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"⚠️  Invalid JSON in {filepath}")
        return {}


if __name__ == "__main__":
    # Test the scraper
    print("Scraping CBS Sports for NHL injuries...")
    injuries = scrape_cbs_injuries()
    
    if injuries:
        total = sum(len(inj_list) for inj_list in injuries.values())
        print(f"\n✅ Found {total} injuries across {len(injuries)} teams\n")
        
        # Show first 3 teams
        for team, inj_list in list(injuries.items())[:3]:
            print(f"{team}: {len(inj_list)} injuries")
            for inj in inj_list[:2]:
                print(f"  - {inj['player_name']} ({inj['position']}): {inj['injury_type']} - {inj['status']}")
        
        # Save to file
        save_injuries_to_file(injuries)
    else:
        print("❌ No injuries found")
if __name__ == "__main__":
    # Test the scraper
    print("Scraping CBS Sports for NHL injuries...")
    injuries = scrape_cbs_injuries()
    
    if injuries:
        total = sum(len(inj_list) for inj_list in injuries.values())
        print(f"\n✅ Found {total} injuries across {len(injuries)} teams\n")
        
        # Show first 3 teams
        for team, inj_list in list(injuries.items())[:3]:
            print(f"{team}: {len(inj_list)} injuries")
            for inj in inj_list[:2]:
                print(f"  - {inj['player_name']} ({inj['position']}): {inj['injury_type']} - {inj['status']}")
        
        # Save to file
        save_injuries_to_file(injuries)
    else:
        print("❌ No injuries found")
