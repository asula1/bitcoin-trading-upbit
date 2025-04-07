# GitHub Upload Instructions

To upload this project to GitHub, follow these steps:

1. Create a new repository on GitHub:
   - Go to https://github.com/new
   - Name: `jocoding-trading`
   - Description: "Bitcoin automated trading program with Upbit API integration and advanced strategies"
   - Set as Public or Private according to your preference
   - Click "Create repository"

2. Push the code to GitHub using the commands below. First, log in with your credentials:
   ```bash
   # Add the remote repository
   git remote add origin https://github.com/asula1/jocoding-trading.git
   
   # Push the code to GitHub
   git push -u origin main
   ```

3. After pushing, verify that all files are uploaded correctly by visiting your repository URL:
   https://github.com/asula1/jocoding-trading

Note: When prompted for credentials, use:
- Username: asula1@naver.com
- Password: Your GitHub personal access token (not your GitHub password)

If you're using GitHub for the first time, you might need to create a personal access token:
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with "repo" permissions
3. Use this token as the password when pushing

Alternatively, if you prefer SSH:
1. Add your SSH key to GitHub (if not already done)
2. Use the SSH URL instead:
   ```bash
   git remote add origin git@github.com:asula1/jocoding-trading.git
   git push -u origin main
   ```