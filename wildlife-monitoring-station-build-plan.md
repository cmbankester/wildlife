# Backyard Wildlife Monitoring Station — Build Plan

**Status:** 🔨 Phase 3 — enclosure build started — Pass 29
**Last updated:** 2026-10-01

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
| 15 | 2026-09-04 | **Camera node live; the Pi 4 encoder ceiling is now measured.** Detect input moved to `rtsp://wildlife-pi:8554/feeder`. ⚠️ **The hardware H.264 encoder has two limits and only advertises one.** `v4l2-ctl` reports `Stepwise 32x32 - 1920x1920`, but the firmware also enforces **8192 macroblocks** (H.264 L4.1), stated nowhere and surfacing only as `encoder_create(): unable to activate output stream`. 1920x1440 (10800 MB) **fails**; 1664x1248 (8112 MB) is the ceiling. **2028x1520 is 12065 MB and cannot be hardware-encoded on a Pi 4 at all** — so locked decisions #4 (Pi 4 *for* its hardware encoder) and #6 (high-res detect, the snapshot is the deliverable) are in direct conflict, now with numbers: 2.08 MP available against 3.08 MP designed for, 68%. Sensor mode is correct and unaffected (`2028:1520:10:P`); the loss is one downscale step before encode. MJPEG is the open route that keeps both decisions. Also: **the bench motion mask was suppressing detection entirely** — 44% of a differently-shaped frame, `detection_fps` 0.0 with it, 8.2 without; removed, redraw against the real scene. **Open question #2 closed** — VA-API decodes real camera input clean (7.72ms, 10.0 process_fps, zero skipped); pass 11's failure was the corrupt out-of-band publisher, as suspected. Recording restored with `alerts`/`detections` at 30 d. |
| 16 | 2026-09-10 | **The encoder is the only bottleneck — the ISP goes to 16384×16384.** So skipping the encoder removes the 1920 cap entirely, which opens two routes to full-MP capture, now written up as an open decision in Phase 2. Route A: MJPEG 1920×1440, config-only, intra-only (no inter-frame generation loss), fits the measured ~100 Mbps wifi, recording still works via a secondary path — but it is **unverified** whether the 8192-macroblock cap applies to JPEG. Route B: full-res RAM ring buffer with retroactive fetch on Frigate events. ⚠️ **Disk is the wrong medium for Route B — endurance, not bandwidth:** 185 MB/s = 15.98 TB/day would kill a 128 GB SSD in 4–6 days. RAM fits: ~1000 MB = 5.4 s of 4056×3040 against ~1.3 s detection latency. Cost is a custom libcamera app (the camera is exclusive, so one process must stream *and* buffer), and it abandons 2×2 binning — worse dawn/dusk noise at peak bird activity — while the lens likely cannot resolve 1.55 µm pixels anyway. ⚠️ **Frigate silently adds the `record` role** if no input declares it (observed: config said `[detect]`, runtime said `["record","detect"]`) — in a raw pipeline that would attach recording to 46 MB/s and write 166 GB/hour, so raw configs must declare roles explicitly. Measured on the node: 2 GB RAM (not 4/8), USB3 SSD 269 MB/s write, wifi ~100 Mbps sustained while streaming, hardware JPEG encoder present at `/dev/video31`. **Open question #2 (VA-API) closed in pass 15**; the workstation `mediamtx` container is now dead weight since the Pi publishes its own. |
| 17 | 2026-09-10 | **Route A is live — MJPEG 1920×1440.** The 8192-macroblock cap is H.264-only; JPEG's 8×8 MCUs are exempt, so 2.76 MP now streams where H.264 capped at 2.08. **Bandwidth 15.3 Mbps / 6.4 GB/hour measured** against H.264's 14 Mbps / 5.9 — 33% more pixels for ~8% more bandwidth, so the storage objection to MJPEG was wrong by 3–4×. VA-API hardware-decodes MJPEG on Alder Lake; `preset-vaapi` stays valid at 6.24ms inference, zero skipped frames. Wifi measured at ~100 Mbps sustained while streaming, so MJPEG fits wireless with room. ⚠️ **MJPEG recording unproven** — segments mux correctly (18.9 MB/10s in `/tmp/cache`) but none promoted to `recordings/`, because no review segment has existed to retain one. ⚠️ **The lens test was invalid**: full-res and binned crops of the same scene are indistinguishable, both focus-limited, and bytes/pixel *falls* as resolution rises (0.1805 → 0.1625 → 0.1576) — the extra pixels mostly interpolate. Camera was through a window at a distant roof, focused ~2 m, at Lux 6035. Redo at ~2.5 m, focused, near f/2. Also corrected: snapshots are **not** higher-res than the stream — the 2028×1520 files date from the fixture era, so snapshots do come from the detect stream and Route B's rationale is unaffected. ⚠️ **Nothing has validated the live path end to end** — all 500 events predate the camera going live on 09-04; zero detections since, expected with `objects.track: [bird]` on an out-of-focus indoor lawn. |
| 18 | 2026-09-10 | **The aperture ring delivers 0.48 stops per marked stop** — measured, both steps independently, spread 0–1 pixel value on steps of 27. The whole ring is worth ~1 stop, not 2. A light-leak model does not fit, so this is iris under-travel or misaligned engraving, not stray light. **Sit at the 2.8 marking**: it costs ~1 stop from wide open rather than the 2 implied, while still closing the iris 1.4× in diameter — enough to work on the chromatic aberration visible on this lens. ⚠️ **Absolute f-number remains unknown** (ratios only): if 1.4 is honest, marked 2.8 is ≈f/1.95; if 2.8 is honest, wide open is ≈f/2.0. Measure the entrance pupil to settle it — 11.4mm is a true f/1.4 at 16mm — because it changes the sourcing decision and the dawn/dusk margin. The light budget table is annotated accordingly. **Method matters and is recorded**: three auto-exposure attempts were confounded first — focus changed mid-test, then a target 5cm away that the camera shadowed until the AEC railed (identical `ExposureTime=66654`/`AnalogueGain=7.876923` at every aperture, the ~8× analogue cap), then flicker from freshly-lit mains at ~30ms exposures. The method that works: fix shutter and gain to kill the AEC, flat evenly-lit target deliberately defocused so reframing stops mattering, shutter in multiples of 8333µs for 120Hz mains, measure the central 50%, and ⚠️ **calibrate the tone curve rather than assuming gamma** — a shutter ladder at fixed aperture gave 0/−0.415/−1/−2 stops → means 154/131/97/52, whose fitted exponent drifts 0.56→0.67→0.78. Also captured: a focus check at the current setting shows detail density up 35% (0.1576 → 0.2127 bytes/px) but **veiling glare off the house window now dominates**, and at 1920×1440 each pixel carries more information than at 4056×3040 — a lens-limited system, which argues for settling the optics before building anything to move more pixels. |
| 19 | 2026-09-10 | **Phase 3 started. Camera window decided: 100×100×1mm double-side-polished fused quartz in a side wall.** Better than the "optical acrylic or glass" originally specified. Costs **0.1 stops** — the ">83% over 190–2500nm" spec is a broadband minimum dragged down at the UV/IR ends; in-band it is ~93%, just Fresnel loss — and shifts focus 0.33mm, inside DoF at f/2. ⚠️ **The real risk is thermal expansion, not optics:** quartz is 0.55×10⁻⁶/K against ~80 for ABS/PC, ~150× mismatch, giving ~0.6mm differential across a 100mm pane over a 75°C swing. **Silicone, never epoxy; no screw bearing on the pane.** Uncoated, so 8% reflects back into the box and **flocking is no longer optional**. **The transparent front lid is rejected** — tinted and visibly warped, edges swim when moved across a scene, which is the right quick test for waviness and disqualifying on its own. But it remains a light path: a clear front floods the interior and returns glare through the lens, so ⚠️ **cover it from the outside** (white), not blacked inside, because a clear lid admits solar load and absorbing it internally traps heat against this plan's own 60–70°C figure. **Window moves to a side wall**, which puts the optical axis along the box's longest dimension and dissolves the standoff problem. **Hole size is calculable**: at 16mm with the IMX477's 7.857mm diagonal the half-field is 13.8°, so `hole ≥ front element + 0.49 × d` where d includes wall thickness — **31.2mm** with the measured geometry — front element ~27mm, lens lip 3.5mm deep at 38mm OD, wall 3.0mm confirmed, quartz 1mm, 1mm air gap — so a **1⅜" (34.9mm) saw**. ⚠️ The lip does not vignette (built-in hood) but it is the frontmost surface, so it puts a ~4mm floor under "lens as close to the window as possible" and that distance propagates into the hole. Lip measures 38mm OD / 36mm ID — a 1mm-thick rim, so **not** usable as a bearing surface or baffle: a 1⅜" hole leaves only 1.54mm of land and the lip bore is wider than the hole. Spill light is controlled by flocking on the barrel and interior instead, which is also the only option that does not press on 1mm quartz. Vignetting check closed: 36mm bore against 28.7mm required, 3.7mm clearance per side. Added a **build order** (measure the assembly first, dry fit with zero drilling, drill last — the camera is constrained and the hole is not, so the camera decides) and ⚠️ **camera mounts on an L-bracket shelf off the vertical backboard**, sitting on its base with the tripod screw running up. Bolting it flat to the vertical board instead would put the screw on a horizontal axis with the lens cantilevered sideways, so **gravity applies a constant torque about the screw** — a static load resisted only by friction, failing with the lens swung to vertical. The shelf converts that torque into a normal force. ⚠️ The **camera** sits on the shelf, not the lens: the barrel underside is 12mm above the mount plane, so resting the barrel would put the axis at 19mm rather than 31mm and misplace the hole by 12mm. A shelf also keeps `d`, and therefore the hole, small. **Assembly measured with the adapter fitted: 63.5mm from the tripod-screw centre to the lip tip, optical axis 31.0mm above the mount plane** — which fully specifies the bracket (flat surface 31mm below the axis, screw 64.5mm back from the pane). Focus travel is only ~0.1mm across 2.0–2.5m so it does not eat the 1mm air gap. ⚠️ **The tripod thread is a single fastener on a vertical axis and yaws on friction alone: 1.68° consumes the entire 1.86mm lateral margin and vignettes**, and perpendicularity to the pane goes well before that — so it needs locating pins, and a padded saddle under the 38mm barrel to take 63.5mm of lens overhang off one screw. Ribbon length confirmed **not** a constraint; the chosen wall is flat with just over 100mm of clear area, so the 100mm pane fits with only a few mm for the bead. |
| 20 | 2026-09-10 | **Enclosure measured — 225 × 325 × 115mm internal**, notably larger than the ~200×150×100 originally specified, so the window geometry resolves comfortably. Optical axis runs along the width, out a side wall whose flat area is 115 × 325. **Every placement figure is now a number:** hole centre 57.5mm from the back wall, 7.5mm bead margin per side, camera 46.0mm out along the shelf from the backboard face (board standing ~11.5mm off the back wall), screw 64.5mm from the window wall. The pane's rear edge tucks **4mm behind the backboard plane**, which the gap around the removable board accommodates — so **the pane goes in first with the board out**, giving access to both wall faces for bedding and squeeze-out. ⚠️ **The front edge is the lid's sealing surface**: verify whether the 115mm reaches the gasket or stops short, because silicone on a sealing face costs IP66 on a box meant to stay shut a year. Considered and rejected shifting the pane forward to clear the backboard — buys 4mm at the back, costs 4mm at the gasket. **Camera mounts low**, for mounting flexibility *and* because ⚠️ heat rises: Pi, SSD and buck converter above the camera means convection carries their heat away from the sensor rather than past it, which matters against a dawn/dusk noise budget already strained. Floor is **65.5mm axis height** (corner radius, assumed 8mm and to be verified, + bead margin + half pane), leaving ~210mm of backboard above for electronics. Earlier "pane margin is thin" note superseded — it assumed 105mm. **Parts in hand:** 2× AOM-5024L-HD-R (one spare), a **UGREEN USB-to-3.5mm TRRS adapter** (24bit/96k — plug-in power is probably inherent, since a TRRS headset jack must bias the electret mics headsets use, the same part class as the AOM-5024L; ⚠️ but **it needs a TRRS plug, not TRS** — a TRS sleeve bridges Ring 2 and Sleeve and shorts the mic to ground, failing silently — and the mic path bandwidth is unspecified and worth measuring, since headset inputs are voice-optimised and BirdNET needs clean response past 8kHz), and an AudioMoth USB mic with its purpose-made case, which has an open port at the element and therefore **suits** the Phase 5 rule rather than conflicting with it. |
| 21 | 2026-09-14 | **The camera node's config is now in the repo** (`camera-node/`), after a failure that took four hours to diagnose and would have taken ten minutes if it had been. The Pi appeared not to boot — solid green LED, then an uncountable flicker, no SSH. ⚠️ **It was booting fine.** cloud-init ran to completion twice with zero module failures; the flicker was ordinary disk activity, not an error code, and error codes are slow and deliberate with a pause before repeating. What had failed was networking: `/etc/NetworkManager/system-connections/` **emptied** and both `/etc/netplan/90-NM-*.yaml` **truncated to 0 bytes**, all at 2026-09-10 13:01 — eleven minutes after the last good SSH session. Not cloud-init (no log activity then), not apt (zero dpkg entries that day), not the SSD (enumerated clean, filesystem intact, 4% full). Cause undetermined; it coincided with the camera being physically removed. **Recovery method worth reusing:** pull the USB SSD, mount it on the workstation **read-only with `norecovery`** via `udisksctl` (unprivileged, no writes), recover config first, diagnose second. **Ethernet restored it with no configuration at all** — `/lib/netplan/00-network-manager-all.yaml` survived because it is in `/lib` not `/etc`, and NetworkManager auto-generates a wired profile on carrier. **Decision: the node is wired.** That is the Phase 2 design rather than a fallback, since the locked PoE+ topology means a deployed node has an Ethernet cable by definition; it also gives 0.29ms latency and reopens the raw-video option that wifi's ~100 Mbps ceiling had ruled out. ⚠️ **No wifi profile now exists** — restoring it needs `nmcli device wifi connect` with credentials still present in `/boot/firmware/network-config`, and Phase 6 will need it when nodes become relocatable. Note the node's address changed from .133 to .131 when it moved to Ethernet; DHCP reservations on both MACs would stop the hostname flapping. |
| 22 | 2026-09-14 | **Bird mic chain tested end to end and it works.** AOM-5024L-HD-R on a TRRS plug into the UGREEN adapter, on the Pi. Enumerates as a real capture device (`KT USB Audio`, KTMicro) — the "DAC" naming was misleading — S16_LE **mono** at 44.1/48kHz, so 48k and mono are both available and both are what this plan wants. **Plug-in power is present** and **CTIA was the right pinout**; neither the OMTP swap nor the mic/ground swap was needed. Ambient floor −32 dB mean, −16 dB peak. **No AGC** — the keys test clipped at 0.0 dB, which an AGC would have prevented, so the path is linear. ⚠️ Capture gain sits at 100% and clipped on a loud close source; birds at 2.5m will be far quieter, but check once deployed. **Bandwidth, the figure on no spec sheet: flat from 4kHz to 20kHz**, rolling off only at Nyquist, with the **peak at 4–8kHz where BirdNET's diagnostic energy sits**. The voice-tuned rolloff Phase 4 feared is simply absent. Method caveat recorded: this measures the whole chain against a keys source, so it does not separate mic response from source spectrum — but content *reaching* 20kHz proves nothing filters it out. ⚠️ **The listening test caught what measurement could not:** clean with no crackle (solder joints sound), slight hum attributable to a room water pump rather than a TRRS ground fault, and faint speech **intelligible underneath loud keys** — which is better validation than any number here, since it demonstrates real dynamic range, no AGC pumping, and enough sensitivity to resolve a quiet distant source against a loud near one. ⚠️ **Remaining Phase 4 work: the mic is on the Pi and BirdNET-Go is on the workstation.** Bridge it as this plan already specifies — audio as its own mono RTSP stream, separate from video, via the MediaMTX already running on the node — then re-enable the source disabled in `3dbc1e2`. |
| 23 | 2026-09-15 | **Audio runs end to end: mic → Pi → RTSP → BirdNET-Go.** LPCM 48kHz over the node's MediaMTX, `channelMode: left` on the consumer. ⚠️ Three findings worth not rediscovering. **The UGREEN adapter only enumerates with a plug inserted** — pull the TRRS and it vanishes from USB entirely, so a mic unplugged in the field takes the whole audio device with it, the plug must be present at boot, and "measure the adapter alone" is impossible. **`plughw:Audio,0`, by name and via the plug layer** — card numbers shift on reboot, and the raw `hw:` device rejects ffmpeg's period size even though `arecord` accepts it. **Configure BirdNET-Go in its web UI**, which Phase 1 already said and I ignored: `rtsp.streams` takes structs (`name`/`url`/`enabled`/`type`/`transport`/`channelMode`/`gain`/`quietHours`/`models`), not URL strings, and hand-writing one crash-looped the container. The stream reports 2 channels despite `-ac 1`, but L−R measures −91 dB against −39 dB, so it is duplicated mono and `channelMode: left` recovers it exactly. **60 Hz hum investigated and closed at ~−58 dB.** ⚠️ **It is electrical, not acoustic** — muffling the capsule removed 10 dB above 1kHz, proving the test worked, while 60 Hz moved 0.3 dB; a similar-pitched hum is audible in the room from the workstation but is not what is in the recording. Only clipping the exposed L/R leads helped (−2.9 dB); earthing the Pi did nothing; and ⚠️ **an ungrounded static shield bag made it 3 dB worse** — a large floating conductor intercepts the field and, having nowhere to drain it, couples it into the high-impedance mic conductor. Grounding the bag only undid that harm. Not pursued further: BirdNET works above 1kHz where it contributes nothing, a disabled 100 Hz HighPass removes it from analysis, and the deployed mic sits metres from the workstation rather than feet. Shielded cable remains the right fix. ⚠️ Also logged: `processing time exceeded buffer interval` twice on first run — watch it once the camera returns, since Phase 1's load model assumes GPU video and CPU audio do not contend. |

