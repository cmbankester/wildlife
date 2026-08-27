# Backyard Wildlife Monitoring Station — Build Plan

**Status:** ✅ Phase 1 running on existing workstation — Pass 14
**Last updated:** 2026-08-27

A local-inference camera + acoustic station for bird ID (image + sound), with a
parallel ultrasonic channel for bats and orthoptera. No third-party inference.

---

## Changelog

| Pass | Date | What changed |
|------|------|--------------|
| 1 | 2026-08-14 | Initial plan. Architecture, enclosure, mounting, and bat channel decided. Camera/lens, solar sizing, and software config still open. |
| 2 | 2026-08-14 | Phase 0 marked done (existing Merlin dataset). Swapped ultrasonic and solar — ultrasonic is now Phase 5, solar Phase 6. Added wired power to the ultrasonic mast as a new open question. |
| 3 | 2026-08-14 | Phase 2 restructured around observation quality. Detect stream must be high-res (reverses standard Frigate advice). Added `clean_copy`, detect fps, and the `best.jpg?crop=1` iNat path. |
| 4 | 2026-08-14 | Camera and lens decided: Pi HQ Camera + 16mm C-mount at 2.2m, binned 2028×1520. Added framing/focal-length/light-budget math and a 25mm upgrade path. Mounting reframed around rigidity rather than concrete. Fixed Pi 5 4GB misattribution. Storage identified as the real constraint over bandwidth. |
| 5 | 2026-08-14 | Phase 1 expanded: N100/N150 16GB confirmed sufficient, with load budget, N305/Core Ultra upgrade tiers, ordering checklist, and the OpenVINO/`shm_size` config gotchas. Detector choice closed out. |
| 6 | 2026-08-14 | Camera/mic requirements closed. **Reversed** the separate-camera-mount decision — single enclosure with a window, since the Pi camera module invalidated it. Node board set to Pi 4 (hardware encoder). Added camera settings to lock, mic plug-in-power and RTSP items, bat mast on active USB, and single PoE+ topology with surge protection. |
| 7 | 2026-08-14 | Phase 1 software expanded with working docker-compose, Frigate config, mosquitto.conf, and verification commands. MQTT decided (Mosquitto, as the Phase 7 seam). Storage decided (`record.retain.days: 0`, event-only). Added regional labelmap pruning and the one-time-internet caveat for the classification model. |
| 8 | 2026-08-14 | Added bench testing harness (MediaMTX + looping ffmpeg) as a permanent regression fixture, plus first-run sequencing checklist. Phase 1 planning complete — ready to execute. |
| 9 | 2026-08-14 | **Fixed a bug in the bench ffmpeg command** — IMX477 is 4:3, so 16:9 phone footage needs `crop=ih*4/3:ih` or it renders squashed. Added IMX477 sensor mode table, full frame dimensions (86×65cm), and phone-footage capture guidance. |
| 10 | 2026-08-14 | Site survey via framing preview. Three activity zones confirmed (feeder, perch +20cm, bath to be relocated). **Layout decided: horizontal, not stacked** — bath beside the feeder, never behind it. Distance revised 2.2m → **2.5m**. Added the 3.4× sizing rule, bath watch-outs, and focus-setting procedure. |
| 11 | 2026-08-26 | **✅ PoC validated on Alder Lake-S bench.** 5.45ms inference, working classification (Mourning Dove), MQTT events confirmed. New findings: Frigate 0.17 auto-detects hwaccel (commenting out doesn't disable); `detectors`/`model` are a pair; RTSP publisher throughput causes corrupt-stream symptoms that masquerade as other bugs — **use file-direct on the bench**; `sub_label` arrives on event *updates*. ⚠️ **Wind pushes detect CPU to 154% — motion masking is now a prerequisite for N100 sizing.** |
| 12 | 2026-08-26 | **Compute purchase cancelled** — stack stays on the existing always-on workstation, which already delivers the validated 5.45ms. Recorded **Intel-only** as a hard constraint for any future buy (AMD loses the OpenVINO GPU path and degrades enrichments). Noted NPU is *slower* than iGPU for detection. Added **Phase 8 — Runbook** as a deliverable, elevated because compute lives on a work machine. |
| 13 | 2026-08-26 | Repo created: github.com/cmbankester/wildlife. Config now under version control — the main work-machine risk is mitigated. Added secrets and media gitignore guidance (note: source video carries home GPS coordinates). |
| 14 | 2026-08-27 | **Storage decision corrected — it was wrong twice over.** `record.retain` does not exist in Frigate 0.17 (renamed to `record.continuous`); Frigate rejected it and ran in **safe mode**, which skips all cleanup. And `continuous.days` already defaults to 0, so the setting was a no-op even spelled correctly. The real cause of 126 GB in 40 h was `detections.retain: 30d` covering the 55% of timeline a looping fixture marks as detections. **Recording is now off on the bench** — recording a loop of a file you already have stores nothing. Restore `alerts`/`detections` to 30 d with the real camera. Also: repo leak paths closed (`.MOV` was unignored, and the config re-export would have copied `birdnet.latitude`/`longitude` into the tracked template); `birdmap.txt` now tracked so pruning is diffable; **819 kernel GP faults** in `pipe2()` on CPU 1 wedged docker exec, health checks, and git until a reboot onto 6.8.0-138. |

---

## Locked design decisions

These are settled. Don't re-litigate them on later passes without a reason.

1. **Capture is separated from inference.** Outdoor nodes only capture and stream.
   All ML runs on an indoor box on wall power.
2. **Outdoor nodes run on 12V DC natively.** An external PoE→12V splitter feeds
   the bus now; a battery feeds the same bus after solar conversion. Identical
   node either way — which is why the official PoE HAT (5V out, plus a fan) is
   ruled out.
3. **Everything local.** Frigate for video, BirdNET-Go for audio. Merlin / iNat
   integration is post-processing only, added later.
4. **Right-size each machine separately.** The *indoor host* wants 16GB because
   each RTSP stream spawns another FFmpeg process and three audio models load at
   once. The *camera node* is a **Pi 4**, chosen for its hardware H.264 encoder —
   less CPU, less heat, less power than a Pi 5, which has no hardware encoder.
5. **The bat mic gets its own mast**, but connects to the bird box by active USB.
   One computer outdoors, not two.
6. **A good observation beats a confident label.** Optimize the pipeline for
   sharp, well-framed captures; treat species ID as a bonus layer. This is why
   the detect stream runs at high resolution despite the CPU cost.
7. **MQTT is the integration seam.** Frigate and BirdNET-Go both publish to a
   local Mosquitto broker. Phase 7 post-processing subscribes to that bus rather
   than coupling to either application.
8. **Compute stays on the existing workstation.** No purchase. ⚠️ If that ever
   changes, **Intel only** — Frigate's OpenVINO GPU/NPU path requires it, and
   AMD drops you to CPU detection with degraded enrichment support.
9. **The runbook is a deliverable, not a nice-to-have.** Compute lives on a work
   machine, so porting is plausible. See Phase 8.

---

## Phase 0 — Baseline species list ✅ DONE

*Satisfied by existing Merlin recordings and an established species list for the
property. No survey period needed.*

This dataset is an asset for later phases, not just a checkbox:

- [ ] Cross-check the species list against the iNat classifier's label set to
      find which local birds Frigate **can't** name. Now informational rather
      than blocking — unnamed birds still produce usable observations — but it
      tells you which gaps are expected vs. which indicate a real problem.
- [ ] Use it to set BirdNET-Go's range filter and per-species thresholds from
      day one instead of tuning blind
- [ ] Use the known regulars to sanity-check detections during Phase 1 bench
      testing — a known-good reference beats guessing
- [ ] Note the gap: Merlin data is diurnal and audible-band only. It says nothing
      about Phase 5, where you'll be starting from zero.

---

## Phase 1 — Indoor compute box

*Goal: the permanent brain, on wall power, before anything goes outside.*

### Hardware — DECIDED: existing workstation, purchase deferred
**No compute purchase.** Frigate + BirdNET-Go run on the existing Alder Lake-S
Ubuntu workstation, which already measured **5.45ms** OpenVINO inference.

**Why defer:**
- Buying an Intel mini PC would reproduce a result already in hand — the same
  OpenVINO/iHD path, same driver stack
- The workstation is genuinely always-on, which is the only hard requirement
  Frigate and BirdNET-Go have
- Its other duties (fleet health-check HTTP, tmux sessions) don't contend with
  GPU decode or audio inference
- **Marginal cost is near zero** — the machine runs regardless, so you pay only
  for decode and inference load, not idle draw
- ⚠️ Current sizing numbers are contaminated by wind false-positives anyway.
  Size against real camera input after masking, not before.
- 2026 DDR5 pricing is punishing; barebones + RAM is poor value right now

**Revisit if:** the workstation stops being available, semantic search proves
compelling in practice, or a second camera is added.

### ⚠️ If you do buy later: Intel only
**Non-negotiable constraint.** Frigate's OpenVINO detector requires a supported
Intel platform for GPU or NPU use — it runs on AMD CPUs but only in **CPU mode**.
AMD means CPU detection or the `-rocm` image, and Frigate disables ROCm
enrichment models that are unstable, so only some are available. An AMD box
(e.g. the Ryzen 8845HS options that look cheap) discards the validated 5.45ms
path *and* compromises semantic search.

Also avoid, if buying:
- **Panther Lake (Core Ultra X7/X9)** — brand-new silicon, immature Linux
  drivers, $1,600+ configs. Wrong for an unattended appliance.
- **V-series (258V, 288V)** — Lunar Lake uses on-package LPDDR5X. Soldered,
  capped, non-upgradeable.

Target instead: **Meteor Lake (155H/185H) or Arrow Lake H (225H/255H)** with
SO-DIMM slots, dual M.2, Arc iGPU, 2.5GbE. Cross-check the exact model against
Frigate GitHub discussions for posted inference numbers.

### ⚠️ Portability — this is a work machine
The station depends on hardware whose lifecycle you don't fully control. If the
job ends or IT reimages it, everything goes with it.

**Repo: https://github.com/cmbankester/wildlife** ✅

- [x] Config under version control — `docker-compose.yml`, `config.yml`,
      `mosquitto.conf`
- [ ] **Put media on a path that survives a reimage.** If `/mnt/storage/frigate`
      is on the OS drive, a rebuild takes your clips and the BirdNET database
      with it. Separate disk or NAS mount.
- [ ] ⚠️ **Never commit secrets.** Frigate 0.17 generates an admin password; MQTT
      creds and any future API tokens (iNat, Merlin) belong in a gitignored
      `.env`, referenced from compose. Commit a `.env.example` instead.
- [ ] Runbook (Phase 8) lives in this repo alongside the configs

### Load profile — why this works

| Workload | Runs on | Cost |
|---|---|---|
| Video decode (2028×1520@10fps) | iGPU / Quick Sync | ≈1080p15. Trivial. |
| Object detection | iGPU via OpenVINO | **5.45ms measured** |
| Bird classification | CPU | Only fires on detected birds |
| BirdNET-Go multi-model | CPU | Main CPU consumer |

GPU does video, CPU does audio, neither contends.

### If a purchase becomes necessary — tiers
Only relevant if the workstation stops being viable. Intel-only, per above.

| Chip | Why you'd want it |
|---|---|
| **N100 / N150** (4 E-cores) | Sufficient for one camera + three audio models, *conditional on motion masking*. Cheapest viable option. |
| **N305 / N355** (8 E-cores) | Doubles CPU cores cheaply. For **more cameras**, a second station, or extra audio models. The cheapest way to remove all doubt. |
| **Core Ultra H** (Meteor/Arrow Lake) | For Frigate **enrichments** — semantic search, face/plate recognition. ⚠️ Buy for the **Arc iGPU**, not the NPU: measured reports put the NPU *slower* than the iGPU (Core Ultra 5 245K: ~4ms iGPU vs 12–20ms NPU; Core Ultra 2 285H: ~30ms NPU vs 13–18ms iGPU). The NPU's value is offloading detection so the GPU is free for enrichments, not raw speed. |

> Rule of thumb: small-core chips are limited by **cores**, not GPU. Future CPU
> work (more audio models, more streams) → N305. Future GPU work (enrichments) →
> Core Ultra H.

**Whatever you buy:** 32GB, SO-DIMM (not soldered), dual M.2, 2.5GbE, Linux.
Skip the Coral — OpenVINO on the iGPU is enough and it frees the M.2 slot.

### MQTT — DECIDED: yes, run Mosquitto
Not for Home Assistant (optional, later). **MQTT is the integration seam for
Phase 7.** Both Frigate and BirdNET-Go publish detections to it, which means:

- The iNat/Merlin pipeline subscribes to one bus instead of polling two APIs
- **Cross-modal correlation becomes possible** — an audio detection and a visual
  detection within the same few seconds is far stronger evidence than either
  alone. This is the payoff for running both pipelines, and it needs a shared bus.
- Post-processing can be written and rewritten without touching Frigate or
  BirdNET-Go config

Cost is one small container and a few MB of RAM. Do it now so Phase 7 has
somewhere to plug in.

### Stack: `docker-compose.yml`

```yaml
services:
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: mosquitto
    restart: unless-stopped
    ports: ["1883:1883"]
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data

  frigate:
    image: ghcr.io/blakeblackshear/frigate:stable
    container_name: frigate
    restart: unless-stopped
    privileged: true
    shm_size: "256mb"          # see calculation below
    devices:
      - /dev/dri/renderD128:/dev/dri/renderD128   # Intel iGPU
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - ./frigate/config:/config
      - /mnt/storage/frigate:/media/frigate
      - type: tmpfs
        target: /tmp/cache
        tmpfs: { size: 1000000000 }
    ports:
      - "8971:8971"    # authenticated UI
      - "8554:8554"    # RTSP restream
    depends_on: [mosquitto]

  birdnet-go:
    image: ghcr.io/tphakala/birdnet-go:nightly
    container_name: birdnet-go
    restart: unless-stopped
    ports: ["18080:8080"]   # host 8080 is contested; container still serves 8080
    environment:
      - TZ=America/Chicago
    volumes:
      - ./birdnet-go/config:/config
      - ./birdnet-go/data:/data
    depends_on: [mosquitto]
```

> For bench testing, also add the **MediaMTX** service from the bench harness
> section below, and point the camera at `rtsp://mediamtx:8554/feeder`.

`mosquitto/config/mosquitto.conf`:

```
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest stdout
```

> Anonymous is fine on a trusted LAN segment. Add auth if this ever routes
> beyond it.

### `frigate/config/config.yml`

```yaml
mqtt:
  enabled: true
  host: mosquitto
  port: 1883
  topic_prefix: frigate
  stats_interval: 60

detectors:
  ov:
    type: openvino
    device: GPU          # NOT CPU — see gotchas

model:
  width: 300
  height: 300
  input_tensor: nhwc
  input_pixel_format: bgr
  path: /openvino-model/ssdlite_mobilenet_v2.xml
  labelmap_path: /openvino-model/coco_91cl_bkgr.txt

classification:
  bird:
    enabled: true        # disabled by default
    threshold: 0.65      # default 0.9 is very high; start lower and tighten

birdseye:
  enabled: false         # pointless with one camera

cameras:
  feeder:
    enabled: true
    ffmpeg:
      hwaccel_args: preset-vaapi
      inputs:
        - path: rtsp://<node-ip>:8554/cam
          roles: [detect, record]
    detect:
      enabled: true
      width: 2028
      height: 1520
      fps: 10
    objects:
      track:
        - bird
        # - cat    # optional: catches squirrels/mammals, COCO has no squirrel
    snapshots:
      enabled: true
      clean_copy: true     # un-annotated copy for iNat
      timestamp: false
      bounding_box: false
      quality: 95          # default 70 leaves visible compression artifacts
      retain:
        default: 60
    record:
      enabled: true
      continuous:
        days: 0            # 0.17 key. Was `retain` pre-0.17. Already the default.
      motion:
        days: 0
      alerts:
        retain: { days: 30 }
      detections:
        retain: { days: 30 }
```

**⚠️ The storage decision was wrong — corrected in pass 14.** `record.retain` does
not exist in Frigate 0.17; it was renamed to `record.continuous`, and Frigate
rejects the old key outright, falling back to **safe mode** — which silently
skips storage maintenance, event cleanup, and recording cleanup. Worse, the
setting was a no-op regardless: `record.continuous.days` already defaults to 0.

**Event-only retention was never the lever.** `alerts.retain` and
`detections.retain` are, and they default to 30 days. On the bench that kept
116.6 GB of 123.8 GB, because a looping fixture puts detections across 55% of
the timeline. Only 7.2 GB sat outside a review window. See pass 14.

**`quality: 95` matters more here than in a security build** — it's the same
principle as locked decision #6. The snapshot is the deliverable.

### `shm_size` calculation
Formula: `(width × height × 1.5 × 9 + 270480) / 1048576` MB per camera.

For 2028×1520 → ~40MB. Docker's 64MB default is *technically* enough for one
camera, but Frigate also caches recordings in `/dev/shm`. **256MB** gives margin
without thought.

### BirdNET-Go setup
**Don't hand-write the YAML.** BirdNET-Go is under active nightly development
with an onboarding wizard, a model gallery UI, and hot-reload settings — config
keys have churned. Bring the container up and configure through the web UI at
`:18080` (the container serves 8080; the host publishes 18080).

- [ ] Set **location** — drives the range filter, which is a major false-positive
      reduction and directly useful given your known species list
- [ ] Add the bird mic as an **RTSP source** (or sound card during bench testing)
- [ ] Install models from the gallery: **BirdNET v2.4** first, add **Perch v2**
      once stable
- [ ] Enable **MQTT** output, host `mosquitto`, port 1883
- [ ] Defer BattyBirdNET to Phase 5

### Regional label pruning (optional, high value)
Frigate's bird labelmap lives at `config/model_cache/bird/birdmap.txt`, formatted
as `Scientific name (Common Name)`. You can rename entries for birds that don't
occur in Louisiana so obvious misfires are recognizable.

- [ ] **Do not add or remove lines** — the model returns a fixed index into this
      file. Rename only.
- [ ] Officially unsupported. Back it up first.
- [ ] Your Merlin species list is exactly the input for this.

### Config gotchas — the ones that waste a weekend
- [ ] **`preset-vaapi` accelerates ffmpeg decoding only, NOT object detection.**
      You must also declare the `openvino` detector with `device: GPU`. Leaving
      detection on CPU produces high CPU load and the false conclusion that the
      hardware is undersized.
- [ ] **Set `shm_size` explicitly.** The Docker default is small and Frigate fails
      confusingly. Most common first-install mistake.
- [ ] **Bird classification needs one-time internet access** to download the model
      and labelmap from GitHub; it runs fully offline afterward. ⚠️ Plan this
      around the network segmentation in open question #4 — firewall the node off
      the internet *after* first run, not before.
- [ ] **Acceptance test: ~15ms inference.** A correctly configured N100 hits this.
      Reports of ~60ms traced to host kernel/driver problems, not hardware — fix
      drivers rather than buying a bigger box.

### Verification
```bash
# Watch every detection from both pipelines on one bus
mosquitto_sub -h localhost -t '#' -v

# Frigate events only (JSON: new / update / end)
mosquitto_sub -h localhost -t 'frigate/events' -v
```

- [ ] Frigate UI → System → confirm inference speed and GPU (not CPU) detector
- [ ] Trigger a detection, confirm a `sub_label` appears
- [ ] Confirm both Frigate and BirdNET-Go messages land on the same broker —
      that's the Phase 7 foundation working

### ✅ Bench results — PoC validated (pass 11)
Full chain confirmed working on an Alder Lake-S workstation: stream → decode →
detection → classification → MQTT.

| Metric | Measured | Notes |
|---|---|---|
| OpenVINO inference | **5.45ms** | Well under the 15ms target |
| camera_fps | 10.1 | Matches the 10fps stream |
| detect/sec | **~104** | ⚠️ ~10× per frame — see wind finding |
| detect CPU | **154%** | ⚠️ Fine here, **not** fine on an N100 |
| Classification | Working | `sub_label: Mourning Dove` — plausible for the site |

**`sub_label` arrives on event *updates*, not the initial detection.** Detection
fires first; classification runs across subsequent frames and amends the event.
⚠️ Phase 7 must subscribe to event updates, not just new events, or it will miss
every species label.

### ⚠️ Wind is the load driver at this site — masking is a prerequisite
Wind-moved vegetation generates ~10 motion regions per frame. GPU cost is
trivial (5.45ms × 10), but the **CPU** side — motion detection, region
extraction, tracking, object association — scales with region count. That's the
154%.

154% of one core is nothing on a desktop. **On an N100 with 4 cores also running
three audio models, it is not.** The N100 sizing in this plan assumes this gets
fixed.

- [ ] **Draw motion masks over background vegetation** using Settings → Motion
      Tuner in the UI, which generates the polygon coordinates visually
- [ ] Raise `motion.threshold` and `contour_area` so small leaf movement doesn't
      qualify
- [ ] **Target: detect/sec under ~20** before trusting the N100 sizing
- [ ] ⚠️ Mask the *background*, never the zone where birds land
- [ ] ⚠️ Masks drawn on bench footage **do not transfer** — the fixture frame is
      ~2.7× wider than production. Re-draw against the real camera.

```yaml
    motion:
      mask:
        - 0,0,0.4,0,0.4,0.3,0,0.3   # fractional coords; use the UI editor
      threshold: 30
      contour_area: 15
```

### ⚠️ Frigate 0.17 auto-detects hwaccel — commenting it out does NOT disable it
Cost several hours of misdiagnosis. Commenting `hwaccel_args` lets
auto-detection take over, so `-hwaccel vaapi` keeps appearing in the ffmpeg
command line while the config looks clean.

- [ ] To actually disable it, set it **explicitly empty**: `hwaccel_args: []`
- [ ] **The only reliable check is the running process, not the config:**
      `docker exec frigate ps aux | grep ffmpeg`
- [ ] `detectors:` and `model:` are a **pair** — enabling one without the other
      gives `TypeError: stat: path should be string... not NoneType`, the detector
      process dies, and the watchdog takes the whole container down. Clean-looking
      shutdown logs with no cause? Scroll up for a Python traceback.

**VA-API status: unresolved, deferred to Phase 2.** It failed on the bench, but
the stream was genuinely corrupt at the time (see below), and hardware decoders
reject invalid streams that software decode conceals. So this is *not* evidence
that VA-API is broken on Alder Lake — retest against real camera input before
concluding anything.

### ⚠️ Skip RTSP on the bench — feed Frigate the file directly
The MediaMTX + ffmpeg publisher path cost hours and tested nothing relevant.
Root cause: the publisher ran at **speed=0.989x**, slightly below real time, so
RTSP muxing wrote partial frames → `concealing 4655 DC/AC/MV errors in I frame`
→ visible blur bands and pink/black artifacts. `-preset ultrafast` didn't fix it.

**The fix was deleting the whole layer:**

```yaml
    ffmpeg:
      inputs:
        - path: /media/frigate/feeder-fixture.mp4
          input_args: -re -stream_loop -1
          roles: [detect]
```

Copy the fixture to the host path mapped to `/media/frigate`. No MediaMTX, no
publisher process, no RTSP corruption class. **You're testing detection and
classification, not RTSP transport** — the real camera validates the network path
in Phase 2.

> Keep the MediaMTX harness below for reference, but reach for file-direct first.
> Corrupt-stream symptoms (artifacts, VA-API failures, inflated detection counts)
> masquerade as unrelated problems and will burn a session.
### Bench testing harness (RTSP path — fallback / reference only)
Prefer the file-direct config above. Use this only when you specifically want to
exercise the RTSP path.

**Keep the fixtures either way.** A fixed video file is a *repeatable regression
fixture*, which a live camera can never be. Change a threshold, replay the same
clip, compare results directly — tuning becomes empirical instead of a week of
waiting to see whether it felt better.

Add MediaMTX to the compose stack:

```yaml
  mediamtx:
    image: bluenviron/mediamtx:latest
    container_name: mediamtx
    restart: unless-stopped
    ports: ["18554:8554"]   # NOT 8554 — Frigate already binds that on the host
```

⚠️ **Port conflict:** Frigate binds host 8554 for its own RTSP restream. The
`18554` mapping exists only so you can inspect the stream in VLC. Frigate reaches
MediaMTX over the Docker network, so in `config.yml` use the container name:

```yaml
        - path: rtsp://mediamtx:8554/feeder
```

Push a looping file in:

```bash
ffmpeg -re -stream_loop -1 -i birds.mp4 \
  -vf "crop=ih*4/3:ih,scale=2028:1520" -r 10 \
  -c:v libx264 -preset veryfast -tune zerolatency \
  -f rtsp -rtsp_transport tcp \
  rtsp://localhost:18554/feeder
```

- `-re` reads at real-time pace. Without it, ffmpeg blasts the whole file through
  in seconds.
- `-stream_loop -1` loops forever
- ⚠️ **`crop=ih*4/3:ih` is required for 16:9 source footage.** The IMX477 is
  **4:3**, so scaling a phone video straight to 2028×1520 squashes it
  horizontally — the exact distortion you're trying to evaluate. Omit the crop
  only if the source is already 4:3.
- `scale` and `-r` deliberately match the real target, so this validates the
  actual resolution path and the `shm_size` math, not a toy stream
- ⚠️ **Watch the publisher's `speed=` value.** Anything at or below 1.0x means it
  can't keep up and RTSP will mux partial frames, producing corrupt I frames.
  Symptoms look like unrelated bugs: blur bands, chroma artifacts, VA-API decode
  failures, inflated detection counts. `-preset ultrafast` may not be enough —
  go file-direct instead.
- ⚠️ **`-c copy` does not work with `-stream_loop`.** Timestamps reset at the wrap
  and B-frames reference frames that no longer exist → `co located POCs
  unavailable`. Re-encode, or use file-direct.

**Source footage — shoot it yourself.**
- [ ] ~10 minutes of phone video at ~2.5m from the intended camera location,
      **on a tripod or propped**. Handheld shake triggers motion detection across
      the whole frame and masks whether Frigate is finding actual birds.
- [ ] **Shoot 4:3 if the camera app offers it** for video — avoids the crop entirely
- [ ] **Shoot 4K, not 1080p.** Target is 2028×1520 (~3MP); 1080p is 2MP, so you'd
      be upscaling. 30fps is fine — downsampling to 10 is free.
- [ ] **Set shutter to 1/500s if you have a pro mode.** At default 30fps a phone
      shoots around 1/60s, so footage will be *blurrier* than production. A
      conservative test, but if classification struggles you won't know whether
      it's framing or blur that won't exist in the real thing.
- [ ] Include variety in one clip: two or three species, one partially obscured,
      **one at the frame edge** — that last one exercises Frigate's
      edge-deprioritization when picking the best frame
- [ ] Note the time of day. Good light proves nothing about dawn/dusk, which is
      where this build actually strains. A second low-light clip is the honest test.
- [ ] Doubles as **site scouting**: reveals whether the lighting plan works, the
      background is too busy, and whether the frame size feels right — all before
      buying a lens
- [ ] Wikimedia Commons has CC-licensed bird video as a fallback

> **Limitation:** phone footage carries HDR, sharpening, and noise reduction the
> HQ camera won't. This validates framing, geometry, and the software pipeline —
> not final image quality.

**Two things that look like tests but aren't:**
- `ffmpeg -f lavfi -i testsrc` confirms only that Frigate connects and decodes.
  Zero detections — it cannot validate the part that matters.
- A looping still image triggers no motion, so nothing downstream ever fires.

⚠️ **Don't tune for hardware you won't deploy on.** If the test workstation has an
Nvidia GPU, resist the TensorRT path — you'd be validating a config you throw away.

### First-run sequencing
- [ ] Comment out the `detectors` and `model` blocks and let Frigate fall back to
      the CPU detector. Confirm the stream connects and decodes **first**, then
      enable OpenVINO. Otherwise a stream problem and a driver problem look
      identical in the logs and you debug two things at once.
- [ ] Replace `<node-ip>` / stream path — it's a placeholder, Frigate won't connect
      until it's real
- [ ] Point `/mnt/storage/frigate` at a real path, or Docker silently creates an
      empty directory somewhere unhelpful
- [ ] Camera name `feeder` becomes part of MQTT topics and API paths. Settled.

---

## Phase 2 — Camera node, wired

*Goal: working detection + good observations outdoors on Ethernet, before adding
solar complexity.*

**Reframe:** species classification is a bonus layer, not the point. Frigate
detects `bird` as a standard COCO object class; species classification runs
afterward and adds a `sub_label` on top. If the classifier has no label for a
species or gets it wrong, the detection, snapshot, clip, and event all survive —
you just have an unnamed bird. An unnamed bird with a sharp photo is a
submittable iNat observation, so **the snapshot is the real deliverable.**

### Camera and lens — DECIDED
**Raspberry Pi HQ Camera (IMX477), standard IR-filtered version, C-mount
telephoto lens.** Chosen over a commercial IP camera because minimum focus
distance and manual exposure are guaranteed rather than gambled on.

### Scene layout — DECIDED: horizontal, not stacked
Site survey (pass 10) found three activity zones: **feeder**, **perch ~20cm
above it**, and a **bird bath** to be relocated into frame. All at roughly equal
distance from the camera.

**Arrange the bath BESIDE the feeder, not above, below, or behind it.**

The frame is 4:3 — wider than it is tall — so the horizontal axis is where the
spare room is. Stacking zones vertically fights the aspect ratio and forces the
camera further back.

| Layout | Distance needed | Frame (W × H) | Cardinal px tall |
|---|---|---|---|
| Vertical stack | 2.9m | 113 × 85cm | ~393 |
| **Horizontal** ← chosen | **2.5m** | **98 × 74cm** | **~450** |

- [ ] ⚠️ **Never place the bath directly behind the feeder.** Two failures: the
      feeder *occludes* bathing birds, and a reflective water surface becomes the
      background for every feeder shot — bright and moving, the exact opposite of
      the dark static background the whole aiming plan depends on.
- [ ] Offset the bath 20–30cm in depth to clear the feeder's shadow. Well inside
      the focus range, so it costs nothing.
- [ ] **Center vertically between perch and feeder, not on the feeder.** A perched
      cardinal is ~15cm tall plus crest; centering on the feeder puts its head at
      the top edge — precisely where Frigate penalizes edge-touching frames.

**Sizing rule: camera distance ≈ 3.4 × desired frame height.**

| Distance | Frame (W × H) | Cardinal px tall |
|---|---|---|
| 2.2m | 86 × 65cm | ~515 |
| **2.5m** | **98 × 74cm** | **~450** |
| 2.6m | 102 × 77cm | ~434 |
| 2.9m | 113 × 85cm | ~393 |
| 3.2m | 125 × 94cm | ~356 |

> Measure the real span across all zones, add ~20cm for bird height and margin,
> multiply by 3.4. **Distance is the free variable** — 2.2m came from the lens,
> not from the yard. Let the site decide.

### Bird bath — three specific watch-outs
The bath is worth the resolution cost because **baths attract species feeders
never will** — thrashers, warblers, vireos, thrushes. For an observation-first
build that's a real expansion of the species list.

- [ ] **Site it reflecting foliage or fence, not open sky.** Water mirrors bright
      sky and blows out exposure — same failure as a sky background.
- [ ] **Still water only.** A dripper or fountain fires motion detection
      continuously. If one is added later, mask that region in Frigate.
- [ ] **Expect worse classification on bathing birds.** Soaked plumage changes
      silhouette and color, and is underrepresented in training data. The
      observation still lands; the label may not.

### Framing reference

| Species | Length | % of 74cm frame | Px tall @1520 |
|---|---|---|---|
| Hummingbird | 9cm | 12% | ~185 |
| Carolina chickadee | 12cm | 16% | ~245 |
| Cardinal | 22cm | 30% | ~450 |
| Blue jay / mourning dove | 28–30cm | 38–41% | ~580 |

**Focal length vs. perch distance** (IMX477 sensor height 4.71mm):

| Distance | Focal length for 65cm | for 74cm |
|---|---|---|
| 2.2m | 16mm | 14mm |
| **2.5m** | 18mm | **16mm** ← chosen |
| 3.0m | 22mm | 19mm |

The 16mm lens covers both — distance is what you adjust, not the lens.

- [ ] **16mm C-mount lens, fastest available** (f/1.4 preferred). Plan to shoot
      around f/2 — cheap CCTV glass is soft wide open.
- [ ] C-to-CS adapter (HQ cam is CS-mount; the 16mm is C-mount). Set back focus.
- [ ] **Camera at ~2.5m** from the scene plane. Confirm against the sizing rule
      once the bath is positioned.
- [ ] **Standard HQ camera, NOT NoIR.** Color accuracy is diagnostic for species
      ID and for iNat community review.
- [ ] **Setting focus:** prop something finely detailed — newspaper, a ruler, a
      leafy twig — at the chosen distance, focus live at full resolution, then
      lock the ring. Do this on the bench before sealing the box.
- [ ] **Bias focus slightly toward the nearer subject.** Depth of field extends
      further behind the focus point than in front, so focusing forward of centre
      actually centres the sharp zone.
- [ ] Focused at 2.5m, roughly **2.0–3.1m is sharp** at f/2.8 — DoF grows with
      distance, so all three zones fit comfortably with depth offsets.

**Why 88mm-equivalent beats a 6-inch feeder cam:** no perspective distortion
(wide-angle close-ups balloon the beak and sit outside the classifier's training
distribution), no behavioral effect on shy species, wider coverage than just the
feeder port, and the camera stays out of the seed-hull and droppings splash zone.

### Sensor and exposure
**IMX477 sensor modes** — note the sensor is **4:3**, not 16:9:

| Mode | Max fps | Notes |
|---|---|---|
| 4056×3040 (full, 12.3MP) | ~10 | Wider than 4K but fps-capped |
| **2028×1520 (2×2 binned)** | **~40** | ← chosen; ample headroom at 10fps |
| 2028×1080 | ~50 | Crops vertically |
| 1332×990 | ~120 | Too little resolution |

**Real frame at 2.5m: ~98cm wide × 74cm tall.**

- [ ] **Use the 2×2 binned 2028×1520 mode**, not full 4056×3040. Same field of
      view, ~2× better low-light SNR, faster readout (less rolling-shutter skew
      on wingbeats), manageable encode, and it halves the resolution demand on
      the lens so cheap glass performs better.
- [ ] **Cap exposure at 1/500s or faster.** Non-negotiable — everything else is
      wasted on motion blur.
- [ ] **Spend depth of field on shutter speed.** The small sensor gives ~85cm of
      DoF at f/2.8 and ~40cm at f/1.4; a perch needs ~15cm. Shoot wide.
- [ ] **Don't stop below ~f/4.** Diffraction starts costing real detail at the
      binned 3.1µm effective pixel pitch. f/2–2.8 is the sweet spot.
- [ ] **Turn denoising down or off.** High-ISO NR smears the fine feather detail
      that separates similar species. Noise is recoverable; lost detail isn't.

### Node board — DECIDED: Raspberry Pi 4
The node only captures, encodes, and publishes. On that job the Pi 4 beats the
Pi 5 on every axis that matters here:

- **Hardware H.264 encoder** → less CPU, less heat, less power. Heat matters
  twice: once for the sealed sunlit box, again for sensor noise, since a hot
  IMX477 next to a hot SoC is a noisier IMX477.
- **Standard 15-pin CSI connector** matches the stock HQ camera cable (Pi 5 needs
  the narrower 22-pin cable).
- Cheaper, and a lighter load on the Phase 6 solar budget.

### Settings to lock down
Each of these fails silently — you won't notice until you review a week of frames.

- [ ] **Lock the focus and iris rings** with set screws or thread locker once set.
      C-mount rings drift with vibration and thermal cycling.
- [ ] **Fixed white balance, not auto.** AWB shifts frame to frame, hurting both
      classification consistency and color fidelity for iNat. Set manual gains
      once against a grey card.
- [ ] **Fixed shutter, auto gain.** Cap exposure at 1/500s and let gain float. On
      full auto, the exposure algorithm will lengthen shutter in low light and
      quietly hand you blurred birds.

**Light budget** (f/2.8, ISO 100) — the real binding constraint:

| Conditions | Shutter achievable | Notes |
|---|---|---|
| Full sun | ~1/3200s | Trivial |
| Overcast | ~1/400s | ISO 200 |
| Canopy shade | — | ISO 400–800 for 1/500s |
| **Dawn / dusk** | — | **ISO 1600–3200. Peak bird activity.** |

Dawn/dusk is where this build strains. A fast lens buys ~1.5 usable stops back.

### Power and network topology — DECIDED: single PoE+ run
Everything runs off one Ethernet cable from the house. No separate power run.

```
House PoE+ switch/injector
    └── one Cat6 run
         └── PoE splitter (bird box)
              └── 12V bus
                   ├── buck converter → Pi 4 → HQ camera
                   │                        └── USB sound card → bird mic
                   └── (Phase 6: battery connects here instead)
                        
Bird box ── active USB extender ──> AudioMoth on bat mast
            (carries power + data)
```

**Load budget:**

| Item | Draw |
|---|---|
| Pi 4 (camera + HW encode) | 5–7W |
| HQ camera | ~1W |
| USB sound card + electret | ~0.5W |
| AudioMoth USB mic | ~0.5W |
| Active USB extender | ~0.5W |
| **Total** | **~8–10W** |

- [ ] **Use 802.3at (PoE+), not 802.3af.** af delivers ~12.95W at the device —
      enough, but only just. USB peripherals draw in bursts and you'll add things.
- [ ] **External PoE splitter to 12V — NOT the official PoE HAT.** The HAT outputs
      5V directly, which abandons the 12V bus and breaks the "identical node on
      PoE or solar" design. It also has a fan: a moving part, a noise source, and
      something wanting airflow a sealed box doesn't have.
- [ ] **Ethernet surge arrestor at building entry, and ground the mast.**
      Baton Rouge has among the highest lightning-strike density in the country,
      and this is copper running from the house to an elevated outdoor pole — a
      textbook surge path into your switch. Cheapest insurance in the build.

> Solar conversion (Phase 6) then becomes: unplug the splitter, connect the
> battery to the same 12V input. Nothing downstream changes.

### Future option: 25mm
Not needed now, but the C-mount makes it a ~2-minute, ~$30–250 swap later.

- At the same 2.5m: FOV tightens to ~47cm, cardinal ~710px tall. Richer image.
- Costs: DoF drops to ~35cm at f/2.8, jays and doves fill 70% of frame, and more
  frames get edge-clipped — which matters because Frigate deprioritizes frames
  where the object touches the edge, so you lose best-frame candidates.
- Moving *back* to 3.45m with a 25mm gains nothing — identical framing and DoF
  to 16mm at 2.5m. **Magnification is what matters, not focal length.**
- If buying: any C-mount lens rated 1/2" or larger covers the 7.9mm sensor
  diagonal. MP-rated machine vision glass (Computar, Kowa, Fujinon) meaningfully
  outperforms generic CCTV lenses, but binned mode narrows the gap.

### Frigate config — optimized for observation quality, not security
The usual Frigate advice is to run detection on a low-res substream to save CPU.
**That advice is backwards for this build** and will quietly destroy the thing
you care about.

- [ ] **Point the `detect` role at the high-resolution feed.** The detect stream
      is the only stream Frigate decodes, and it's the stream snapshots are
      generated from. There's no API parameter to force high-res snapshots, and
      the `record` stream is only copied, never decoded — so no snapshot can come
      from it. High-res detect is the only path. Let the mini PC work harder.
- [ ] If load is a problem, use the `detect` width/height params to downsize on
      the GPU rather than dropping to a low-res substream
- [ ] **Raise detect fps toward 10.** Frigate defaults to a recommended 5fps with
      10 as the practical max for fast-moving objects. Birds are fast and visits
      are short — at 5fps a brief landing yields only a handful of candidate
      frames to choose a best from.
- [ ] **Enable `clean_copy`.** Saves a second snapshot with no bounding box or
      timestamp overlay — exactly what an iNat upload needs.

### What Frigate gives you per bird
Useful to know before tuning anything:

- Frigate saves one "best" frame per tracked object, continuously scoring each
  frame against the previous best on detection confidence and object size, and
  deprioritizing frames where the object touches the frame edge. Rough photo
  selection is already handled.
- `/<camera>/<object>/best.jpg?crop=1` returns a full-resolution image cropped to
  the detection region — effectively an auto-generated, iNat-ready crop.

> Consequence: unidentified birds are not a failure mode, they're a submission
> queue. This raises the stakes on lens choice, since all of the above assumes
> the underlying frames are sharp.

---

## Phase 3 — Enclosure and mounting

*Goal: survive a year outdoors without opening it.*

### Enclosure
- [ ] IP66 ABS or polycarbonate box, ~200×150×100mm
- [ ] **Light gray or white.** Never black.
- [ ] **Gore-style breather vent plug** (M12, ~$8). Condensation, not rain, is
      the primary failure mode. This is the actual fix.
- [ ] Rechargeable silica desiccant as backup, not as the fix
- [ ] **All penetrations on the bottom face.** Cable glands sized to cable OD
      (PG7 = 3–6.5mm, PG9 = 4–8mm). Drip loops on every cable.
- [ ] **Sunshade** standing 20–30mm off the box, open sides for airflow.
      A box in sun hits 60–70°C and the Pi throttles hard.
- [ ] Fit **one extra gland now, blanked off**, for future expansion
- [ ] Size the box for a future XLR audio interface if you ever go that route

### Mounting
- [ ] **Rigidity is the requirement; concrete is just one way to get it.** At an
      88mm-equivalent focal length, angular shake is magnified — a mount that
      would pass with a wide lens will visibly soften frames, and wind wobble
      also generates false motion triggers and audio rumble.
      Ranked by how well they actually work:
      - Existing fence **post** — good. Cheap and quick.
      - Fence **rail or panel** — avoid. Panels flex noticeably in wind.
      - Mature tree trunk, mounted **low** — good. Sway increases with height.
      - Small or slender tree — weakest option. Young trees move a lot, and
        trunk growth will shift your aim over a season.
      - Dedicated post set in concrete — best, if you want it permanent.
- [ ] Whatever you choose, push on it hard. If you can make it move by hand, the
      wind will move it more.
- [ ] **Single enclosure — camera and Pi together, aimed as one unit** on an
      adjustable bracket.
      ⚠️ *This reverses earlier guidance.* "Mount the camera separately" assumed a
      commercial IP camera and does not survive the switch to a Pi camera module:
      the CSI ribbon isn't weatherproof, dislikes distance and flexing, the HQ
      camera board would need its own sealed housing, and flat ribbon through a
      round gland is miserable to seal. One set of seals beats two.
- [ ] Conduit or armored sheath within squirrel reach

### Camera window
Required by the single-enclosure decision — the lens now shoots through the box.

- [ ] **Optical acrylic or glass**, not whatever plastic is on hand
- [ ] **Lens front as close to the window as possible.** Single biggest factor in
      killing internal reflections.
- [ ] Black flocking or felt around the lens barrel
- [ ] External hood over the window for flare and rain — separate from the box
      sunshade
- [ ] Interior fogging is already handled by the Gore vent

### Aiming
- [ ] **Face north** (northern hemisphere). Sun behind the camera, never in frame.
- [ ] **Perch lit, background shaded.** This is the money shot setup: subject in
      a pool of sky light, background in shadow 1–2m behind. Gives both correct
      exposure on the bird and maximum contrast for the detector.
- [ ] **Background 1–2m behind the perch**, static and dark. A fence board or
      dense shrub. Never sky — it blows out exposure and silhouettes the bird.
- [ ] **Add a dedicated perch branch** just outside the feeder. Birds stage there
      and you get clean side profiles at a predictable distance. Biggest single
      accuracy win available.
- [ ] **Do not co-locate an IR illuminator with the lens.** It attracts insects,
      which attract spiders, which web across the lens nightly. Separate bracket
      a meter away, or skip IR.
- [ ] Seal well — wasps love a warm enclosure

---

## Phase 4 — Bird audio

- [ ] Dedicated mic, **not** the camera's built-in one (AGC and noise suppression
      mangle exactly the frequencies BirdNET needs)
