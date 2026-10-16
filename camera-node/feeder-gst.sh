#!/bin/sh
# Feeder camera publisher, run by MediaMTX (runOnInit on the feeder path).
#
# Camera -> hardware JPEG image encoder (/dev/video31) -> RTSP into MediaMTX.
# Replaces MediaMTX's built-in rpiCamera source, whose MJPEG encoder is software
# libjpeg on one core: about 100% of a core and the node's main heat source. This
# pipeline encodes in hardware at about 20% of a core.
#
# sensor-config pins the 2x2-binned 2028x1520 10-bit mode, the same mode as
# rpiCameraMode "2028:1520:10:P". v4l2video31jpegenc is the quality-controlled image
# encoder; plain v4l2jpegenc binds /dev/video11's bitrate-controlled MJPEG instead.
#
# Requires gstreamer1.0-tools, -plugins-base, -plugins-good, -libcamera and -rtsp,
# with gstreamer1.0-libcamera matching the installed libcamera.
exec gst-launch-1.0 -e \
  libcamerasrc sensor-config="sensor/config,width=2028,height=1520,depth=10" ae-enable=true awb-enable=true \
  ! video/x-raw,width=1920,height=1440,framerate=10/1,format=I420 \
  ! v4l2video31jpegenc extra-controls="c,compression_quality=85" \
  ! image/jpeg ! queue \
  ! rtspclientsink location="rtsp://localhost:${RTSP_PORT:-8554}/${MTX_PATH:-feeder}" protocols=tcp