| 24 | 2026-09-17 | **Camera mount hardware in hand, and the barrel saddle is removed from the plan.** The shelf is **0.75" (19.05mm) stock with a ~76mm (3") slot** routed along the optical axis, so the camera's fore/aft position is adjustable rather than drilled once — which turns the 25mm lens upgrade into a slide instead of a second hole in a shelf built around a 34.9mm aperture. ⚠️ **The saddle's stated job does not exist.** At ~135g with the centre of mass ~29mm ahead of the screw, the nose-down moment about the camera body's front edge is ~0.013 N·m and needs **~0.7N of screw tension**, against the kilonewton-scale preload a hand-tight ¼"-20 develops — three orders of magnitude of margin, and the shelf already carries most of the weight in compression. **Anti-yaw hardware is deferred, not replaced:** a fence or saddle would fight a possible motorised stage for distance and yaw, and the yaw joint stays adjustable through one screw with vignetting directly visible in the image as the check. The 1.68° budget stands. ⚠️ **Screw length is set by the shelf, and 1.5" bottoms out** — 38.1mm of thread entering a ~5mm tripod bush, which reads as "loose no matter how tight" and can push the bush out of the housing. **1" with exactly one washer** puts engagement at 4.75mm, so the washer is dimensional rather than optional. ⚠️ **The 0.75" shelf drops the bracket arm to ~15mm off the floor** (34mm surface − 19.05mm stock) — confirm the backboard reaches that low and that the arm clears the bottom face and the glands. Pi fasteners: a **100pc brass M2.5 kit**, using 11+6 M/F standoffs, nuts and M2.5×5 screws; brass over nylon because the box runs 60–70°C where nylon creeps under load. ⚠️ Check continuity between a Pi corner hole and a header GND pin before metal standoffs touch anything conductive — an accidental chassis bond is expensive next to a high-impedance mic input. |

| 25 | 2026-09-21 | **The node is back on the designed power chain and it holds: PoE → surge arrestor → splitter → buck → Pi 4.** `throttled=0x0` before, during and after a sustained 4.2 GB write at **271 MB/s** with the camera streaming, ARM pinned at 1800 MHz throughout, no undervoltage in `dmesg` or `in0_lcrit_alarm`, one clean boot. The SSD matches pass 16's 269 MB/s, so nothing degraded through the splitter and converter. ⚠️ **`0x0` only means the rail never fell below ~4.63V, not that it sits at 5.1V** — a converter set to 4.8V passes this test with no reserve, so a meter at the USB-C under load is still owed. **Gigabit survived the new path** (`1Gbps/Full`, flow control), which is not automatic: many cheap PoE splitters and Ethernet arrestors pass two pairs and force 100 Mbps, and pass 21's claim that going wired reopens raw video depends on this. Camera confirmed genuinely live rather than a stuck stream — luminance 15.3684 / 15.3711 / 15.3681 across three frames, jittering because the AEC rails to maximum gain against a capped lens. ⚠️ **The finding that matters is thermal, and it is a new open question.** 63.7°C mean and 65.2°C peak under load at **22.2°C ambient** is a **41.5°C rise**, entirely passive with no cooling device registered. That puts the ceiling for an unthrottled Pi at about **38°C ambient**, against this plan's own **60–70°C** figure for a sealed box in sun — a 25–30°C gap, so the failure is continuous hard throttling at 85°C rather than a lost margin. A fan is ruled out twice over: no airflow in IP66, and the PoE HAT was rejected partly for having one. That leaves conduction, and ABS runs ~0.17 W/m·K, so the shell is not a radiator without a metal path through the wall — which then conducts solar heat inward and complicates the seal. ⚠️ **The 60–70°C figure has never been measured**, so log the empty box in place before designing cooling against an assumption. Also corrected: the Phase 2 load budget omitted the USB3 SSD entirely, since the table predates pass 16. Audio is down for the expected reason — cable unplugged pending the shielded re-solder, `lsusb` shows no audio device at all, exactly pass 23's adapter behaviour and not a regression. Frigate's hostname resolution failed until 14:41:05 and self-healed when the Pi's DHCP lease returned, which is pass 21's unresolved reservation item resurfacing. Minor and unexplained: the feeder path now advertises `Stream #0:1: Data: none`, harmless while Frigate decodes and records normally. |

| 26 | 2026-09-22 | **Window hole resized from 1⅜" to 2" (50.8mm)**, so future lenses do not mean re-drilling a wall the pane is already bedded to. ⚠️ **Longer lenses need *smaller* holes, not bigger** — the half-field angle shrinks with focal length, so the `0.49 × d` cone term collapses and the hole is set almost entirely by front element diameter. Across the realistic C-mount range at d=8.5mm: 8mm needs 38.3mm, 12mm 35.6mm, 16mm 31.2mm (current), 25mm 32.7mm, and even a fat 50mm f/0.95 only 46.3mm. **2" covers every one**, and costs little — bead land on the pane falls from 32.6mm to 24.6mm per side against a 7.5mm budget, and wall land stays 32.1mm per side of a 115mm face. **A ~90mm aperture, nearly as wide as the pane, was considered and rejected:** the silicone bead is the pane's entire mount, so ~5mm of land per side removes the mount, the ~1mm setting blocks have nowhere to sit, and plate deflection scales with span⁴ — about 44× more on a 1mm plate, which is a hail question rather than a wind one. ⚠️ **A swappable mask taped to the inner face of the glass was rejected with it:** adhesive at 60–70°C creeps and outgasses onto the coldest surface in the box, which is the window, and felt against glass wicks the condensation a breather-vented enclosure will produce. **The same idea belongs on the barrel instead** — a slip-on flocked baffle tube, sized per lens, swapping with the lens, touching nothing, and blocking off-axis light along its whole length rather than at a single plane. Logged as an idea for the flocking stage, not specified. ⚠️ **The bigger hole spends glare margin:** at 34.9mm the hole was a shallow hood over a 31.2mm cone, at 50.8mm it is wide open, so more oblique light reaches an uncoated pane on a system where pass 18 already found veiling glare dominant. The barrel baffle is what pays that back. **Knock-on, and it is large: lateral margin goes 1.86mm → 9.80mm, so the yaw budget goes 1.68° → 8.78°** — a 5.2× loosening that strongly vindicates pass 24's decision to set yaw by eye. ⚠️ Yaw still matters, but the binding constraint is now perpendicularity to the pane and the ghosting it causes, which has no measured budget, rather than vignetting. Also struck: the 50×50mm pane alternative, which no longer covers the hole. |

| 27 | 2026-09-22 | **Corrected: the breather vent does not handle fogging, and this plan said it did.** ⚠️ **An ePTFE vent passes water vapour freely** — pores run 0.2–1µm against a 0.3nm gas molecule, so nitrogen, oxygen and vapour all diffuse through without distinction. What it blocks is the *liquid* phase, by capillary pressure: PTFE's ~115° contact angle puts water entry at **~2.4 bar** for a 0.5µm pore, orders of magnitude above rain or a hose test. Those are two different questions and the vent only answers one. **Its real job is stopping the box acting as a pump** — unvented, an enclosure exhales all afternoon and then pulls a vacuum overnight, drawing air back through gland seams and gasket, which is how sealed boxes flood; IP66 is a test condition, not a promise under sustained negative pressure. **So the vent lets moisture leave rather than keeping it out**, and interior absolute humidity equilibrates with outdoors over days. ⚠️ **Condensation therefore still happens, and the window is where** — thin, low-mass, high-emissivity, coupled to outdoor temperature and with a clear sky view, so radiative cooling on a calm clear night can put it *below* outdoor air temperature while warm interior air convects against its inner face. It lands at dawn, which is peak bird activity. Note the irony against pass 25: the Pi's waste heat holds most interior surfaces above dew point and is genuinely protective, but does nothing for the window, because heating air does not change its dew point. **Assembly conditions now matter explicitly** — this station's own weather log logged 32°C at 62% RH, a **dew point of ~24°C**, so closing the box in those conditions charges it with air that condenses on anything cooler, which is most Baton Rouge nights. Close it on a cool dry morning. **Desiccant and a vent are in tension**, which the plan half-knew by calling desiccant a backup: in a vented box it equilibrates with outdoor air, so it is for the initial charge and the drying-in weeks, not steady state. Sizing is a non-issue — 8.4L across a 40°C swing moves ~1.15L, averaging 1.6 mL/min over a 12-hour cooling cycle against vent ratings in the hundreds. ⚠️ Two ways to ruin one: **paint over it** while masking the box white for solar load, or let **surfactants** reach it — detergent, road film or insect residue lower water surface tension and drop that 2.4 bar sharply. |

