# Camera node — wildlife-pi

Config for the Raspberry Pi 4 that captures and publishes the camera stream. This is a
separate machine from the inference host; everything else in this repo runs on the
workstation.

These files live only on the Pi's USB SSD. They are here because that drive has twice
been one failure away from taking them with it.

| File | Goes to | Notes |
|---|---|---|
| `mediamtx.yml` | `/usr/local/etc/mediamtx.yml` | Verbatim. Mostly upstream defaults; our settings are in `paths:` at the end |
| `mediamtx.service` | `/etc/systemd/system/mediamtx.service` | Then `systemctl daemon-reload && systemctl enable --now mediamtx` |

## What our settings do

```yaml
feeder:
  rpiCameraCodec: mjpeg          # H.264 caps at 1664x1248 on this encoder
  rpiCameraWidth:  1920
  rpiCameraHeight: 1440          # 2.76 MP, the encoder's real ceiling
  rpiCameraMode: "2028:1520:10:P"  # sensor in 2x2 binned mode, then ISP-downscaled
  rpiCameraMJPEGQuality: 85      # measured 15.3 Mbps / 6.4 GB/hour
```

The sensor runs at 2028x1520 and the ISP downscales to 1920x1440 for the encoder. The
Pi 4's hardware encoder enforces **1920 px per axis and 8192 macroblocks**, which is why
2028x1520 cannot be encoded at all and why MJPEG reaches 1920x1440 where H.264 stops at
1664x1248 — JPEG has no macroblocks. See the build plan, Phase 2, "Full-resolution
capture".

`rpiCameraBitrate` and `rpiCameraH264Profile` are inert while the codec is MJPEG. They
are left in place for the H.264 fallback.

`focus` is a secondary 1024x768 path, useful for focusing by eye at lower latency than
the Frigate UI.

## Networking

The node is **wired**. That is the Phase 2 design, not a fallback — the locked power
topology is a single PoE+ run feeding a 12V bus, so a deployed node has an Ethernet
cable by definition.

NetworkManager generates the wired connection automatically, so no network config is
tracked here. ⚠️ **There is no wifi profile.** It was deleted on 2026-09-10 and not
restored; restoring it means `nmcli device wifi connect`, with credentials from
`/boot/firmware/network-config` on the Pi. Phase 6 will need it when the nodes become
relocatable.

## Restoring the node from scratch

1. Flash Raspberry Pi OS / Ubuntu, boot from the USB SSD.
2. Install mediamtx to `/usr/local/bin/mediamtx`.
3. Copy both files from this directory to the paths in the table above.
4. `sudo systemctl daemon-reload && sudo systemctl enable --now mediamtx`
5. Confirm: `rpicam-vid --list-cameras` sees the imx477, and
   `ffprobe rtsp://<host>:8554/feeder` reports `mjpeg 1920x1440 10/1`.