- [ ] **Mono.** Stereo introduces phase errors that reduce accuracy.
- [ ] Capsule: PUI Audio AOM-5024L-HD-R is the community favorite
- [ ] Shielded mic cable, under 10m
- [ ] **Housing:** element pointing *down* inside a PVC elbow or cup, acoustic
      mesh over the opening, foam windscreen on the capsule
- [ ] **Fur "dead cat" over the foam.** Wind is the dominant noise source.
- [ ] Soft, non-resonant mount — rain drumming on a rigid housing is noise source #2
- [ ] **Confirm the USB sound card supplies plug-in power.** The AOM-5024L is an
      electret and needs bias voltage; not every cheap dongle provides it. Verify
      *before* the box is sealed.
- [ ] **Standoff arm, away from the enclosure body** and especially the sunshade.
      Flat panels resonate and reflect.
- [ ] **Aim for general yard coverage, not at the feeder.** BirdNET wants broad
      soundscape; the feeder itself is mostly wing-flap and seed-rattle.
- [ ] **Publish audio as its own mono RTSP stream**, separate from video. Sidesteps
      stereo channel-selection entirely and keeps BirdNET-Go independent of Frigate.

> Note: this windscreen advice is **bird-only**. See Phase 5 for why it inverts.

---

## Phase 5 — Ultrasonic channel: bats + orthoptera