| 28 | 2026-10-01 | **Shielded mic cable in, and the hum was a bad solder joint all along.** After the first solder job the capsule worked but measured 60 Hz at **−41 dB**, 120 Hz at −45 and the 1–8kHz floor at −52 — worse than pass 23's unshielded figure — and a day of tests built an elaborate story on it: a PoE-injected 120 Hz, an adapter-limited floor, a position-dependent source somewhere in the office. **A resolder erased all of it.** Same spot, same PoE power, same 100% gain: 60 Hz **−69.8** (−28.8), 120 Hz **−62.7** (−17.4), 1–8kHz **−65.5** (−13.6), >8kHz **−76.0** (−20.6). ⚠️ **The signature of a bad ground joint, for next time:** strong line-locked 60 Hz with 120/180 harmonics, a 120 Hz that tracks the power supply, a broadband floor 15–25 dB high, and pickup that changes when the capsule moves — the joint fault turns the ground return into an impedance that everything couples across. Resolder before measuring anything else. ⚠️ **A shorted capsule is not a valid floor test on this adapter**: Sleeve-to-Ring-2 is the CTIA headset button, and the adapter logged `KEY_PLAYPAUSE` held for the whole short and released when the jumper came off, so the −91 dB it read may be a muted input. Terminate with ~2.2kΩ instead, which is above every headset-button band. The muffled capsule bounds the electronics floor instead: **at or below −69 dB in 1–8kHz, −83 above 8kHz**. **Wiring:** braid is ground, capsule − → Ring 2, + → Sleeve; a reversed capsule looks like an open input, not silence, and BirdNET-Go's level stats round it to `zero_pct: 100`. **BirdNET-Go has zero detections ever**; its only high-confidence result since reconnection was `Human` at 0.93, removed by the privacy filter, which fires continuously on indoor speech. **Sensitivity baseline recorded:** a 4 kHz tone at 30cm reads **−27.8 dBFS**, 0.4 dB spread, 2nd harmonic 70 dB down — the first repeatable sensitivity number this chain has had. ⚠️ It was taken *after* heat-shrinking got the capsule hot, so on its own it could not show whether the heat cost sensitivity; in the same setup reads −31.8 dBFS, 4 dB *lower*, so the heat did no measurable damage — the gap is capsule tolerance and placement. The node's SSH user is `pi`. |

| 29 | 2026-10-01 | **AudioMoth works as a 384kHz USB mic — but not alongside the bird mic on the Pi 4's USB bus.** It shipped with the USB Microphone firmware (1.3.0, now **1.3.3**), and still showed no audio device, because ⚠️ **the switch decides the role**: at **USB/OFF** it is a configuration device only (HID + vendor class, `10c4:0002`); at **CUSTOM** it enumerates as `16d0:06f3` "384kHz AudioMoth USB Microphone", ALSA card `Microphone`, mono `S16_LE`, **384000 Hz only**. It has a **third** identity in the flash bootloader, `2544:0003` (Energy Micro EFM32 CDC), and the Flash App needs user access to all three — including the raw `/dev/bus/usb` node, since its helper uses libusb rather than hidraw. The udev rule that grants it must sort before `73-seat-late.rules` or `uaccess` silently does nothing. ⚠️ **On the Pi, it cannot record while the UGREEN streams**: `Not enough bandwidth for altsetting 1`, `usb_set_interface failed (-28)`. Both are 12M full-speed isochronous devices behind the Pi 4's single internal USB 2.0 hub, sharing one transaction translator; 384kHz × 2 bytes is ~768 bytes per 1ms frame and the UGREEN already holds its share. Unplugging the UGREEN made 384kHz record cleanly — confirmed contention, and **first to open wins**, so either mic could be the casualty after a reboot. Every USB 2.0 port on a Pi 4 shares that hub, so moving ports does nothing. **Fix: a multi-TT hub** (preferred, keeps 384kHz), or 256kHz (~512 bytes/frame, untested, still covers 128kHz). **No ultrasonic interference from the node:** band levels on the Pi match a quiet workstation within ~1 dB from 4–40kHz and 80–190kHz, with no narrow lines anywhere; 40–80kHz runs 2–3 dB higher but wanders, not a switching tone. **The AudioMoth's own floor has a broad hump at 16–32kHz**, about −53 dB per 2kHz band, identical on both machines — most likely the MEMS element's resonance, and the floor for faint bats in that range. |

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

### ⚠️ Measured: the aperture ring delivers half of what it's marked

Bench measurement, 2026-09-10, on the unit in hand. **Each marked stop delivers
0.48 stops.** The whole ring is worth about **one stop, not two.**

| Marking | Mean pixel | Stops vs 1.4 | Marked | Delivered |
|---|---|---|---|---|
| f/1.4 | 154.5 | 0.00 | — | reference |
| f/2 | 127.0 | −0.48 | −1.0 | **48%** |
| f/2.8 | 99.3 | −0.96 | −2.0 | **48%** |

Both steps land on 0.48 independently, against a frame-to-frame spread of 0–1
pixel value on steps of 27 — so this is a systematic, not measurement slop. A
light-leak model (constant stray light compressing the ratios) was fitted and does
not match. The likeliest cause is iris under-travel or engraving misaligned with
actual iris position.

#### How it was measured, and three ways it went wrong first

Auto-exposure metadata cannot answer this. Three attempts were confounded before
the method worked, each differently — worth recording so they are not repeated:

1. **Focus changed between captures.** Metering is centre-weighted by default and
   defocus redistributes brightness across the frame, so exposure moved for reasons
   unrelated to the iris.
2. **Target too close.** A white box 5 cm from the lens is shadowed by the camera
   itself. The AEC railed — identical `ExposureTime=66654`, `AnalogueGain=7.876923`
   at every aperture, which is the ~8× analogue cap and a frame-duration limit, not
   evidence the iris does nothing. Auto-exposure agreeing to six significant figures
   across three light levels is always a rail.
3. **Still using AEC.** Even unrailed, exposure clamped at 29983 µs with gain taking
   over, and freshly switched-on mains lighting flickers at 120 Hz against ~30 ms
   exposures.

What works:

- [ ] **Kill the AEC.** `--shutter` and `--gain` fixed; measure how bright the image
      actually is. Auto-exposure readings are a proxy for the thing you want.
- [ ] **Flat, evenly lit target, deliberately defocused**, filling the frame. Blur
      preserves frame mean while destroying detail, so reframing between captures —
      unavoidable when the ring needs two hands — stops mattering.
- [ ] **Shutter in multiples of 8333 µs** (120 Hz mains) so light flicker averages out.
- [ ] **Measure the central 50%**, away from vignetting.
- [ ] ⚠️ **Calibrate the tone curve; do not assume gamma.** A shutter ladder at fixed
      aperture gives known light ratios: 33332/24999/16666/8333 µs → 0/−0.415/−1/−2
      stops → measured means 154/131/97/52. Fitting an exponent between adjacent pairs
      gives 0.56, 0.67, 0.78 — drifting, so the ISP applies a tone curve on top of
      gamma. Reading stops straight off pixel values understates differences at the
      bright end. Interpolate the measured curve instead.

#### What this changes

- **Sit at the 2.8 marking.** Getting there from wide open costs ~1 stop, not the 2
  the engraving implies, while still closing the iris by 1.4× in diameter — enough to
  work on the chromatic aberration and corner softness seen on the same lens. A better
  trade than the markings suggest.
- ⚠️ **The light budget table below assumes standard stops and this lens has none.**
  The dawn/dusk row especially, where ISO is already 1600–3200.
- [ ] **Absolute f-number is still unknown** — the above is all ratios. If f/1.4 is
      honest, marked 2.8 is really ≈f/1.95; if 2.8 is honest, wide open is ≈f/2.0. Both
      fit. To settle it, measure the entrance pupil physically: at 16 mm, a true f/1.4
      is 11.4 mm across and f/2 is 8 mm. Photograph the lens front square-on with a
      ruler at each setting. **This matters for sourcing** — a lens that is really f/2
      wide open is a different purchase than one that is f/1.4, and it is the fast-lens
      margin at dawn/dusk that is at stake.

**Light budget** (nominal f/2.8, ISO 100) — the real binding constraint. ⚠️ Assumes
standard stops; the measured lens does not have them, see above:

| Conditions | Shutter achievable | Notes |
|---|---|---|
| Full sun | ~1/3200s | Trivial |
| Overcast | ~1/400s | ISO 200 |
| Canopy shade | — | ISO 400–800 for 1/500s |
| **Dawn / dusk** | — | **ISO 1600–3200. Peak bird activity.** |

Dawn/dusk is where this build strains. A fast lens buys ~1.5 usable stops back —
⚠️ but the measured unit's entire ring is worth ~1 stop, and its true wide-open
aperture is unconfirmed. Do not count on that margin until the pupil is measured.

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
| USB3 SSD (boot + root) | 1–4W |
| Active USB extender | ~0.5W |
| **Total** | **~9–14W** |

⚠️ The SSD row was missing until pass 25. This table predates the pass 16 decision to
boot and root from USB3, and an SSD under sustained write is the largest single swing in
the budget. PoE+ still covers it with room.

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

#### ✅ Chain verified end to end — 2026-09-21
PoE → surge arrestor → splitter → buck converter → Pi 4, with the camera attached and
streaming. Loaded with a sustained 4.2 GB write to the SSD while the camera ran:

```
pre    temp=63.7'C  throttled=0x0
t+20s  temp=64.7'C  throttled=0x0  clk=1800MHz
       4.2 GB written, 15.47 s, 271 MB/s
t+110s temp=65.2'C  throttled=0x0  clk=1800MHz
post   temp=63.3'C  throttled=0x0
```

- [x] **No undervoltage and no frequency capping.** `throttled=0x0` throughout,
      `in0_lcrit_alarm` 0, nothing in `dmesg`, ARM held at 1800 MHz. One clean boot, no
      restart loop.
- [x] **The converter is not costing throughput.** 271 MB/s against pass 16's 269 MB/s
      on the bench supply.
- [x] **Gigabit survives the arrestor and splitter** — `Link is Up - 1Gbps/Full - flow
      control rx/tx`. Worth confirming rather than assuming: plenty of cheap splitters
      and arrestors pass only two pairs and silently force 100 Mbps, which would quietly
      void pass 21's note that going wired reopens the raw-video option.
- [ ] ⚠️ **Still owed: a meter on the 5V rail under load.** `throttled=0x0` means the
      rail never crossed the ~4.63V undervoltage threshold. It does not mean 5.1V. A
      converter sitting at 4.8V passes every test above with nothing in reserve, and the
      reserve is the whole point of setting 5.1V.
- [ ] Verification commands, for the next time this needs checking:

      ```bash
      vcgencmd get_throttled; vcgencmd measure_temp    # 0x0 is clean
      cat /sys/class/hwmon/hwmon*/in0_lcrit_alarm      # 1 = undervoltage
      cat /sys/class/net/eth0/speed                    # expect 1000
      ```

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

### ⚠️ Full-resolution capture — OPEN DECISION

The pass 15 encoder ceiling caps **any streamed frame at 1920 px per axis**, so the
2028×1520 this phase's framing math assumes can never leave the node as an encoded
stream. Two routes to more pixels. They are not the same kind of change.

**Measured constraints (pass 16), all on the bench node:**

| Thing | Measured | Source |
|---|---|---|
| Encoder max, H.264 *and* MJPEG | 1920 px/axis | `v4l2-ctl` on `/dev/video11`, `/dev/video31` |
| Encoder macroblock cap | 8192 (H.264 L4.1) | `encoder_create()` failure at 1920×1440 |
| **ISP** max | **16384×16384** | `v4l2-ctl` on `/dev/video12` — the cap is the encoder, not the pipeline |
| Hardware JPEG encoder | present | `/dev/video31 bcm2835-codec-encode_image` |
| Node RAM | 1846 MB total, ~1574 free | **2 GB Pi 4**, not 4 or 8 |
| Node storage | USB3 SSD, 269 MB/s write | `dd` O_DIRECT 3 GB on `/dev/sda2` |
| Wifi throughput | ~100 Mbps sustained | 120 MB over SSH while streaming |
| Clock sync | NTP active, both ends | needed for timestamp correlation |

#### Route A — MJPEG at 1920×1440

Config only. MediaMTX already supports `rpiCameraCodec: mjpeg` and the hardware JPEG
encoder exists, so this costs nothing but a restart.

- 2.76 MP, 90% of 2028×1520's linear resolution
- **Intra-only**: no inter-frame compression, so the snapshot JPEG is the only lossy
  step after capture. Worth more than it sounds — today every snapshot is H.264'd at
  14 Mbps, decoded, then re-JPEG'd at quality 95
- Measured 15.3 Mbps (see below), comfortably inside the measured ~100 Mbps wifi ceiling
- Recording still works: MediaMTX's secondary path carries an H.264 record stream
- [x] **VERIFIED 2026-09-10: it does not.** MJPEG 1920×1440 runs. The macroblock cap is
      an H.264 constraint only; JPEG's 8×8 MCUs are not subject to it. mediamtx logs
      "using MJPEG encoder", the service stays active, and ffprobe reports
      `mjpeg 1920x1440 10/1`. **Route A is live.**
- [x] **Bandwidth measured — the estimate above was wrong by 3–4×.** Actual is
      **15.3 Mbps / 6.4 GB/hour** at quality 85 (~182 KB/frame), against H.264's
      14 Mbps / 5.9 GB/hour. So 33% more pixels for ~8% more bandwidth, which removes
      the storage objection to MJPEG almost entirely. ⚠️ Measured against a soft,
      out-of-focus indoor scene that compresses unusually well — re-measure against real
      foliage, which could run 2–3× higher.
- [x] VA-API hardware-decodes MJPEG on Alder Lake, verified with an explicit ffmpeg run.
      `preset-vaapi` stays valid: 6.24ms inference, camera_fps 10.1, zero skipped frames.
- [ ] ⚠️ **MJPEG recording is still unproven.** Segments mux correctly — an 18.9 MB
      10-second segment appeared in Frigate's `/tmp/cache`, matching the measured bitrate
      — but nothing has been promoted to `recordings/` because no review segment has
      existed to retain. Confirm on the first real detection: if events show
      `has_clip=false` and `recordings/` stays empty, move the record role to an H.264
      secondary path.

#### Route B — full-res ring buffer, retroactive fetch

Detect on a downscaled stream as now; the node holds recent **4056×3040** frames and
serves them on request when Frigate reports an event.

- 12.33 MP
- **Disk is the wrong medium.** 18.5 MB/frame × 10 fps = 185 MB/s = **15.98 TB/day**.
  A 128 GB consumer SSD (60–100 TBW) dies in 4–6 days. Bandwidth was never the problem.
  The 269 MB/s measurement also likely sat in SLC cache; sustained writes on a cheap
  drive collapse well below 185 MB/s.
