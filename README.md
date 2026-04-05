# 🔧 MikroTik Monitoring Dashboard

Real-time monitoring dashboard for MikroTik RouterOS.

## Features

- ✅ **System Health**: Uptime, CPU Load, Memory Usage
- ✅ **Interface Monitoring**: Real-time traffic per interface
- ✅ **Auto Refresh**: Updates every 5 seconds
- ✅ **Responsive Design**: Works on mobile & desktop
- ✅ **Dark Mode**: Easy on the eyes

## Quick Deploy

### Option 1: Render (Recommended)

1. **Fork this repo** or push to your GitHub
2. Go to [render.com](https://render.com)
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repo
5. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Add Environment Variables:
   ```
   MIKROTIK_HOST=your_router_ip
   MIKROTIK_PORT=53000
   MIKROTIK_USER=your_username
   MIKROTIK_PASSWORD=your_password
   ```
7. Click **"Create Web Service"**

**Done!** You'll get a URL like: `https://mikrotik-monitor-xxxx.onrender.com`

### Option 2: Railway

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Select this repo
4. Add environment variables (same as above)
5. Deploy!

### Option 3: Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MIKROTIK_HOST=103.133.56.21
export MIKROTIK_PORT=53000
export MIKROTIK_USER=jose
export MIKROTIK_PASSWORD=your_password

# Run
python app.py
```

Open: `http://localhost:5000`

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Tailwind CSS + Vanilla JS
- **MikroTik API**: librouteros
- **Deployment**: Render/Railway

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Main dashboard |
| `/api/status` | JSON data for dashboard |
| `/health` | Health check |

## Security Notes

⚠️ **Important:**
- Use HTTPS in production
- Consider creating a dedicated API user on MikroTik
- Don't commit `.env` file with credentials
- Use firewall rules to restrict access

## License

MIT