*Goal: second acoustic stream, high sample rate, own mast.*

### Hardware
- [ ] **AudioMoth USB Microphone** — up to 384kHz, no phantom power, plain USB
      audio device. Chosen for spectrum coverage and simple power.
- [ ] Not weatherproof out of the box. Housing is your build.
- [ ] Own mast, 3–5m up

**Connection — DECIDED: active USB extender back to the bird box.**
The AudioMoth stays a dumb USB device with no computer on the mast. One cable
carries both its power and its data, and the bird box's Pi sees it as a locally
attached mic. Simpler than the alternative, with nothing extra to power or
maintain outdoors.

- [ ] **Active USB extender**, good to ~10–15m (USB 2.0 passive tops out ~5m)
- [ ] **Shielded cable, in its own conduit.** The bird box contains a buck
      converter and, later, a solar charge controller — both radiate into the
      20–100kHz band, and an unshielded USB run is an antenna pointed straight at
      the mic you're trying to keep quiet. Do not zip-tie it to the 12V run.
- [ ] *Fallback only if the mast exceeds extender range:* Pi Zero 2 W publishing
      RTSP over Ethernet, which is distance-indifferent. Adds a second outdoor
      computer — avoid unless geometry forces it.

### Weatherproofing — inverts the Phase 4 rules
- [ ] **No foam, no fur.** Any membrane attenuates hard above 20kHz.
- [ ] Element pointing down or sideways under a rain cap with an **open air gap**,
      not a sealed window
