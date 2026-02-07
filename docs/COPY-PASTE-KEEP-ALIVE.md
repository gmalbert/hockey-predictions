# 🚀 STREAMLIT KEEP-ALIVE - READY TO COPY

## How to Use This in Any Repository

### Step 1: Copy the workflow file below

Create `.github/workflows/keep-alive.yml` in your repository and paste this:

```yaml
name: Keep Streamlit App Alive

on:
  schedule:
    # Run twice daily: 9 AM and 9 PM UTC
    - cron: '0 9,21 * * *'
  workflow_dispatch:

env:
  # ⚠️ UPDATE THIS with your Streamlit app URL
  STREAMLIT_APP_URL: 'https://your-app-name.streamlit.app'

jobs:
  ping-app:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - name: Random delay (0-20 minutes)
        run: |
          DELAY=$((RANDOM % 1200))
          echo "⏳ Waiting ${DELAY} seconds before ping..."
          sleep $DELAY
      
      - name: Ping Streamlit App
        run: |
          echo "🔔 Pinging: ${{ env.STREAMLIT_APP_URL }}"
          RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 --retry 2 "${{ env.STREAMLIT_APP_URL }}")
          echo "Response: $RESPONSE"
          if [ "$RESPONSE" -ge 200 ] && [ "$RESPONSE" -lt 400 ]; then
            echo "✅ App is alive!"
          else
            echo "⚠️ Status: $RESPONSE (will retry later)"
          fi
```

### Step 2: Update the URL

Replace `https://your-app-name.streamlit.app` with your actual Streamlit app URL.

### Step 3: Commit and push

```bash
git add .github/workflows/keep-alive.yml
git commit -m "Add keep-alive workflow for Streamlit app"
git push
```

### Step 4: Verify it works

1. Go to your repository's **Actions** tab
2. Find **Keep Streamlit App Alive** workflow
3. Click **Run workflow** to test manually

---

## Customization Options

### Change the random delay window

```yaml
- name: Random delay (0-20 minutes)
  run: |
    # Change 1200 to adjust max delay in seconds
    DELAY=$((RANDOM % 1200))  # 0-20 minutes
    # Examples:
    # 600 = 0-10 minutes
    # 1800 = 0-30 minutes
    # 300 = 0-5 minutes
    echo "⏳ Waiting ${DELAY} seconds..."
    sleep $DELAY
```

### Remove randomization (fixed time pings)

Just delete the "Random delay" step to ping at exact scheduled times.

### Change frequency

```yaml
# Once daily (noon UTC):
- cron: '0 12 * * *'

# Every 6 hours:
- cron: '0 */6 * * *'

# Three times daily (morning, afternoon, evening):
- cron: '0 6,14,22 * * *'
```

### Multiple apps

```yaml
env:
  PRIMARY_APP: 'https://app1.streamlit.app'
  BACKUP_APP: 'https://app2.streamlit.app'

jobs:
  ping-apps:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Apps
        run: |
          for url in "$PRIMARY_APP" "$BACKUP_APP"; do
            echo "Pinging: $url"
            curl -s -o /dev/null "$url"
          done
```

---

## Why You Need This

- ✅ Prevents sleep/cold starts on Streamlit Community Cloud
- ✅ Keeps app responsive 24/7
- ✅ Better user experience (no 30-second wake-up delays)
- ✅ Free on GitHub Actions (2,000 minutes/month for private repos)
- ✅ Set-and-forget automation
- ✅ Random timing makes logs look natural (not bot-like)

---

## Cron Schedule Reference

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6) (Sunday=0)
│ │ │ │ │
* * * * *

Examples:
'0 12 * * *'      - Daily at noon UTC
'0 */6 * * *'     - Every 6 hours
'0 9,21 * * *'    - 9 AM and 9 PM UTC
'0 0 * * 0'       - Weekly on Sunday at midnight
```

---

## Testing Locally

Test if your app responds:

```bash
curl -I https://your-app-name.streamlit.app
```

You should see `HTTP/2 200` or similar success status.

---

## FAQ

**Q: How often should I ping?**  
A: Twice daily is sufficient. More frequent pings waste resources.

**Q: Will this use up my GitHub Actions minutes?**  
A: Minimal usage (~2 minutes/month). Well within free tier.

**Q: Can I use this with Streamlit sharing?**  
A: Yes, works with any Streamlit deployment that's accessible via URL.

**Q: What if the ping fails?**  
A: The workflow logs the issue but doesn't fail, so you won't get spammed with notifications.

---

**That's it! Copy, paste, customize, and forget about app sleep! 🎉**