- **RAM is the right medium.** ~1000 MB of buffer = 54 frames = **5.4 s** at 10 fps,
  against ~1.3 s of detection latency (≈1.0 s stream/IDR + 0.1 s detect + 0.2 s
  round-trip). ~4× margin, zero write wear.
- Request a **window** (±0.5 s ≈ 10 frames), not one frame: robust to clock skew, and
  you get to pick the sharpest — your own best-frame scoring on better data than
  Frigate had.
- `rpicam-vid --circular` is this exact pattern but buffers *encoded* output, so it
  inherits the 1920 cap. `rpicam-raw` gets full-res Bayer with no buffer. Neither
  suffices.
- **Cost: a custom libcamera application.** libcamera is exclusive, so one process must
  serve the detect stream *and* hold the buffer. `libcamera-dev` is not installed.
  Plus a workstation-side subscriber — which belongs in Phase 7, since it already plans
  to consume `frigate/events`.

#### ⚠️ Route B argues against two of this phase's own decisions

- **It abandons 2×2 binning.** Binned mode was chosen for ~2× low-light SNR, faster
  readout (less rolling-shutter skew on wingbeats), and halved resolution demand on the
  lens. Dawn/dusk at ISO 1600–3200 is where this build strains, and that is peak bird
  activity. The ISP downscale keeps most SNR for *detection*; the saved stills would be
  measurably noisier.
- **The lens may not resolve it.** Pixel pitch goes 3.1 µm → 1.55 µm. This plan says do
  not stop below ~f/4 at 3.1 µm for diffraction; at 1.55 µm that boundary moves to about
  f/2. With cheap CCTV glass soft wide open, a 900 px cardinal may carry 500–600 px of
  real detail. The gain is real but well short of 4×.

#### What decides it

Route A is live, so Route B is now optional rather than necessary: the question is
whether 12.33 MP of softer, noisier pixels beats the 2.76 MP of clean ones you already
have.

- [ ] ⚠️ **The lens test ran on 2026-09-10 and was invalid.** Captured 4056×3040,
      2028×1520 and 1664×1248 of the same scene. Matched crops of the same scene region
      are indistinguishable — both **focus-limited, not resolution-limited**. Objective
      corroboration: at identical q95, bytes/pixel *falls* as resolution rises
      (0.1805 → 0.1625 → 0.1576), meaning the extra pixels mostly interpolate. The
      camera was aimed through a window at a roof tens of metres away while focused
      around 2 m, at `Lux=6035` — bright, gain 1.0, best case, and says nothing about
      dawn/dusk.
- [ ] **Redo it properly:** fine detail at ~2.5 m, focus set carefully at full
      resolution, aperture near f/2. Judge resolved detail, not pixel count.
- [ ] Note from the invalid run: pronounced magenta fringing on a dark vertical edge.
      Real chromatic aberration and a hint the lens is near wide open — a genuine data
      point about the glass, feeding open question "lens sourcing".
- [x] ~~Snapshots appear at 2028×1520, above the stream — does Frigate source them
      outside the detect stream?~~ **No.** Those files date from 2026-08-25 and
      2026-09-01, when the detect input was the 2028×1520 `feeder-fixture.mp4`.
      Snapshots do come from the detect stream. Route B's rationale is unaffected.
- [ ] ⚠️ **Nothing has validated the live path end to end.** Every event in the database
      predates the live camera (181 on 08-31, 319 on 09-01, all from the fixture). Zero
      detections since the node went live on 09-04 — expected, since `objects.track` is
      `[bird]` and the camera is indoors on an out-of-focus lawn, but it means no live
      event, snapshot, clip, or MQTT message has been observed yet.

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
- [x] IP66 ABS or polycarbonate box. **In hand: 225 × 325 × 115mm internal**, larger
      than the ~200×150×100 originally specified. See placement, below.
- [ ] **Light gray or white.** Never black.
- [ ] **Gore-style breather vent plug** (M12, ~$8). Condensation, not rain, is the
      primary failure mode, and this is the right part — but see "What the breather
      vent does" below for what it does and does not fix. It is not a fogging cure.
- [ ] Rechargeable silica desiccant — for the initial charge and the drying-in weeks,
      not a steady-state fix. ⚠️ In a *vented* box desiccant eventually equilibrates
      with outdoor air, because the vent keeps supplying more moisture. That is not an
      argument against either part; it is the reason desiccant cannot be the answer on
      its own.
- [ ] **All penetrations on the bottom face.** Cable glands sized to cable OD
      (PG7 = 3–6.5mm, PG9 = 4–8mm). Drip loops on every cable.
- [ ] **Sunshade** standing 20–30mm off the box, open sides for airflow.
      A box in sun hits 60–70°C and the Pi throttles hard.
- [ ] Fit **one extra gland now, blanked off**, for future expansion
- [ ] Size the box for a future XLR audio interface if you ever go that route
- [ ] ⚠️ **Close the box on a cool, dry morning, not a hot humid afternoon.** Whatever
      air is inside at assembly is the charge it starts with. The station's own weather
      log recorded 32°C at 62% RH, which is a **dew point of ~24°C** — seal it in that
      and every surface below 24°C condenses, which is most nights here.
- [ ] ⚠️ **Mask the vent before painting.** The box gets covered white for solar load,
      and paint on the membrane destroys it. Small part, easy to overlook with a
      spray can in hand.
- [ ] ⚠️ **No soapy water near the vent.** Surfactants — detergent, road film, insect
      residue — lower water's surface tension and collapse the membrane's water entry
      pressure. Clean the enclosure with plain water around it.

#### What the breather vent does
Worth being precise about, because it is easy to over-credit and this plan did.

**It passes water vapour.** ePTFE pores run 0.2–1µm against a ~0.3nm gas molecule, so
nitrogen, oxygen and water vapour all diffuse through alike. The membrane has no
selectivity between gases, and vapour is a gas. **Humid air does enter the box.**

**It blocks liquid water**, by capillary pressure. PTFE's water contact angle is ~115°,
so intruding the liquid phase into a pore costs:

```
dP = -4 y cos(0) / d  =  -4 x 0.072 x cos(115) / 0.5e-6  ~=  2.4 bar
```

Rain, wind-driven spray and a hose test are orders of magnitude below that.

**Its real job is stopping the box acting as a pump.** Unvented, the enclosure heats all
afternoon and pushes air out past the gasket, then cools overnight and pulls a partial
vacuum — drawing air back in through gland seams, the gasket, any path available, along
with any liquid water sitting on a seal. That suction is how sealed boxes flood. IP66 is
a test condition, not a promise under sustained negative pressure. The vent gives the
cycle a deliberate path so the seals never see the differential.

- [x] **Sizing is a non-issue.** 8.4L of internal volume across a 40°C swing moves
      ~1.15L of air, which averages 1.6 mL/min over a 12-hour cooling cycle against vent
      ratings in the hundreds of mL/min. One M12 plug is overkill, which is correct.
- [ ] ⚠️ **It does not stop condensation.** The vent lets moisture *leave* rather than
      keeping it out, so interior absolute humidity tracks outdoors over days. Whenever
      a surface falls below the interior dew point, it fogs. See the window note in
      "Remaining window items".

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

### Camera window — DECIDED: fused quartz in a side wall
Required by the single-enclosure decision — the lens now shoots through the box.

**Material: 100×100×1mm double-side-polished fused quartz**, UV-Vis grade, in hand.
Better than the "optical acrylic or glass" this plan originally called for.

| Property | Value | Consequence |
|---|---|---|
| Transmission | >83% over 190–2500nm; **~93% in visible** | **0.1 stops.** The 83% is a broadband minimum dragged down by the deep-UV and IR ends; in-band it is just 4% Fresnel loss per surface |
| Thickness | 1mm | Focus shift ≈ t/3 = **0.33mm**, inside DoF at f/2 |
| Surfaces | double-side polished | The flatness and homogeneity the moulded lid lacked |
| Coating | **none** | 8% reflects back into the box — see flocking below |

#### ⚠️ Do not use the transparent lid
The enclosure's front lid is clear but tinted and **visibly warped** — edges swim when
you move it across a scene, which is the quick test for surface waviness and is
disqualifying on its own. Rejected 2026-09-10 without further measurement.

Two things follow anyway:

- [ ] **The lid is still a light path.** A clear front floods the interior with
      daylight, which bounces off the backboard, Pi and SSD and returns through the
      lid into the lens. That is veiling glare generated inside the enclosure — the
      same defect measured through a house window in pass 18, on a shorter path.
- [ ] ⚠️ **Cover it from the OUTSIDE** — white vinyl, tape or paint — not blacked out
      on the inside. A clear lid admits solar load directly onto the electronics, and
      absorbing it internally traps the heat. This plan's own figure is 60–70°C in a
      sunlit box with the Pi throttling hard.

#### Window goes in a side wall, not the front
- [ ] **Optical axis then runs along the box's longest internal dimension**, so the
      camera-plus-lens length stops competing with the ~100mm depth. This dissolves
      the standoff problem, see the build order below.
- [ ] An opaque ABS/PC side wall takes a hole saw far more forgivingly than the
      polycarbonate lid, which is also the sealing surface — a crack there is a dead
      enclosure.
- [ ] A window on a vertical face sheds water, and leaves the "all penetrations on
      the bottom face" rule undisturbed.
- [ ] ⚠️ Check the chosen face for **draft angle, moulding texture and internal ribs**.
      A 100×100mm pane needs that much genuinely flat wall to seal against. Cutting
      quartz down needs a diamond saw — it will not score and snap.

#### Placement — MEASURED 2026-09-10
Internal, the box in hand is **225mm wide × 325mm high × 115mm deep**, notably larger
than the ~200×150×100 originally specified. The optical axis runs along the **width**,
out of a side wall whose flat area is 115 × 325mm.

**Depth layout, from the back wall:**

| | |
|---|---|
| back wall | 0.0mm |
| pane rear edge | 7.5mm |
| backboard face | 11.5mm — ⚠️ the pane tucks **4.0mm behind** this |
| optical axis / hole centre | **57.5mm** |
| pane front edge | 107.5mm |
| front edge of the wall | 115.0mm — 7.5mm margin |

- [x] 100mm pane in 115mm of clear depth gives **7.5mm of bead margin per side**.
- [ ] **Camera sits 46.0mm out along the shelf** from the backboard face (57.5 − 11.5,
      the backboard standing ~11.5mm off the back wall).
- [x] *Considered and rejected:* shifting the pane forward to clear the backboard
      entirely. It buys 4mm at the back and costs 4mm at the front, dropping the front
      margin to 3.5mm — see the gasket warning below. Worse trade.
- [x] **Gasket confirmed clear (2026-09-10).** It meets at the edge of the lip and
      does not intrude onto the flat wall, so the **full 115mm is usable** and the
      centred pane leaves **7.5mm between its front edge and the sealing surface**.
      Still tool the front bead carefully and wipe squeeze-out before it skins —
      silicone migrates further than expected, and 7.5mm is comfortable rather than
      generous. Losing IP66 on a box meant to stay shut a year is the cost.

**Height: mount low.** Two independent reasons:

- **Mounting flexibility.** With the camera near the bottom, the box extends upward
  from it, so siting the box outdoors is positioning from near its bottom edge — which
  permits close-to-the-ground camera placement if a site ever calls for it.
- ⚠️ **Thermal, and this one is not obvious.** Pi, SSD and buck converter are the heat
  sources. Camera **below** them means convection carries their heat up and away from
  the sensor; camera above means every watt rises past it. This plan already flags heat
  twice — Pi throttling, and a hot IMX477 being a noisier IMX477 — and dawn/dusk is
  where the noise budget is already strained.

```
axis height     ~65 mm  (geometric floor 56mm; bead access is the real limit)
shelf surface   ~34 mm  (axis - 31)
```

- [x] **Corner fillet measured ~1mm** (2026-09-10, by sliding the pane down until it
      stopped sitting flush). Far sharper than the 8mm assumed, so the geometric
      floor drops to ~56mm. ⚠️ **But geometry is no longer the constraint — sealant
      access is.** Allow ~10mm below the pane for a nozzle and for tooling the bead,
      giving ~61mm. **65mm remains a sensible target**, now a comfortable choice
      rather than a hard floor; going lower buys a few mm of siting flexibility and
      costs bead access, which is where seals fail.
- [ ] ⚠️ That test measured the **side-wall-to-back-wall** corner. The one setting the
      height floor is **side-wall-to-bottom**. Moulded fillets are usually consistent
      so 1mm is very likely right, but confirm — it is the difference between the pane
      sitting flat and rocking on an unexpected fillet.
- [ ] It also keeps the camera clear of the bottom face, where the cable glands are and
      where any water that does get in will pool.
- [ ] Camera zone is ~116mm of the 325mm height, leaving **~210mm of backboard** above
      for Pi, SSD and buck converter. No competition for space.
- [ ] Laterally the screw sits 64.5mm from the window wall, leaving 160.5mm to the far
      wall.

#### Build sequence — pane first, backboard out
The backboard is removable and has a several-mm gap around it, which is what lets the
pane's rear edge sit 4mm behind the board's face plane.

1. [ ] **Pane in first, with the backboard removed.** Full access to both faces of the
       wall for masking, bedding and cleaning up squeeze-out. Bedding a 1mm pane past an
       installed backboard with 4mm of overlap would be miserable.
       See "Bedding the pane" for bead placement and the squeeze-out budget.
2. [ ] Backboard back in.
3. [ ] Shelf onto the backboard.
4. [ ] Camera onto the shelf, 46.0mm out.

#### ⚠️ Mount it compliantly — the CTE mismatch is the real risk
Fused quartz is **0.55 × 10⁻⁶/K**. ABS/polycarbonate is around **80 × 10⁻⁶/K**, about
150× higher. Across a 100mm pane and a 75°C swing (a Baton Rouge winter to a sunlit
box, both of which this plan already anticipates):