- [ ] Fine hydrophobic acoustic mesh only, accepting a few dB loss
- [ ] Treat the capsule as a **consumable** — plan on periodic cleaning/replacement

### Placement
- [ ] Aim at a **linear feature**: treeline, hedgerow, canopy gap, water margin.
      Bats commute along edges rather than crossing open ground.
- [ ] Clear of walls and dense foliage within ~2m — hard surfaces throw echoes
- [ ] **Keep away from your own electronics.** Switching regulators, solar charge
      controllers, some LED drivers and PIR sensors all radiate into 20–100kHz.
      This is why it gets its own mast.

### Stream config
- [ ] **Raw PCM or FLAC only.** Lossy codecs (AAC, Opus, MP3) destroy ultrasonic
      content even at a high sample rate.
- [ ] Bandwidth: 384kHz × 16-bit mono ≈ 6.1 Mbps continuous. FLAC won't help much —
      an ultrasonic noise floor compresses poorly.
- [ ] **Duty-cycle dusk→dawn via cron on the publishing Pi**, not the receiver.
      Roughly halves bandwidth, radio-on time, and battery draw at no real cost.
- [ ] **Verify the rate end to end.** BirdNET-Go advertises up to 256kHz for bats;
      release notes describe a 384kHz community feed working. Both can be true if
      it resamples — confirm with the **Test Stream** button, which probes and
      shows sample rate, codec, and a bat-compatibility badge.

