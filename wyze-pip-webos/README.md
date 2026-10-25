# Wyze PiP for LG webOS (G5)

## 1. Bridge (Wyze -> local stream)
Edit `bridge/docker-compose.yml` with your Wyze login + API ID/KEY, then on any always-on LAN machine:

    cd bridge && docker compose up -d

Open `http://<host>:5000` to see camera names. Stream URL format:
`http://<host>:8888/<camera-name>/index.m3u8`

## 2. Install on the TV
1. TV: install **Developer Mode** app from LG Content Store, sign in, turn Dev Mode + Key Server on.
2. PC: `npm i -g @webos-tools/cli`
3. `ares-setup-device` -> add TV IP, port 9922, user prisoner
4. `ares-novacom --device tv --getkey` (enter passphrase shown on TV)
5. `ares-install --device tv com.local.wyzepip_1.0.0_all.ipk`

## 3. Use
First launch opens Settings. Enter one camera per line: `Front Door | http://192.168.1.50:8888/front-door/index.m3u8`

| Remote | Action |
|---|---|
| Arrows | Move PiP to corner |
| OK | Next camera |
| CH+ / CH- | Resize |
| Green | PiP fullscreen toggle |
| Yellow | Hide/show PiP |
| Red | Settings |
| Back | Exit |

**Background** setting: Live TV tuner or HDMI 1-4 plays full screen behind the PiP inside this app.
webOS doesn't let third-party apps float over other apps (Netflix, YouTube, etc.). To watch cable/antenna/HDMI
with the camera on top, use this app's Background setting.