```
plastic expands   ~0.60 mm
quartz expands    ~0.004 mm
differential      ~0.6 mm
```

- [ ] **Silicone sealant, never epoxy.** Bed the pane and let the silicone absorb the
      movement.
- [ ] **No hard clamping and no screw bearing directly on the pane.** Continuous
      compliant gasket, not point loads. 1mm × 100mm quartz is a fragile plate.
- [ ] This is the difference between a window that survives a year unopened and one
      that cracks in the first cold snap.
- [x] **Body confirmed ABS (2026-09-10)**, so the CTE figures above stand as written —
      ~80 × 10⁻⁶/K against quartz's 0.55, giving the full 0.6mm differential. Silicone
      is essential, not merely good practice.
- [ ] ⚠️ **Use setting blocks; the wall is not flat.** The side-to-bottom join is
      wavier and slightly bulgier than the side-to-back join. Silicone accommodates
      waviness, but **only if the bead is thicker than the deviation** — press the pane
      flat against a wavy wall and it squeezes to nothing at the high spots, which is
      where it leaks and where the pane is stressed. Put two or three ~1mm shims
      between pane and wall, rest the pane on them, and fill the rest. Uniform bead,
      no bearing on high spots, and the pane floats in a compliant layer rather than
      being pinched against ABS that moves 0.6mm relative to it.
- [x] **Bead thickness is absorbed by the 2" hole.** It pushes the pane toward the
      lens and so adds to `d`:

      | Bead | d | Hole needed | 2" margin |
      |---|---|---|---|
      | 0.0mm | 8.5mm | 31.2mm | 9.80mm |
      | 1.0mm | 9.5mm | 31.7mm | 9.55mm |
      | 2.0mm | 10.5mm | 32.2mm | 9.30mm |

- [ ] ⚠️ **Do not fix the camera's lateral position before the pane is bedded.**
      Reference the 1mm air gap to the pane's **actual installed surface**, measured at
      dry fit — bead thickness is known after the fact, not before, and 1mm of error
      here is the entire gap. From the window wall's inner face the screw sits at
      65.5mm with no bead, 66.5mm with a 1mm bead.


#### Hole size — calculate it, do not guess
Too small vignettes the corners unrecoverably; too large weakens the wall and admits
more stray light. IMX477 active area is 6.287 × 4.712mm, 7.857mm diagonal, so at 16mm
the half-diagonal field angle is 13.8° and tan = 0.2456:

```
clear diameter needed at distance d  =  front element diameter + 0.49 x d
```

`d` is measured forward from the **front element**, and the hole is a tube not a plane,
so it accumulates every layer in front of the glass.

⚠️ **The lens lip sets a floor on how close the element can get to the pane.** The lip
extends **3.5mm** in front of the element and is the frontmost physical surface — so
"lens front as close to the window as possible" bottoms out at ~4mm on this lens, and
that distance propagates into the hole size.

**Measured geometry (2026-09-10):** front element ≈27mm; lip 3.5mm deep, **38mm OD /
36mm ID, so a 1mm-thick rim**; enclosure wall **3.0mm confirmed**; quartz 1mm; 1mm air
gap so the lip never touches the pane.

| Plane | d | Clear dia needed |
|---|---|---|
| front element | 0.0 | 27.0mm |
| lip front face | 3.5 | 28.7mm |
| quartz inner face | 4.5 | 29.2mm |
| quartz outer face | 5.5 | 29.7mm |
| **outer face of wall** | **8.5** | **31.2mm ← the minimum** |

- [x] **Vignetting check closed.** The lip's 36mm bore against the 28.7mm required at
      that plane leaves 3.7mm clearance per side. The lip is nowhere near the light
      cone — it is a built-in hood, and the lens covers the sensor as shipped.
- [ ] **Mount the pane on the inside face** over the hole. The seal then sits where
      weather cannot reach it and the hole depth becomes a shallow hood.
- [x] **DECIDED 2026-09-22 — use a 2" (50.8mm) hole saw**, sized for the lens *range*
      rather than the lens in hand. 31.2mm is what the current 16mm needs; the wall is
      drilled once and the pane is bedded over it, so the hole is the expensive thing to
      get wrong.

      ⚠️ **Longer lenses need smaller holes, not bigger.** The half-field angle shrinks
      with focal length, so the cone term collapses and the hole is set almost entirely
      by front element diameter:

      | Lens | cone factor | front element | hole needed at d=8.5mm |
      |---|---|---|---|
      | 8mm | 0.98 | ~30mm | 38.3mm |
      | 12mm | 0.66 | ~30mm | 35.6mm |
      | **16mm (in hand)** | 0.49 | 27mm | **31.2mm** |
      | 25mm | 0.31 | ~30mm | 32.7mm |
      | 50mm f/0.95 | 0.16 | ~45mm | 46.3mm |

      2" clears all of them, including about the fattest glass anyone puts on a 1/2.3"
      sensor. ⚠️ Front element diameter is the term that varies most between makers, so
      **check it against any actual candidate lens** rather than trusting the estimates
      in that column.

- [x] **What 2" costs, and it is affordable.** Bead land on the pane drops from 32.6mm
      to 24.6mm per side, still over 3× the 7.5mm budgeted; wall land stays 32.1mm per
      side of the 115mm face.

- [x] **A ~90mm aperture — nearly the full pane — was considered and rejected.** The
      silicone bead *is* the pane's mount, since screws and hard clamping are already
      ruled out. ~5mm of land per side removes the mount, leaves nowhere for the ~1mm
      setting blocks, and does not survive a few mm of centring error. Plate deflection
      scales with span⁴, so 34.9 → 90mm is ~44× on a 1mm plate — a hail question. A 90mm
      hole in a 115mm face also leaves two 12mm strips of ABS, at the face carrying the
      camera mount and the lid's sealing edge.

- [ ] ⚠️ **The 2" hole is no longer a hood, and that costs glare.** At 34.9mm the hole
      shaded oblique light on its way to a 31.2mm cone; at 50.8mm it is wide open, so
      more of it reaches an uncoated pane — on a system where pass 18 found veiling
      glare already dominant. This is the one real cost of the resize, and the barrel
      baffle below is what pays it back.

- [ ] ⚠️ **Do not plan to seal or bear against the lip.** At 1mm wall thickness it is a
      thin rim, not a flange, and at 2" the lip's 38mm OD passes straight through the
      hole with no land at all. That loses nothing: the 1.54mm a 1⅜" hole would have
      left was never doing a job, being too slight to seal against or to take a
      compression ring.
- [ ] **Control spill light with flocking instead**, on the barrel and on the interior
      around the window. Light that gets past the lens then lands on flocking and dies
      there. This is also the only option that respects the pane: any compression seal
      at the lens front, with the quartz on the inside face, would press on 1mm quartz
      — which the CTE section above forbids.
- [ ] **Idea for the flocking stage — a slip-on baffle tube on the barrel.** A flocked
      sleeve sized to each lens, sliding over the barrel and reaching toward the pane,
      restores the aperture the 2" hole gives up and swaps with the lens. It blocks
      off-axis light along its whole length rather than at one plane, which beats a flat
      mask at the window. Not specified yet — shape and length get worked out with
      flocking in hand.
- [ ] ⚠️ **Do not tape a mask to the inner face of the pane.** It is the obvious way
      to make the aperture swappable and it fails twice over in this box: adhesive at
      60–70°C creeps and outgasses, and what it outgasses condenses on the coldest
      surface in the enclosure — which is the window, in the optical path, behind a
      seal meant to stay shut a year. Felt held against glass also wicks and holds the
      condensation a breather-vented box will produce. Put the mask on the barrel, where
      it touches nothing.
- [ ] Note the formula rewards keeping the lens close to the glass, which is also what
      reflection control wants. Both constraints push the same way — the lip is the
      only thing stopping you going closer.

#### Bedding the pane — procedure
**Bead on the enclosure, not on the glass.** Three reasons:

- You can see what you are doing. A bead on a fixed wall is controllable; a bead on a
  1mm quartz pane means handling a fragile part with wet sealant on it, then placing it
  blind.
- **The pane is transparent — use that.** Setting it onto a bead on the wall lets you
  watch the bead compress and spread *through the glass*, so voids, bubbles and gaps in
  the ring are visible before cure. An opaque gasket never gives you that.
- Cleanup stays reachable. Misplaced sealant on the wall wipes off; misplaced sealant on
  the pane's wall-facing surface is in the optical path permanently.

**A continuous ring ~50mm in diameter, centred on the hole** — roughly 7–8mm out from
the hole's edge. Not near the pane's edge.

The governing reason is thermal: CTE strain scales with the **bonded span**, not with
the pane size.

| Ring diameter | Differential across it, 75°C swing |
|---|---|
| 100mm (near the pane edge) | 0.60mm |
| 70mm | 0.42mm |
| **50mm** | **0.30mm** |

Beading near the edge doubles the movement the joint must survive for no benefit — the
pane weighs ~22g and a 50mm ring holds that easily. Two lesser reasons agree: a tighter
ring shrinks the vented annulus between pane and wall where condensation can sit beside
the aperture, and it keeps sealant away from the lid gasket, only 7.5mm from the pane's
front edge.

- [ ] ⚠️ **The 7–8mm standoff from the hole edge is the squeeze-out budget.** Sealant
      spreads inward when the pane is set down, and **silicone inside the aperture is
      unrecoverable** — that face is never reachable again.
- [ ] **Place the setting blocks outboard, near the pane's edges.** A 50mm ring leaves
      ~25mm of 1mm quartz overhanging unsupported at each edge; outboard blocks control
      bead thickness *and* support that overhang while you work.
- [ ] ⚠️ **Clean both faces immediately before bedding.** Isopropyl, lint-free. The
      wall-facing surface is permanently in the light path and permanently unreachable —
      a fingerprint or a hair there is a defect for the life of the build.
- [ ] **Inspect through the glass after setting**, before the sealant skins: look for a
      continuous wetted ring with no voids.
- [ ] **Cure before it goes outside.** Neutral-cure skins in about an hour, wants a day
      before handling, and up to a week for full cure through section. Neutral-cure
      specifically — acetoxy cure releases acetic acid, which does not belong near
      optics or electronics.

#### Remaining window items
- [ ] **Lens front as close to the window as possible.** Single biggest factor in
      killing internal reflections.
- [ ] **Black flocking or felt around the lens barrel and the interior near the window
      — not optional with uncoated
      glass.** 8% of incoming light reflects off the two quartz surfaces and lands on
      the backboard, Pi and walls, then returns into the lens.
- [ ] External hood over the window for flare and rain — separate from the box
      sunshade.
- [ ] ⚠️ **Interior fogging is NOT handled by the Gore vent** — corrected pass 27,
      this line previously claimed it was. The vent passes water vapour freely; it
      equalises pressure and blocks the liquid phase. See "What the breather vent does".
- [ ] ⚠️ **The window is the surface that will fog, and it fogs at dawn.** It is
      thin, low-mass, high-emissivity, thermally coupled to outdoors and looking at open
      sky, so radiative cooling on a calm clear night can hold it *below* outdoor air
      temperature while warm interior air convects against its inner face and delivers
      moisture to it. Dawn is peak bird activity, so this lands squarely on the
      deliverable. Note that pass 25's waste-heat problem is protective everywhere
      *except* here: warming the interior raises surface temperatures but does not
      change the air's dew point, and the window is the one surface tied to outdoor
      temperature rather than interior.
- [ ] No mitigation is chosen yet. Assembly humidity and desiccant during drying-in are
      the cheap levers; anything better means keeping the pane warm, which fights the
      thermal budget rather than helping it.

### Build order — reversible before irreversible
Two steps here cannot be undone, so everything that can be dry-fitted comes first.

1. [x] **DONE 2026-09-10 — assemble camera + C-CS adapter + lens and measure mounting-plane to lens
       front.** 63.5mm screw-to-tip, 31.0mm axis height. See assembly geometry below.
       Every downstream decision derives from these against the
       box's internal dimensions.
2. [ ] **Decide where the camera must live** — driven by the shelf geometry and
       the pane position. ⚠️ Ribbon length is **not** a constraint — it reaches most of
       the backboard. The camera is the constrained item; place it first and arrange
       the Pi, SSD, buck converter and glands around it.
3. [ ] **Dry fit everything with zero drilling.** Tape, clamp, cardboard. Confirm the
       lens reaches the glass plane, the bracket holds the camera square, nothing
       fouls the lid gasket, and the Pi and SSD clear the camera.
4. [ ] Mark where the lens axis meets the chosen wall.
5. [ ] **Only now drill.** The camera's position is heavily constrained and the hole's
       is not, so let the constrained thing decide. Drilling first is how you discover
       the bracket cannot hold the lens where the hole already is.

#### Assembly geometry — MEASURED 2026-09-10
Camera + C-CS adapter + 16mm lens, measured as one assembly with the adapter fitted.
Datum is the **centre of the camera's ¼"-20 tripod mount**, on the mount plane.

| | |
|---|---|
| Screw hole to lip tip, along the axis | **63.5mm** |
| Optical axis above the mount plane | **31.0mm** (12mm to barrel edge + 19mm barrel radius) |
| Barrel diameter | 38mm |

The tripod screw axis is perpendicular to the optical axis, so the mount plane is
horizontal and the lens looks along it.

**Derived — along the axis, from the screw hole:**

| Plane | Distance |
|---|---|
| lip tip | 63.5mm |
| pane inner face (1mm air gap) | **64.5mm** |
| wall inner face | 65.5mm |
| outer wall face | 68.5mm |

**Derived — the bracket's job:** present a flat surface **31.0mm below the intended
optical axis**, parallel to it, with the screw hole **64.5mm back from the pane's inner
face**. That is the whole requirement.