### Orthoptera
Katydids and bush crickets are extremely loud in the 20–60kHz band and will be
your dominant bat false positive. Since you want them anyway, this becomes a
feature.

- [ ] Tune per-classifier bat false-positive levels first
- [ ] Later: BirdNET-Go supports **custom TFLite classifiers** — a dedicated
      orthoptera model is a plausible future project

---

## Phase 6 — Solar / wifi conversion

*Goal: make the nodes relocatable. Deliberately last, so it's sized against
**measured** load rather than estimated load.*

- [ ] Measure actual draw of the finished camera node and ultrasonic mast over a
      full 24h cycle, including the dusk→dawn bat window
- [ ] Ballpark placeholder until then: 5W continuous ≈ 120Wh/day → ~100W panel,
      ~40Ah LiFePO4. **Expect the real number to be higher** once the nocturnal
      ultrasonic load is included.
- [ ] **BMS with low-temperature charge cutoff.** LiFePO4 takes permanent damage
      if charged below 0°C. Non-negotiable.
- [ ] Battery in its own insulated box at ground level — thermal mass helps
- [ ] Panel and camera want opposite things (sun vs shade). Mount separately.
- [ ] Two masts now means two power problems. Decide whether the ultrasonic mast
      gets its own small panel/battery or a buried 12V run from the main node.

