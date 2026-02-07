# Keep-Alive Workflow for Streamlit Apps

This GitHub Action pings your Streamlit Community Cloud app to prevent it from going to sleep due to inactivity.

## Quick Setup

### 1. Copy the workflow file

Copy [keep-alive.yml](../../.github/workflows/keep-alive.yml) to your repository's `.github/workflows/` directory.

### 2. Update the app URL

Edit the workflow file and replace the `STREAMLIT_APP_URL` with your app's URL:

```yaml
env:
  STREAMLIT_APP_URL: 'https://your-app-name.streamlit.app'
```

### 3. Commit and push

The workflow will automatically start running on its schedule!

## How It Works

- **Runs**: Twice daily at 9 AM and 9 PM UTC (adjust for your timezone)
- **Randomization**: Adds 0-20 minute random delay before each ping
- **Method**: Simple HTTP GET request using curl
- **Timeout**: 30 seconds max, with 2 retry attempts
- **Logging**: Shows response codes and timestamps

### Why Randomization?

The workflow adds a random delay (0-20 minutes) before pinging to:
- Make logs look more natural (not always at :00 mark)
- Spread load across time window
- Avoid patterns that might look like automated abuse
- Simulate real user traffic patterns

## Customization

### Change the schedule

Edit the cron expression in the workflow:

```yaml
on:
  schedule:
    # Current: 9 AM and 9 PM UTC
    - cron: '0 9,21 * * *'
    
    # Examples:
    # Every 6 hours: '0 */6 * * *'
    # Once daily at noon UTC: '0 12 * * *'
    # Three times daily: '0 8,16,0 * * *'
```

### Manual testing

Trigger the workflow manually:
1. Go to **Actions** tab in GitHub
2. Select **Keep Streamlit App Alive**
3. Click **Run workflow**

Or use GitHub CLI:
```bash
gh workflow run keep-alive.yml
```

## Why This Is Needed

Streamlit Community Cloud puts apps to sleep after periods of inactivity to conserve resources. Sleeping apps:
- Take 10-30 seconds to wake up when accessed
- Can appear unresponsive to users
- May cause poor user experience

Regular pings keep your app "warm" and ready to serve users instantly.

## Best Practices

- **Don't overdo it**: Twice daily is usually sufficient
- **Consider usage patterns**: Schedule pings before peak user times
- **Monitor**: Check the Actions tab for any failures
- **Be respectful**: Don't ping more than necessary (avoid sub-hourly pings)

## Troubleshooting

### Workflow shows warning but doesn't fail

This is normal. The workflow logs warnings but doesn't fail the build, so occasional issues won't spam your notifications.

### Want to test without waiting?

Use `workflow_dispatch` to manually trigger the ping:
1. Go to Actions tab
2. Select the workflow
3. Click "Run workflow"

### Non-200 response codes

- **301/302**: Redirects - usually fine, app is responding
- **403/503**: Temporary server issues - will retry next time
- **404**: Check if the URL is correct

## Cost

GitHub Actions provides:
- **2,000 free minutes/month** for private repos
- **Unlimited** for public repos

This workflow uses ~1 minute per day, well within free limits.

## License

Copy and modify freely for your own projects!

## Related Workflows

See [automated-data-collection.md](../automated-data-collection.md) for other automation workflows in this project.