Worked example, pane centred in a 105mm clear area — ⚠️ confirm the real figure and
recompute, it is just `hole centre − 31`:

```
clear flat area              105 mm
bead margin per side         2.5 mm
hole centre from backboard  52.5 mm
bracket surface height      21.5 mm above the backboard
```

- [x] **Focus travel does not eat the air gap.** Extension from infinity is 0.129mm at
      2.0m and 0.103mm at 2.5m — about a tenth of a millimetre across the whole useful
      range, so 63.5mm holds as you refocus and the 1mm gap is safe.

#### ⚠️ The tripod screw is one fastener — it yaws
Mounting by the ¼"-20 tripod thread is the easy option and worth keeping, but it is a
**single fastener on a vertical axis**, so the camera can pan on it held only by
friction. With a 63.5mm lever arm to the lip tip the tolerance is much tighter than it
looks:

| Yaw | Lateral at tip | |
|---|---|---|
| 0.50° | 0.55mm | 6% of margin |
| 1.00° | 1.11mm | 11% of margin |
| 2.00° | 2.22mm | 23% of margin |
| 4.00° | 4.44mm | 45% of margin |
| **8.78°** | **9.80mm** | **vignettes** |

Lateral margin is **9.80mm** — half of (50.8mm hole − 31.2mm required) — so **8.78° of
yaw is what it takes to vignette**.

⚠️ **This table was 5.2× tighter before pass 26.** At the original 1⅜" hole the margin
was 1.86mm and the budget 1.68°, which is what made anti-rotation hardware look
necessary. The 2" hole loosens it enormously and vindicates pass 24's decision to set
yaw by eye. **It does not make yaw free:** well before vignetting, the axis stops being
perpendicular to the pane and reintroduces the ghosting the good glass was chosen to
avoid. That is now the binding constraint, and unlike vignetting it has no measured
budget — so square it up as well as you can and treat 8.78° as a backstop, not a target.

- [x] **DECIDED 2026-09-17 — set yaw by eye, add no anti-rotation hardware.** Pins, a
      fence along the shelf, or an upstand bearing on the camera body would all work,
      and all of them fix the camera in one orientation. That forecloses a **motorised
      stage for distance and yaw**, which is a live possibility now that the slot makes
      the joint adjustable. The failure mode also announces itself: vignetting appears
      in the image corners, so the check is free and the correction is one loosened
      screw. ⚠️ **Updated pass 26:** the budget was 1.68° when this was decided and is
      **8.78°** at the 2" hole — 5.7mm across the 38mm camera body, which is easy by
      eye. Perpendicularity to the pane, not vignetting, is now what limits yaw.
- [ ] Revisit if the mount ever carries the 25mm lens. More overhang and more mass
      shrink the angular budget while making the joint harder to hold by friction.
- [ ] The lens-to-adapter-to-camera joint is separately locked and is **not** this
      problem. This is the camera-to-bracket joint.

#### Camera mount — an L-bracket shelf off the backboard
The backboard is **vertical** and the window is on a side wall, so the camera hangs off
the board with the lens pointing horizontally out of it. How the tripod screw is
oriented in that arrangement decides whether the mount survives.

⚠️ **Do not bolt the camera flat to the vertical backboard.** That puts the tripod
screw on a *horizontal* axis with the lens cantilevered sideways, so **gravity applies
a constant torque about the screw axis** — resisted by nothing but friction. It is a
static load that never lets up, and the failure mode is the lens swinging down to
vertical. A clamp can hold it, but it leaves a permanent load on the joint for the life
of a build whose whole goal is a year outdoors unopened.

**Instead: an L-bracket off the board with a horizontal shelf.** Vertical leg bolted
flat to the grid board, shelf extending out, camera sitting on top, tripod screw
running *up* into the thread on the camera's underside.

```
gravity   -> presses the camera down onto the shelf (normal force)
screw     -> clamps along its own axis, no torque about it
```

Gravity stops being a torque and becomes a normal force into a flat surface. Removing
the load beats holding it.

⚠️ **The camera sits on the shelf, not the lens.** From the measured geometry the
barrel's underside is 12mm above the mount plane, so with the camera's base on the
shelf the lens floats clear of it:

```
shelf surface        0 mm
barrel underside    12 mm   <- does NOT touch
optical axis        31 mm
```

If the barrel rested on the shelf the axis would sit at 19mm — the barrel radius — and
the hole would be 12mm out of place.

**Geometry:**

```
shelf height   = intended optical axis height - 31 mm
axis position  = 52.5 mm out from the backboard   (centres the pane in a 105mm clear area)
screw          = 64.5 mm back from the pane's inner face
```

- [ ] The grid backboard carries only Pi, SSD and buck converter besides the bracket,
      which is what it is good at. **Pi placement follows the lens**, not the reverse —
      the CSI ribbon reaches most of the backboard, so it is not a constraint
      (confirmed 2026-09-10).
- [x] **No barrel saddle.** See "The tripod screw is one fastener — it yaws" for the
      numbers; the pitching moment it was specified to remove is ~0.7N against a
      kilonewton-scale preload.

#### Shelf and fasteners — IN HAND 2026-09-17
The shelf is **0.75" (19.05mm) stock** with a **~76mm (3") slot** routed along the
optical axis, so the camera bolts straight to it and slides fore/aft.

**What the slot buys.** The 64.5mm screw-to-pane figure stops being a one-shot drilled
hole. Bead thickness is only known after the pane is bedded, and the 25mm lens moves the
screw back by its own extra length — both are now a slide rather than a second hole in a
shelf already built around the window aperture. It also leaves yaw free, which is what
makes setting it by eye recoverable.

⚠️ **The slot clamps, it does not locate.** A single screw on a slot can creep, and 1mm
ahead of the lens lip is bedded quartz. Fit a stop at the forward end of travel, or set
the forward limit so the lip cannot reach the pane even at the end of the slot.

**¼"-20 screw length — 1", not 1.5".** The stack is washer + shelf + engagement, and a
tripod bush is shallow:

```
1.5" screw  38.1 - 1.6 - 19.05 = 17.4 mm of thread into a ~5mm bush   -> bottoms out
1.0" screw  25.4 - 1.6 - 19.05 =  4.75 mm engagement                  -> correct
```

⚠️ A bottomed screw reads as **"loose no matter how tight"** and can push the bush out
of the camera housing. The washer sets the engagement depth, so it is dimensional rather
than optional; a second washer drops engagement to 3.15mm, which still holds but is
thinner than it needs to be. Measure the bush depth before final torque. Put the washer
under the head so it bridges the slot, and nothing between the camera and the shelf —
that flat contact is what carries the weight.

**Shelf height, with 19.05mm of stock under it:**

```
optical axis        65.0 mm   (target)
shelf surface       34.0 mm   (axis - 31)
bracket arm         14.95 mm  (surface - 19.05)
```

⚠️ **Confirm the backboard reaches 15mm off the floor**, and that the bracket arm and
its fasteners clear the bottom face where the glands are. The 0.75" stock spends 19mm of
the height budget that a thin bracket would not.

**Pi, SSD and buck converter: brass M2.5.** A 100pc brass kit is in hand. The scheme that
uses it: M2.5×11+6 M/F standoff, stud through the backboard, M2.5 nut behind; board on
the 11mm body, M2.5×5 screw into the female end. The 5mm screws are long enough — 1.4mm
of board leaves 3.6mm of engagement, eight threads at 0.45mm pitch — and the 11mm height
leaves convection space under the board, which matters in a box with no air exchange.
**Brass, not nylon:** nylon creeps under load at the 60–70°C this plan already assumes
inside the box.

- [ ] ⚠️ **Meter the Pi's corner holes to a header GND pin before using metal
      standoffs** into anything conductive. On several Pi models they are ground-tied,
      so a metal standoff bonds the Pi's ground to whatever it lands on — which may be
      wanted with a PoE splitter and a buck converter sharing the box, or may hand a
      ground loop to a high-impedance mic input. Phase 4 already spent a pass on 60 Hz.
- [ ] The 6mm stud suits a backboard up to ~3.5mm, leaving room for the nut. If the grid
      board is thicker, use the M2.5×11 F/F standoffs with a longer screw from behind.

*This supersedes an earlier sub-plate proposal*, which assumed a front-face window
~100mm out from the backboard and was designed around a cantilever the side-wall
decision removed. A shelf also keeps the hole small: a sub-plate would add its own
thickness in front of the camera, increasing `d` and therefore the required aperture.
The stack below holds `d` at 8.5mm, which is what keeps the hole at 31.2mm.

```
outside
  wall, 3mm, 50.8mm hole
  pane, 1mm, silicone-bedded on the inner face
  1mm air gap
  lens lip
  camera --> L-bracket shelf --> backboard
```

#### Pane size — keep it whole
The measured 115mm of clear depth gives 7.5mm of bead margin per side, which is
comfortable. An earlier note here warned the margin was thin; that was based on an
estimate of "just over 100mm" and is superseded by the measurement above.

- [ ] **Keep the pane whole** — recommended. Fused quartz is not easily replaced,
      cutting it needs a diamond saw with water, and a botched cut costs the part.
- [x] **Struck in pass 26:** a 50×50mm pane was floated as a way to halve the thermal
      differential. It does not cover a 50.8mm hole at all, so the full 100mm pane is now
      the only option rather than merely the recommended one.
- [ ] Silicone absorbs 0.6mm across 100mm provided the bead has some width and the pane
      is not pinched anywhere.

#### Four things easy to miss
- [ ] **Set final focus with the window installed**, not before. The pane moves the
      focal plane, and rings locked beforehand are locked on the wrong number.
- [ ] **Camera axis perpendicular to the pane.** Aiming is done by the external
      bracket, so inside the box the camera should be square and stay square. Shooting
      through glass off-axis adds ghosting on top of the glare.
- [ ] **Heat.** Pi 4, SSD and buck converter all dump heat into a sealed box, and a hot
      IMX477 is a noisier IMX477. Put the camera as far from those three as the layout
      allows and give the buck converter its own corner.
- [ ] ⚠️ **Measured in pass 25, and it is bigger than a sensor-noise question.** The
      Pi runs a 41.5°C rise over ambient, so the box's own interior temperature decides
      whether the Pi runs at all, not just how noisy the IMX477 is. Arranging the
      components is necessary and not sufficient. See the thermal entry in "Open
      questions for the next pass".
- [ ] **Lock the focus and aperture rings last**, after final focus through the
      installed pane. Both moved repeatedly during pass 18 bench work.

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
- [x] Shielded mic cable, under 10m — **fitted 2026-09-30, resoldered 2026-10-01**; braid is ground.
      See pass 28 for what it did and did not fix.
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

### Bird mic wiring — ⚠️ TRRS, not TRS
Interface in hand is a **UGREEN USB-to-3.5mm adapter**, TRRS, 24-bit/96kHz. The
plug-in-power question this plan flags is probably answered by its design: a TRRS
headset jack must supply mic bias, because phone headset mics are themselves electret
condensers — the same part class as the AOM-5024L.

⚠️ **Solder the capsule to a 3.5mm TRRS plug. A TRS plug fails silently.** On a
4-conductor CTIA jack:

| Contact | Signal | |
|---|---|---|
| Tip | Left audio out | |
| Ring 1 | Right audio out | |
| Ring 2 | Ground | ← capsule ground |
| Sleeve | Mic | ← capsule signal (FET drain) |

A 3-conductor TRS plug does not merely miss the mic contact — its long sleeve bridges
the jack's Ring 2 and Sleeve, **shorting the mic input to ground**. The result is
silence, indistinguishable from a dead capsule or absent bias.

- [x] **CTIA confirmed correct (2026-09-14).** Signal on sleeve, ground on ring 2.
      The OMTP swap was not needed.
- [x] ⚠️ **With shielded cable, the braid is ground: capsule − → braid → Ring 2, capsule +
      → inner core → Sleeve.** The braid carries the return current *and* screens the
      signal conductor inside it. Swapping conductors at one end only reverses the capsule.
- [x] ⚠️ **A reversed capsule is not silent — it looks like an open input** (2026-09-30).
      −68 dB mean, almost all of it hum under 200 Hz, 1–8kHz at −85 to −90 dB. BirdNET-Go's
      `audio level stats` round that to `max_level: 0`, `zero_pct: 100`, which reads as
      digital silence. Pull a capture and measure before believing it.
- [x] **Bandwidth measured and it is fine** — flat 4–20kHz, peak at 4–8kHz. See
      the test results below. The voice-tuned rolloff this warned about is absent.
- [x] Done. No AGC, sensible noise floor, plug-in power present.

---

#### Mic chain — TESTED 2026-09-14, works
AOM-5024L-HD-R soldered to a TRRS plug, into the UGREEN adapter, on the Pi. Every way
this could have failed is ruled out.

| Check | Result |
|---|---|
| Enumerates as capture | `card 3: Audio [KT USB Audio]`, KTMicro. It records — the "DAC" naming was misleading |
| Format | S16_LE, **mono**, 44100/48000 Hz. 48k is what BirdNET wants, and mono is what this plan wants |
| **Plug-in power** | **Present.** Live signal, so the TRRS jack biases the electret as predicted |
| **Wiring** | **CTIA was the right guess.** Signal on sleeve, ground on ring 2 |
| Ambient noise floor | −32 dB mean, −16 dB peak — sensible floor, good headroom |
| AGC | **None.** The keys test clipped at 0.0 dB; an AGC would have prevented that. A linear path is what detection work wants |

⚠️ **Capture gain is at 100% and keys at close range clipped** (216 samples at full scale).
Birds at 2.5m will be far quieter so this may never matter, but check for clipping once
deployed. Backing off to ~80% is available; it costs noise-floor headroom, so do not do
it preemptively.

**Bandwidth — the measurement that is on no spec sheet.** Octave-band energy from a keys
jingle, which has real content past 10kHz:

