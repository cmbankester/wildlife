# Wildlife monitoring station

Docker Compose setup for a backyard wildlife station: Frigate for camera detection,
BirdNET-Go for acoustic bird identification, and Mosquitto as the MQTT broker that
connects them.

This repo tracks configuration only. Recordings, clips, databases, and logs stay on the
host — see [What this repo tracks](#what-this-repo-tracks).

## Services

| Service | Image | Port | Role |
|---|---|---|---|
| `mosquitto` | `eclipse-mosquitto:2` | 1883 | MQTT broker both detectors publish to |
| `frigate` | `ghcr.io/blakeblackshear/frigate:stable` | 8971, 8554 | Camera object detection and recording |
| `birdnet-go` | `ghcr.io/tphakala/birdnet-go:nightly` | 8080 | Acoustic bird identification |
| `mediamtx` | `bluenviron/mediamtx:latest` | 18554 | RTSP restream source |

Frigate's UI is on port 8971 (the authenticated one). BirdNET-Go's is on 8080.

## Layout

```
docker-compose.yml
frigate/config/config.yml                  Frigate camera, detector, and record config
mosquitto/config/mosquitto.conf            Broker listener and persistence
birdnet-go/config/config.yaml.example      BirdNET-Go config, secrets blanked
```

## Host prerequisites

- An Intel iGPU at `/dev/dri/renderD128`. Frigate's OpenVINO detector is pinned to
  `device: GPU`; setting it to `CPU` fails to load the model.
- A media directory at `/mnt/storage/frigate`, mounted into Frigate as `/media/frigate`.
  Frigate writes `clips/`, `recordings/`, and `exports/` there.
- `shm_size: "256mb"` in `docker-compose.yml`. Frigate needs shared memory proportional to
  camera resolution and count; the default 64 MB isn't enough for a 2028x1520 feed.

## First run on a new host

1. Clone the repo, then create the data directories Compose expects:

   ```bash
   mkdir -p mosquitto/data birdnet-go/data /mnt/storage/frigate
   ```

2. Copy the BirdNET-Go config template into place:

   ```bash
   cp birdnet-go/config/config.yaml.example birdnet-go/config/config.yaml
   ```

   BirdNET-Go generates `security.sessionsecret` and `security.basicauth.clientsecret` on
   first start, so leave both empty in the copy.

3. Set your coordinates in `birdnet-go/config/config.yaml`. `birdnet.latitude` and
   `birdnet.longitude` are `0` in the template, and `birdnet.locationconfigured` is
   `false`, which disables the range filter.

4. Start the stack:

   ```bash
   docker compose up -d
   ```

## Camera input

The `feeder` camera currently reads a looped file fixture rather than a live stream:

```yaml
- path: /media/frigate/feeder-fixture.mp4
  input_args: -re -stream_loop -1
```

Put a video at `/mnt/storage/frigate/feeder-fixture.mp4` to reproduce that setup. To switch
to the live camera, uncomment the `rtsp://mediamtx:8554/feeder` input block in
`frigate/config/config.yml` and remove the file input.

`mediamtx` publishes RTSP on host port 18554 rather than 8554, because Frigate's own RTSP
restream already binds 8554.

## Detection tuning

- `classification.bird.threshold` is `0.65`. Frigate defaults to `0.9`, which is high
  enough to suppress most feeder birds. Start low and tighten.
- Snapshots use `clean_copy: true` and `quality: 95` so you get an unannotated,
  low-artifact image suitable for iNaturalist uploads.
- The COCO label map has no squirrel class. To catch mammals at the feeder, add `cat` to
  `objects.track`.
- `birdnet.threshold` is `0.7` with dynamic thresholding enabled, which drops the
  effective floor to `0.2` after a `0.9`-confidence detection.

## What this repo tracks

Tracked:

- `docker-compose.yml`
- `frigate/config/config.yml`
- `mosquitto/config/mosquitto.conf`
- `birdnet-go/config/config.yaml.example`

Ignored, and why:

| Path | Reason |
|---|---|
| `birdnet-go/config/config.yaml` | Holds generated session and OAuth secrets |
| `birdnet-go/config/.system_id` | Per-install identifier |
| `birdnet-go/config/model-catalog.json` | Downloaded from the upstream model registry |
| `birdnet-go/data/` | Detection database, clips, and logs |
| `frigate/config/.jwt_secret` | Signs Frigate's UI session tokens |
| `frigate/config/go2rtc_homekit.yml` | Holds HomeKit pairing keys once a device pairs |
| `frigate/config/backup_config.yaml` | Frigate rewrites it on every UI config save |
| `frigate/config/*.db*`, `model_cache/` | Event database and cached detector models |
| `mosquitto/data/` | Broker persistence |
| `*.mp4` | Camera fixtures and captures |

After you change BirdNET-Go settings through its web UI, re-export the template so the repo
keeps up:

```bash
sed -e 's|^\(        clientsecret: \).*|\1""|' \
    -e 's|^\(    sessionsecret: \).*|\1""|' \
    birdnet-go/config/config.yaml > birdnet-go/config/config.yaml.example
```
