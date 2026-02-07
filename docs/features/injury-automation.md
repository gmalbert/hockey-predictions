# Automated Injury Updates

## ⚠️ Current Limitation

**NHL does not provide a free, public injury API.**

After testing multiple sources:
- ❌ NHL API - no injury/roster status endpoint
- ❌ ESPN API - no injury data in team/roster endpoints  
- ❌ ESPN web - requires JavaScript rendering (client-side React)
- ❌ CBS Sports - behind paywall/requires scraping

## Manual Entry Required

For now, injuries must be **manually added via the UI**:

1. Navigate to **🏥 Injury Report** page
2. Select team
3. Use "Add/Update Injury" form
4. Fill in player details and tier

The app will automatically calculate betting impact based on position and tier.

## Future Solutions

### Option 1: Paid Sports Data API
Services that provide injury data:
- **SportsData.io** (~$100/month) - comprehensive NHL data
- **Stattleship** - sports injury feeds
- **MySportsFeeds** - NHL injuries included

### Option 2: Web Scraping
Possible sources (check terms of service):
- **Daily Faceoff** (https://www.dailyfaceoff.com/teams/) - projected lineups + injuries
- **Rotoworld** - fantasy injury updates
- **Individual team sites** - official injury reports

Example Daily Faceoff scraper (not implemented):
```python
# Requires: pip install beautifulsoup4 playwright
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_daily_faceoff(team: str) -> List[Dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f'https://www.dailyfaceoff.com/teams/{team}/line-combinations')
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        # Parse injury section...
        browser.close()
```

### Option 3: Twitter/Social Monitoring
Monitor beat reporters for injury news:
- PHI: @charlieo_conn, @JameyBaskow
- TOR: @kristen_shilton
- NYR: @vzmercogliano
- (etc.)

Could use Twitter API to monitor keywords like "IR", "LTIR", "day-to-day"

### Option 4: Manual + Community
- Maintain a shared Google Sheet
- Update via form submission
- Import daily into app

## Current Workflow

**Daily (Before Betting):**
1. Check Daily Faceoff team pages
2. Check NHL.com team news
3. Manually add/update injuries in app
4. System calculates impact automatically

**Takes ~5-10 minutes for all 32 teams**

## Files
- `src/utils/injury_scraper.py` - Currently returns empty (no free API)
- `update_injuries.py` - Preserves manual entries
- `pages/8_🏥_Injuries.py` - Manual entry UI

## Recommendation

For serious betting:
1. **If budget allows**: Subscribe to SportsData.io ($100/mo)
2. **If time allows**: Build Daily Faceoff scraper with Playwright
3. **For now**: Manual entry (5-10 min/day before games)

The system calculates betting impact automatically once injuries are entered.
