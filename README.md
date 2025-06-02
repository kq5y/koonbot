boonbot -> koonbot

```bash
docker build -t koonbot .
docker run -d \
  --name koonbot \
  --restart unless-stopped \
  -e DISCORD_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -e GUILD_ID="xxxxxxxxxxxxxxxx" \
  koonbot
```