---

## Phase 7 — Post-processing

Deliberately deferred. Nothing here affects earlier phases.

- [ ] iNaturalist submission pipeline — feed from `best.jpg?crop=1` plus the
      clean copy; unidentified birds go to the community for ID
- [ ] ⚠️ **Subscribe to event *updates*, not just new events.** `sub_label` is
      added by classification after the initial detection fires. A pipeline that
      only reacts to new events will never see a species label. Confirmed on the
      bench in pass 11.
- [ ] Merlin integration
- [ ] Custom Frigate classifier fine-tuned on local species
- [ ] Cross-model consensus (BirdNET v2.4 + Perch v2 agreement scoring)

---

## Phase 8 — Runbook

*Goal: a standalone, portable rebuild document. Separate deliverable from this
plan.*

**Repo: https://github.com/cmbankester/wildlife**

**This plan records *why*. The runbook records *how*.** Someone (including
future-you on new hardware) should be able to rebuild the whole stack from the
runbook alone, without reading the reasoning.

Elevated in priority because compute lives on a work machine — porting is
plausible, not hypothetical.

### Don't commit
- [ ] Video fixtures — hundreds of MB, and **`birds.mov` carries GPS metadata
      with your home coordinates**. Gitignore media; document how to regenerate
      fixtures from source instead.