```
  125-250   Hz   -44.1 dB        4000-8000   Hz   -30.1 dB  <- peak
  500-1000  Hz   -47.5 dB        8000-12000  Hz   -34.3 dB
 1000-2000  Hz   -39.1 dB       12000-16000  Hz   -34.5 dB
 2000-4000  Hz   -32.7 dB       16000-20000  Hz   -34.5 dB
                                20000-23500  Hz   -43.0 dB  <- Nyquist rolloff
```

- [x] **No cliff at 8kHz.** Energy holds essentially flat from 4kHz to 20kHz, dropping
      only where the anti-alias filter lives. This is not the voice-tuned input the
      plan feared, and the **peak sits at 4–8kHz, exactly where BirdNET's diagnostic
      energy is**.
- [ ] *Method caveat:* this measures the whole chain — keys, capsule, adapter — and keys
      have their own bright spectrum, so it does not separate the mic's response from the
      source's. Content *reaching* 20kHz does prove nothing in the chain filters it out,
      which is what mattered.

**Listening test (the part measurement could not do).** Clean, no crackle — so the
solder joints are sound. Very slight hum, attributable to a water pump in the room
rather than electrical: a TRRS ground fault would show as steady 60/120Hz. And faint
speech stayed **intelligible underneath the loud keys**, which is better validation than
any number here — it means real dynamic range, no AGC pumping quiet content down, and
enough sensitivity to resolve a quiet distant source against a loud near one. That is
the actual job.

#### Audio path — the mic streams from the node
The mic is on the Pi and BirdNET-Go runs on the workstation, so audio crosses as its own
stream, separate from video, exactly as this phase specifies.

```
capsule -> TRRS -> UGREEN adapter -> Pi
        -> ffmpeg (ALSA) -> MediaMTX -> RTSP, LPCM 48kHz
        -> BirdNET-Go (channelMode: left) -> inference
```

- [x] **LPCM, not a lossy codec.** 48kHz mono is 768 kbps — trivial on wired ethernet,
      and nothing is lost before the classifier sees it.
- [x] ⚠️ **`plughw:Audio,0`, not `hw:3,0`.** By *name*, because ALSA card numbers shift
      on reboot; via the **plug** layer, because the raw device rejects ffmpeg's period
      size and fails with `Input/output error` even though `arecord` on `hw:` works.
- [x] `runOnInitRestart: yes`, so the publisher returns on its own.
- [x] **The stream reports 2 channels despite `-ac 1`.** Not a fault: L−R measures
      −91 dB against a −39 dB signal, so it is mono duplicated, and `channelMode: left`
      in BirdNET-Go recovers the original exactly. Left untouched rather than trading
      lossless PCM for a lossy codec to save bandwidth that is not short.

⚠️ **The UGREEN adapter only enumerates when a plug is inserted.** With no TRRS plug it
vanishes from USB entirely — `lsusb` does not list it and there is no capture device.
Consequences worth knowing before this is sealed in a box on a pole:

- [ ] If the mic is ever unplugged in the field, the audio device **disappears** rather
      than going silent. MediaMTX's publisher exits and BirdNET-Go logs `rtsp_404`.
- [ ] The plug must be in place at boot, or there is no capture device at all.
- [ ] It also makes "measure the adapter's own noise floor with the mic removed"
      impossible. ⚠️ **Do not substitute a shorted capsule** (pass 28): Sleeve-to-Ring-2
      is the CTIA headset button, and the adapter reports it as `KEY_PLAYPAUSE` held for
      as long as the short is in place, so the reading may be a muted input. Terminate
      with a **~2.2kΩ resistor** across the capsule instead — above every headset-button
      impedance band, close to the capsule's own output impedance.

⚠️ **Configure BirdNET-Go through its web UI, not by editing the YAML.** This plan already
said so in Phase 1; ignoring it cost a crash loop. `realtime.rtsp.streams` takes structs,
not URL strings, and the real schema is not guessable:

```yaml
streams:
  - name: Feeder
    url: rtsp://wildlife-pi.banklington:8554/birdmic
    enabled: true
    type: rtsp
    transport: tcp
    channelMode: left      # not "downmix" -- the UI warns against it for stereo sources
    gain: 0
    quietHours: {...}
    models: [birdnet]
```

Hand-writing `streams: [- rtsp://...]` produced
`'Realtime.RTSP.streams[0]' expected a map or struct, got "string"` on a restart loop.

#### 60 Hz hum — pass 23, unshielded cable
⚠️ **Describes the old unshielded cable only.** The shielded build, properly soldered,
measures 60 Hz at −70 dB — see pass 28, below. Kept as the record of what was measured
then.

A steady 60 Hz tone sits at about **−58 dB** in the capture. Everything tried, measured:

| Change | 60 Hz |
|---|---|
| exposed L/R leads (as built) | −56.8 dB |
| leads clipped flush to the jacket | −59.7 dB (**−2.9**) |
| Pi grounded via GPIO to an earthed chassis | −59.9 dB (no change) |
| capsule inside an **ungrounded** static shield bag | −56.8 dB (**+3.1, worse**) |
| same bag **grounded** | −58.8 dB (back to baseline) |
| capsule acoustically muffled | −59.1 dB (no change) |

- [x] ⚠️ **It is electrical, not acoustic.** The muffle test is the one that settled it:
      muffling removed **10 dB above 1kHz** — proving the muffle worked — while 60 Hz
      moved 0.3 dB. A similar-pitched hum *is* audible in the room from the workstation,
      but that is not what is in the recording.
- [x] **An ungrounded shield is worse than none.** The bag's metallised layer is a large
      floating conductor: it intercepts the field efficiently and, having nowhere to
      drain it, couples it into the high-impedance mic conductor inside. Grounding it
      only undid that harm; it did not go below baseline. This also explains why cupping
      a hand over the leads helped — a body intercepts *and* has somewhere to send it.
- [x] Earthing the Pi changed nothing, so a floating reference is not the mechanism
      either — or the bond never reached earth, which cannot now be distinguished.
- [ ] **Not worth pursuing further.** BirdNET works above 1kHz where this contributes
      nothing; the equalizer's 100 Hz HighPass (currently disabled) removes it from
      analysis entirely if wanted; and the deployed mic sits on a mast metres from the
      workstation rather than feet. The plan's **shielded mic cable** remains the right
      fix, and matters more outdoors — a standoff arm several feet from a switching buck
      converter in a sealed box.

#### Hum and noise floor — pass 28, shielded cable, 2026-10-01
Shielded cable fitted, braid as ground. The first solder job worked but measured worse than
the unshielded cable; a resolder fixed it. Both sets were taken at the same bench spot, on
the same PoE power, at the same 100% capture gain:

| Condition | 60 Hz | 120 Hz | 1–8kHz | >8kHz | <45 Hz |
|---|---|---|---|---|---|
| First joint, capsule open | −41.0 | −45.3 | −51.9 | −55.4 | −35.5 |
| First joint, capsule muffled | −46.4 | −43.5 | −56.1 | −57.1 | −45.7 |
| **Resoldered, capsule open** | **−69.8** | **−62.7** | **−65.5** | **−76.0** | −40.8 |
| **Resoldered, capsule muffled** | −69.4 | −70.2 | −69.0 | −83.3 | −45.4 |

*Method, so the next pass can compare:* capture from the RTSP stream on the workstation,
left channel only, 30 s. Tones are Goertzel RMS in dBFS over 5–10 s, which resolves
0.1 Hz; bands are ffmpeg `highpass`/`lowpass` → `volumedetect` mean. Every condition was
steady within 0.5 dB across 5 s blocks. Pass 23 recorded neither method nor position, so
its figures are not a baseline for these.

- [x] ⚠️ **The first joint was bad, and it looked like a dozen other problems.** Its
      symptoms, in the order they misled: 60 Hz with strong 120/180 harmonics; a 120 Hz
      that dropped 16 dB on a USB-C brick, which read as PoE injection; a "shorted" floor
      of −56 dB, which read as an adapter limit; and 60 Hz that moved 12 dB when the
      capsule moved a metre, which read as an office source. One resolder removed all of
      it. A poor ground joint puts an impedance in the return path that everything couples
      across, so **resolder and remeasure before diagnosing anything downstream.**
- [x] **The electronics floor is at or below −69 dB in 1–8kHz and −83 dB above 8kHz** —
      the muffled-capsule figures, which include capsule self-noise and whatever the scarf
      passes, so the true floor is lower. A shorted capsule read −91 dB but is not usable;
      see the adapter caveats above.
- [x] **The room, not the electronics, sets the floor.** An open capsule in a quiet office
      sits 3.5 dB above the muffled figure in 1–8kHz and 7 dB above it above 8kHz.
      Indoors that is the right way round; outdoors it will be more so.
- [x] **No PoE problem.** 120 Hz is at −63 dB open and −70 muffled, on PoE. The earlier
      "PoE chain injects 120 Hz" finding was the bad joint.
- [ ] **Sub-45 Hz dominates the broadband level** at −41 dB open, and drops 5 dB under
      the scarf: air movement on a bare capsule. The windscreen and fur outstanding at the
      top of this phase address it; BirdNET ignores this band regardless.

#### Sensitivity baseline — 2026-10-01
The first repeatable sensitivity number for the mic chain. Ambient captures cannot answer
"did this capsule lose sensitivity", because the room is not a fixed source; this can.

| Setting | Value |
|---|---|
| Source | iPhone 16 Pro Max, *Tone Generator* app, **4000 Hz** sine |
| Phone volume | **10%** |
| Geometry | **30cm** from speaker grille to capsule face, speaker aimed on axis |
| Chain | Capsule heat-shrunk, PoE power, capture gain 100% |
| **Result** | **−27.8 dBFS** at 4000.5 Hz, 0.4 dB spread over ten 2 s blocks |
| Linearity | 2nd harmonic −98 dBFS, 70 dB below the tone; sample peak −18.8 dBFS |

- [x] *Method:* same RTSP capture as the hum table, Goertzel at the measured tone
      frequency over 2 s blocks, median reported. Rerun it after anything that could
      change sensitivity — enclosure, routing, a capsule swap — and treat a drop of more
      than ~1 dB as real.
- [x] ⚠️ **Do not raise the volume.** At a louder phone setting the tone clipped (1.6% of
      samples at full scale) and read −4.7 dBFS, which understates the true level by an
      amount that varies with how hard it clips.
- [x] **Heat exposure — no damage found.** The capsule got hot during heat-shrinking, and an
      electret's charge drains with heat, which would show as *lower* sensitivity. The
      unheated spare AOM-5024L, soldered to the old unshielded cable and run in this exact
      setup, reads **−31.8 dBFS** (0.4 dB spread, no clipping) — **4 dB below** the heated
      capsule, not above it. The gap is unit-to-unit tolerance plus placement: at 4 kHz
      the wavelength is 8.6cm, so bench reflections make a couple of centimetres matter.
      ⚠️ So the ~1 dB rule applies to re-measuring **the same capsule**; between capsules,
      expect a few dB. Record which one is fitted when comparing.
- [x] **Shielding, indicatively:** the same pair of captures puts 60 Hz at **−67.7** on the
      shielded cable and **−59.1** on the unshielded one, 8.6 dB apart and close to pass
      23's unshielded −58. Different capsule and position, so not controlled — but the hum
      is electrical pickup, which the capsule barely affects.

#### Remaining Phase 4 work
- [x] **Audio bridged and running end to end (2026-09-15).** BirdNET-Go is pulling the
      stream and analysing; `analysis.log` shows live processing.
- [ ] ⚠️ **Watch `processing time exceeded buffer interval`.** It appeared twice on the
      first run, meaning inference fell behind real time. Harmless if occasional, but
      the load model in Phase 1 assumes GPU does video and CPU does audio without
      contending — if this becomes constant once the camera is back and detecting, that
      assumption needs revisiting rather than ignoring.
- [x] **Shielded mic cable** — fitted 2026-09-30, resoldered 2026-10-01; see pass 28.
- [ ] ⚠️ **Test coupling from the node's own electronics at close range.** Capsule and
      cable right against the buck converter and PoE splitter, then ~30cm off, with a
      2.2kΩ-terminated reference alongside. In the box the cable runs centimetres from both; pass
      28 did not test this and it is the one hum question that transfers outdoors.
- [ ] **Prove bird → detection before deploying.** BirdNET-Go's `detections` table is
      empty — nothing has ever passed the 0.7 threshold. Play a known call from the Merlin
      library at the capsule and confirm a row lands. Indoors, the **privacy filter**
      fires continuously on speech (25 hits in 100 s, threshold 0.05) and its highest
      result so far is `Human` at 0.98; that is the filter working, not a fault.
- [ ] Windscreen, fur cover and the soft non-resonant mount are still outstanding — see
      the capsule checklist at the top of this phase.

## Phase 5 — Ultrasonic channel: bats + orthoptera

*Goal: second acoustic stream, high sample rate, own mast.*

### Hardware
- [x] **AudioMoth USB Microphone** — up to 384kHz, no phantom power, plain USB
      audio device. Chosen for spectrum coverage and simple power. **In hand, flashed
      to USB Microphone firmware 1.3.3, configured for 384kHz — see "Bench test" below.**
- [x] **The USB mic case in hand solves this.** A hard shell with a narrow
      opening at the mic element, so the board is protected while the element
      stays open to air — which is what the weatherproofing rules below require.
- [ ] Own mast, 3–5m up

**Connection — DECIDED: active USB extender back to the bird box.**
The AudioMoth stays a dumb USB device with no computer on the mast. One cable
carries both its power and its data, and the bird box's Pi sees it as a locally
attached mic. Simpler than the alternative, with nothing extra to power or
maintain outdoors.

