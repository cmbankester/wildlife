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
| `feeder-gst.sh` | `/usr/local/bin/feeder-gst.sh` | Mode 755. The camera publisher MediaMTX runs for the `feeder` path |

## What our settings do

The camera is published by **GStreamer**, not by MediaMTX's built-in `rpiCamera` source.
MediaMTX runs `feeder-gst.sh` for the `feeder` path and restarts it if it exits:

```
libcamerasrc (2028x1520 10-bit binned mode, auto exposure, auto white balance)
  -> 1920x1440 I420 at 10 fps
  -> v4l2video31jpegenc, quality 85        # hardware JPEG image encoder, /dev/video31
  -> rtspclientsink -> MediaMTX feeder path
```

**Why not `rpiCamera`:** its MJPEG encoder is software libjpeg-turbo on one thread,
about 100% of a core and the node's main heat source. The hardware image encoder does
the same job at about 20% of a core; measured on 2026-10-16, system CPU fell from about
30% to about 7% and the SoC from 66-71 °C to about 57 °C. MediaMTX v1.20.1's camera helper
has no hardware JPEG path at all, so the switch means leaving it.

The sensor runs at 2028x1520 and the ISP downscales to 1920x1440. The Pi 4's hardware
**H.264** encoder enforces **1920 px per axis and 8192 macroblocks**, which is why it stops
at 1664x1248; JPEG has no macroblocks. The JPEG image encoder advertises 1920x1920, and
1920x1440 is tested. See the build plan, Phase 2, "Full-resolution capture".

- ⚠️ **Use `v4l2video31jpegenc`, not `v4l2jpegenc`.** Plain `v4l2jpegenc` binds
  `/dev/video11` — the video encoder in Motion-JPEG mode — which is bitrate-controlled
  (default 10 Mbps) rather than quality-controlled, and produced half-size frames.
- **Bitrate at quality 85 is about 21 Mbps on the bench scene** (265 kB per frame). That
  is not a hardware penalty: the software encoder's frame of the same scene was 236 kB,
  and on one identical frame the hardware file was smaller (231 against 240 kB). Pass 17's
  15.3 Mbps came from a softer, out-of-focus scene. Real foliage will run higher either way.
- **Not carried over from `rpiCamera`:** `rpiCameraDenoise: "cdn_off"` (libcamerasrc does
  not expose denoise). Exposure is visibly brighter than the software path on the same
  scene; tune with `exposure-value` if it matters.
- **Packages:** `gstreamer1.0-tools`, `-plugins-base`, `-plugins-good`, `-libcamera`,
  `-rtsp`, installed `--no-install-recommends`. `gstreamer1.0-libcamera` pins the system
  libcamera version; when apt upgrades libcamera, upgrade `rpicam-apps` with it —
  `rpicam-hello` 1.13.0 segfaulted against libcamera `0.7.2+rpt20261009` until 1.14.0.
- **Fallback:** the `rpiCamera` settings are kept, commented, in `mediamtx.yml`. Restore
  them and remove the three publisher lines.

`focus` was a secondary 1024x768 path for focusing by eye at lower latency than the
Frigate UI. It is **commented out**: it encoded continuously in software whether or not
anyone watched, about 0.3 of a core. It is a secondary stream of the `rpiCamera` source,
so it only works with the fallback; while GStreamer owns the camera, focus through
`feeder` itself.

## Networking

The node is **wired**. That is the Phase 2 design, not a fallback — the locked power
topology is a single PoE+ run feeding a 12V bus, so a deployed node has an Ethernet
cable by definition.

Log in as `pi` (`ssh pi@wildlife-pi`). A bare `ssh wildlife-pi` sends the workstation
username, and the node rejects it with `Permission denied (publickey)`.

NetworkManager generates the wired connection automatically, so no network config is
tracked here. ⚠️ **There is no wifi profile.** It was deleted on 2026-09-10 and not
restored; restoring it means `nmcli device wifi connect`, with credentials from
`/boot/firmware/network-config` on the Pi. Phase 6 will need it when the nodes become
relocatable.

## Restoring the node from scratch

1. Flash Raspberry Pi OS / Ubuntu, boot from the USB SSD.
2. Install mediamtx to `/usr/local/bin/mediamtx`.
3. Install the GStreamer packages listed under "What our settings do".
4. Copy the files from this directory to the paths in the table above.
5. `sudo systemctl daemon-reload && sudo systemctl enable --now mediamtx`
6. Confirm: `rpicam-vid --list-cameras` sees the imx477, and
   `ffprobe rtsp://<host>:8554/feeder` reports `mjpeg 1920x1440 10/1`.