- [ ] `frigate.db`, `model_cache/`, BirdNET-Go database — runtime state, not config
- [ ] Any `.env` with credentials. Commit `.env.example`.

### Contents
- [ ] Prerequisites — Intel iGPU, `render` group membership, `vainfo` check,
      Docker + compose
- [ ] Full `docker-compose.yml`, `config.yml`, `mosquitto.conf`, verbatim
- [ ] Bring-up sequence in dependency order, with the verification command at
      each step
- [ ] BirdNET-Go UI configuration steps (location, sources, models, MQTT)
- [ ] **Known gotchas**, lifted from pass 11 — auto-detected hwaccel,
      `detectors`/`model` pairing, file-direct vs RTSP, `shm_size`
- [ ] Backup and restore: what state matters (media, BirdNET DB, `model_cache`,
      Frigate DB) and what's disposable
- [ ] Acceptance tests — inference ms, detect/sec, an MQTT event with `sub_label`
- [ ] Network requirements, including the one-time internet access for the
      classification model download

### Build it when
After Phase 2 is stable on real camera input. Writing it against bench fixtures
would bake in file-direct paths and bench-specific masks that don't apply to the
deployed system.

- [ ] Keep it in version control alongside the config files
- [ ] Test it by actually rebuilding somewhere — an untested runbook is a guess