- [ ] **Active USB extender**, good to ~10–15m (USB 2.0 passive tops out ~5m).
      ⚠️ **Must not share a single transaction translator with the bird mic** — see the
      bandwidth finding below. Prefer one built on a **multi-TT** hub chip, or put an MTT
      hub between the Pi and both mics.
- [ ] **Shielded cable, in its own conduit.** The bird box contains a buck
      converter and, later, a solar charge controller — both radiate into the
      20–100kHz band, and an unshielded USB run is an antenna pointed straight at
      the mic you're trying to keep quiet. Do not zip-tie it to the 12V run.
- [ ] *Fallback only if the mast exceeds extender range:* Pi Zero 2 W publishing
      RTSP over Ethernet, which is distance-indifferent. Adds a second outdoor
      computer — avoid unless geometry forces it.

### Bench test — 2026-10-01
#### The AudioMoth has three USB identities
| Mode | Switch | USB ID | Presents |
|---|---|---|---|
| Configuration | **USB/OFF** | `10c4:0002` "AudioMoth" | HID + vendor class. No audio device |
| Microphone | **CUSTOM** | `16d0:06f3` "384kHz AudioMoth USB Microphone" | ALSA card `Microphone`, mono `S16_LE`, 384000 Hz only |
| Flash bootloader | (entered by the Flash App) | `2544:0003` "EFM32 USB CDC serial port device" | `/dev/ttyACM0` |

- [x] ⚠️ **Configure at USB/OFF, record at CUSTOM.** A device at USB/OFF reports firmware
      `AudioMoth-USB-Microphone` and is still not a microphone, which looks exactly like
      the wrong firmware. The serial number in mic mode starts `0384_` — the configured
      rate.
- [x] Settings: 384kHz, gain Med, filter None, 48 Hz DC blocking **kept**, energy saver
      off, low gain range off. Filter left off deliberately, to see the whole spectrum
      before choosing one; a ~15kHz high-pass is the candidate, but it would cut local
      crickets at 4–8kHz.
- [x] Card name `Microphone` does not collide with the bird mic's `Audio`, so the
      `plughw:Audio,0` publisher is unaffected.

#### Flashing from Linux needs a udev rule
The apps are `audiomoth-flash` and `audiomoth-mic` (`.deb` from the Open Acoustic Devices
GitHub releases); flashing is the Flash App, settings are the Mic App. Without access to
all three identities the Flash App says "No AudioMoth found", then fails mid-flash with
"Communication Failure". `/etc/udev/rules.d/70-audiomoth.rules`:

```
SUBSYSTEM=="usb", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="0002", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="0002", TAG+="uaccess"
SUBSYSTEM=="tty", ATTRS{idVendor}=="2544", ATTRS{idProduct}=="0003", TAG+="uaccess"
```

- [x] ⚠️ **The `usb` line is the one that matters**: the apps' `usbhidtool` opens the raw
      `/dev/bus/usb` node through libusb, not `/dev/hidraw*`. The failure is `EACCES` on
      that node, visible only under `strace`.
- [x] ⚠️ **The file must sort before `73-seat-late.rules`.** That is where `uaccess` tags
      become ACLs; named `99-`, the tag is set and nothing happens.

#### ⚠️ It cannot record alongside the bird mic — USB bandwidth
```
usb 1-1.1: Not enough bandwidth for altsetting 1
usb 1-1.1: 1:1: usb_set_interface failed (-28)
```

`arecord` reports only `Unable to install hw params`, which reads like pass 23's period-size
problem and is not; `plughw` does not help. `-28` is `ENOSPC`, and `dmesg` is where it
shows.

```
xHCI root (480M)
 └─ internal USB 2.0 hub (VIA 2109:3431, 480M) — every USB 2.0 port on a Pi 4
     ├─ AudioMoth, 12M full-speed isochronous — ~768 bytes per 1ms frame at 384kHz
     └─ UGREEN,    12M full-speed isochronous — the bird mic, already streaming
```

Full-speed devices behind a high-speed hub share its transaction translator, whose
periodic budget is far smaller than the hub's 480M. **Confirmed by elimination:** with
the UGREEN unplugged, 384kHz records cleanly. **First to open wins**, so after a reboot
either mic can be the one that fails, depending on start order.

- [ ] **Fix, preferred: a multi-TT USB 2.0 hub**, giving each mic its own translator. Keeps
      384kHz. **Ordered 2026-10-01: Adafruit CH334F Mini 4-Port USB Hub Breakout** (product
      5997) — WCH CH334F, MTT stated by the vendor, 32 × 20mm. On arrival:
      - Confirm `bDeviceProtocol 2` (multi-TT) in `lsusb -v`, and whether it reports
        self-powered — bus-powered lets Linux cap each port at 100 mA.
      - Feed its 5V header pin from the buck converter, data only to the Pi. The Pi 4's
        USB ports share ~1.2 A and the SSD takes up to ~0.8 A of it under write. Same rail,
        so no backfeed. ⚠️ Confirm the buck's current rating covers Pi + hub, ~3.5 A.
      - Downstream ports are pins, not sockets — solder or crimp the UGREEN and extender.
        Keep the board away from the bird mic leads.
      - The test that closes this: bird mic streaming through mediamtx and the AudioMoth at
        384kHz together, with no `-28` in `dmesg`.
- [ ] *Fallback: 256kHz* — ~512 bytes per frame, which probably fits beside the UGREEN.
      **Untested.** Still covers bats to 128kHz, and 256kHz is BirdNET-Go's advertised
      bat maximum, but it gives up the specified rate.
- [ ] Moving ports does nothing: all four share the internal hub's USB 2.0 path.

#### Noise floor — no node interference, one inherent hump
5 s captures at 384kHz, same settings, ffmpeg band filters → `volumedetect` mean (dB):

| Band | Workstation | Pi, on PoE |
|---|---|---|
| 0–4kHz | −49.3 | −44.7 |
| 4–16kHz | −63.3 to −56.4 | −63.3 to −57.6 |
| **16–32kHz** | **−51.9 to −54.2** | **−52.6 to −54.4** |
| 40–80kHz | −58.5 to −63.1 | −56.4 to −60.6 |
| 80–190kHz | −64.2 to −68.2 | −63.8 to −68.0 |

- [x] **No switching interference on the Pi.** A converter radiating ultrasound shows as
      narrow lines at fixed frequencies; neither capture has any. The Phase 5 worry about
      the buck converter is not borne out at the bench — re-check once the extender and
      enclosure are in, since cable routing changes it.
- [ ] 40–80kHz runs 2–3 dB higher on the Pi, but its strongest bin wanders (46,650 →
      47,350 Hz between half-second windows) — broadband, and within what two locations
      in the room explain. PoE versus USB-C with the AudioMoth recording would attribute
      it, the same test that isolated the bird mic's 120 Hz in pass 28.
- [x] ⚠️ **The 16–32kHz hump is the AudioMoth's own**, identical on both machines and per-Hz
      higher than the audible band. Most likely the MEMS element's ultrasonic resonance —
      unverified; covering the port would confirm. It sets the floor for faint bats
      calling in that range.

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

⚠️ **Thermal — can the Pi survive the box at all?** *New in pass 25. It sits ahead of
the numbered list because it blocks the Phase 3 build already in progress.* Measured
63.7°C mean and 65.2°C peak under load at 22.2°C ambient: a **41.5°C rise**, passive,
with no cooling device registered. The Pi 4 soft-throttles at 80°C, so ambient has to
stay under **~38°C**. This plan assumes **60–70°C** inside a sealed box in sun — a
25–30°C gap, whose failure mode is continuous hard throttling at 85°C rather than a
reduced margin.

- A fan is ruled out twice over: an IP66 box has no airflow, and the PoE HAT was
  rejected in part for having one.
- Conduction is what remains, and ABS runs ~0.17 W/m·K. The shell is not a radiator
  without a metal path through the wall, which then conducts solar heat *inward* and
  has to cross the seal.
- ⚠️ **Measure before designing.** The 60–70°C figure has never been measured on this
  box. Log the empty enclosure in place over a full day, shaded and unshaded, before
  building cooling against an assumption — a sunshade over the box is the untested
  lever with the most leverage, and it is far cheaper than a thermal bridge.

1. **Full-resolution capture — MJPEG or a ring buffer?** The encoder caps every
   streamed frame at 1920 px/axis, so 2028×1520 cannot leave the node encoded.
   Route A (MJPEG 1920×1440) is config-only and works over wifi; Route B (full-res
   RAM ring buffer + retroactive fetch) is 12.33 MP but needs a custom libcamera app
   and abandons 2×2 binning. ⚠️ Decide with a real full-res still from the actual
   lens in hand — the glass may not resolve 1.55 µm pixels. See Phase 2,
   "Full-resolution capture".
2. **Motion masking against the real camera.** detect CPU hit 154% from wind.
   No longer blocks a purchase, but still the difference between a tidy system
   and a wasteful one — and it determines sizing if compute ever moves. Bench
   masks don't transfer (frame is 2.7× wider).
3. **ffmpeg RTSP publish commands** — video, bird audio, and the dusk/dawn cron
   scheduling for the ultrasonic stream. Next working session.
4. **Network segmentation** — VLAN or firewall rules to keep the node off the
   internet. ⚠️ Must allow Frigate one-time internet access first, to download the
   bird classification model.
5. **Semantic search?** No longer a purchase blocker — evaluate on the existing
   workstation whenever curiosity strikes.
6. **Lens sourcing** — confirm a 16mm f/1.4 C-mount with acceptable sharpness at
   f/2 before committing. Cheap CCTV glass varies wildly unit to unit. ⚠️ **The unit
   in hand measures 0.48 stops per marked stop** — its whole ring is worth ~1 stop,
   not 2 — and shows visible lateral chromatic aberration wide open. Absolute
   aperture is unconfirmed; measure the entrance pupil (11.4mm = true f/1.4 at
   16mm) before treating "f/1.4" as a spec. See Phase 2, "the aperture ring
   delivers half of what it's marked".
7. **Solar geometry and sizing.** Genuinely last — downstream of measured load,
   and the phase swap turned this from a guess into a measurement.

*Closed in pass 15:* VA-API on Alder Lake — decodes real camera input clean (7.72ms, 10.0 process_fps, zero skipped). Pass 11's failure was the corrupt out-of-band RTSP publisher, not the decoder.

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
| 100×100×1mm fused quartz, DSP | Camera window — **in hand** | 3 | ☑ decided |
| Neutral-cure silicone sealant | Bed the quartz compliantly — ⚠️ **never epoxy**, CTE mismatch | 3 | ☐ |
| Setting blocks / ~1mm shims | Control bead thickness — ⚠️ wall is wavy, do not squeeze | 3 | ☐ |
| Shelf, 0.75" stock, slotted | Camera sits on it, screw up — **in hand**, ~76mm slot routed | 3 | ☑ |
| Shelf brackets | Carry the shelf off the backboard — **in hand**; ⚠️ arm lands ~15mm off the floor, size unrecorded | 3 | ☑ |
| ¼"-20 screws, washers, nuts | Camera to shelf — **in hand**; ⚠️ use the **1"** with one washer, the 1.5" bottoms out | 3 | ☑ |
| Brass M2.5 kit, 100pc | Pi, SSD, buck converter to the backboard — **in hand**; 11+6 standoffs, nuts, M2.5×5 screws | 3 | ☑ |
| Standoffs / shim stock | Fine-tune shelf height to put the axis at 31mm | 3 | ☐ |
| Locating pins or bracket upstand | ⚠️ Anti-yaw — **deferred**, would foreclose a motorised stage; set by eye | 3 | ☐ |
| Black flocking / felt | Lens barrel + interior — **not optional, uncoated pane** | 3 | ☐ |
| **2" (50.8mm) hole saw** | Window aperture — sized for the lens range, not the lens in hand | 3 | ☐ |
| White vinyl or paint | Cover the clear lid **from outside** (solar load) | 3 | ☐ |
| Pi HQ Camera, IR-filtered | Sensor — **not NoIR** | 2 | ☑ decided |
| 16mm C-mount lens, f/1.4 | Optics | 2 | ☑ decided (sourcing open) |
| C-to-CS adapter | Back focus | 2 | ☐ |
| IP66 ABS enclosure, 225×325×115 | **In hand.** Clear lid rejected as a window | 3 | ☑ |
| M12 breather vent plug | Pressure equalisation — ⚠️ passes vapour, not a fogging fix | 3 | ☐ |
| Rechargeable silica desiccant | Initial charge + drying-in only; equilibrates in a vented box | 3 | ☐ |
| Cable glands PG7/PG9 | — | 3 | ☐ |
| PUI AOM-5024L-HD-R ×2 | Bird mic capsule — **tested working**, one spare | 4 | ☑ |
| UGREEN USB-3.5mm TRRS adapter | Bird mic input — **tested**: bias OK, flat 4–20kHz, no AGC, floor at or below −69 dB in 1–8kHz; ⚠️ a shorted input reads as a play/pause press | 4 | ☑ |
| Shielded mic cable | Capsule → TRRS plug — **fitted**, braid to capsule − and Ring 2 | 4 | ☑ |
| AudioMoth USB Mic + mic case | Ultrasonic — **in hand**, USB Mic firmware 1.3.3 at 384kHz; case has an open mic port, suits Phase 5 | 5 | ☑ |
| Adafruit CH334F Mini 4-Port USB Hub (5997) | Multi-TT hub — AudioMoth and bird mic cannot share the Pi 4's single TT; **ordered 2026-10-01**. 5V from the buck, pins not sockets | 5 | ☑ ordered |
| USB3 SSD 128GB | Pi boot + root — **in hand**, 269 MB/s measured | 2 | ☑ |
| Active USB extender, shielded | AudioMoth → bird box — ⚠️ prefer a multi-TT hub chip | 5 | ☑ decided |
| Solar panel | — | 6 | ☐ **sizing open** |
| LiFePO4 + low-temp-cutoff BMS | — | 6 | ☐ |