---

## Open questions for the next pass

Roughly in the order they'll block progress.

1. **Motion masking against the real camera.** detect CPU hit 154% from wind.
   No longer blocks a purchase, but still the difference between a tidy system
   and a wasteful one — and it determines sizing if compute ever moves. Bench
   masks don't transfer (frame is 2.7× wider).
2. **VA-API on Alder Lake** — failed on the bench, but against a corrupt stream,
   so unproven either way. Retest in Phase 2. Matters because the N100 uses the
   same decode path and offloading decode keeps CPU free for audio models.
3. **ffmpeg RTSP publish commands** — video, bird audio, and the dusk/dawn cron
   scheduling for the ultrasonic stream. Next working session.
4. **Network segmentation** — VLAN or firewall rules to keep the node off the
   internet. ⚠️ Must allow Frigate one-time internet access first, to download the
   bird classification model.
5. **Semantic search?** No longer a purchase blocker — evaluate on the existing
   workstation whenever curiosity strikes.
6. **Lens sourcing** — confirm a 16mm f/1.4 C-mount with acceptable sharpness at
   f/2 before committing. Cheap CCTV glass varies wildly unit to unit.
7. **Solar geometry and sizing.** Genuinely last — downstream of measured load,
   and the phase swap turned this from a guess into a measurement.

*Closed in pass 7:* MQTT broker (yes, Mosquitto). *Storage and retention were
also marked closed in pass 7 but reopened and re-closed in pass 14* — the key
was wrong for 0.17 and the real lever is `alerts`/`detections` retention.

---

## Parts list

*To be filled in on a later pass, once camera selection is settled.*

| Item | Purpose | Phase | Chosen? |
|------|---------|-------|---------|
| Existing Ubuntu workstation | Inference host — **no purchase** | 1 | ☑ decided |
| Mosquitto (container) | MQTT broker / integration seam | 1 | ☑ decided |
| Raspberry Pi 4 | Camera node — HW H.264 encode | 2 | ☑ decided |
| PoE+ splitter → 12V | Node power | 2 | ☑ decided |
| Buck converter 12V→5V | Pi supply | 2 | ☐ |
| Ethernet surge arrestor | Lightning protection | 2 | ☐ |
| Optical acrylic/glass window | Enclosure port | 3 | ☐ |
| Pi HQ Camera, IR-filtered | Sensor — **not NoIR** | 2 | ☑ decided |
| 16mm C-mount lens, f/1.4 | Optics | 2 | ☑ decided (sourcing open) |
| C-to-CS adapter | Back focus | 2 | ☐ |
| IP66 enclosure ~200×150×100 | — | 3 | ☐ |
| M12 breather vent plug | Condensation | 3 | ☐ |
| Cable glands PG7/PG9 | — | 3 | ☐ |
| PUI AOM-5024L-HD-R | Bird mic capsule | 4 | ☐ |
| USB sound card (CM108 class) | Bird mic input | 4 | ☐ |
| AudioMoth USB Microphone | Ultrasonic | 5 | ☐ |
| Active USB extender, shielded | AudioMoth → bird box | 5 | ☑ decided |
| Solar panel | — | 6 | ☐ **sizing open** |
| LiFePO4 + low-temp-cutoff BMS | — | 6 | ☐ |
