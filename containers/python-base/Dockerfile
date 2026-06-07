# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0


FROM python:3.12-slim-bookworm AS builder

ARG PYTHON_VERSION=cp312
ARG OPENCV_REPO_OWNER=arduino
ARG OPENCV_VERSION=4.13.0.92
# Tag 后缀：app-bricks-py312 分支会传 -cp312，arduino 上游默认空字符串
ARG OPENCV_TAG_SUFFIX=

COPY ./requirements-base.txt /app/requirements.txt

RUN set -ex; \
    apt-get update -y; \
    apt-get upgrade -y; \
    # Install build dependencies
    apt-get install -y --no-install-recommends --no-install-suggests build-essential ca-certificates binutils; \
    # Install dependencies for building ALSA
    apt-get install -y --no-install-recommends --no-install-suggests libasound2-dev libalsaplayer-dev portaudio19-dev libzbar0; \
    # Append OpenCV wheel URL (full wheel name with platform details)
    echo "https://github.com/${OPENCV_REPO_OWNER}/app-bricks-py/releases/download/opencv/${OPENCV_VERSION}${OPENCV_TAG_SUFFIX}/opencv_python_headless-${OPENCV_VERSION}-${PYTHON_VERSION}-${PYTHON_VERSION}-linux_aarch64.whl" >> /app/requirements.txt; \
    # Install Python dependencies
    pip install --no-cache-dir uv; \
    uv pip install --system --no-cache-dir -r /app/requirements.txt; \
    rm /app/requirements.txt; \
    # Strip debug symbols, tests and remove unneeded packages to reduce size
    find /usr/local/lib/python3.12/site-packages -type f -name "*.so" -exec strip -s {} +; \
    find /usr/local/lib/python3.12/site-packages -type f -name "*.so.*" -exec strip -s {} +; \
    find /usr/local/lib/python3.12/site-packages -type d -name "tests" -exec rm -r {} +; \
    apt remove -y build-essential ca-certificates binutils libasound2-dev libalsaplayer-dev portaudio19-dev; \
    apt-get clean; \
    apt-get autoclean -y; \
    apt-get autoremove -y


FROM python:3.12-slim-bookworm AS production

ARG LIBCAMERA_REPO_OWNER=arduino
ARG LIBCAMERA_VERSION=0.7.0-4

# Copy the installed dependencies from the 'builder' stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN set -ex; \
    groupadd -g 1000 arduino || true; \
    useradd -u 1000 -g arduino -ms /bin/bash arduino; \
    apt-get update -y; \
    apt-get upgrade -y; \
    apt-get install -y --no-install-recommends --no-install-suggests wget; \
    # Install dependencies for running ALSA
    apt-get install -y --no-install-recommends --no-install-suggests alsa-utils libportaudiocpp0; \
    # Install dependencies for running OpenCV with Gstreamer backend
    # The opencv-python-headless wheel from the fork is built against ffmpeg 5.x
    # (libavcodec 59, libavformat 59, libavutil 57, libswscale 6), which matches
    # Debian 12 bookworm. Debian 13 trixie ships ffmpeg 7.x and would break cv2
    # with "libavcodec.so.59: cannot open shared object file".
    apt-get install -y --no-install-recommends --no-install-suggests libavcodec59 libavformat59 libavutil57 libswscale6; \
    # libgl1 is required by mediapipe's opencv-contrib-python (needs libGL.so.1).
    # libegl1/libgles2 are the headless GL stack we actually want, but the
    # contrib build of opencv is hard-coded to link against X11/GL symbols.
    apt-get install -y --no-install-recommends --no-install-suggests libgl1 libglib2.0-0; \
    apt-get install -y --no-install-recommends --no-install-suggests libjpeg62-turbo libtiff6 libpng16-16 libwebp7 libopenblas0 liblapacke; \
    apt-get install -y --no-install-recommends --no-install-suggests libgstreamer1.0-0 libgstreamer-plugins-base1.0-0 gstreamer1.0-plugins-good gstreamer1.0-plugins-base-apps; \
    # Install dependencies for running libcamera.
    # Note: libpisp1 / libboost 1.83.0 / libcamera .deb were originally for the
    # Raspberry Pi OS trixie base, but with `python:3.12-slim-bookworm` they are
    # not in the Debian 12 repos. The original libcamera deb chain also requires
    # those Pi-only deps. Commenting out — if your app needs libcamera, re-enable
    # and use the bookworm versions of these packages.
    # apt-get install -y libpisp-common libboost-filesystem1.74.0 libboost-log1.74.0 libboost-thread1.74.0 libpisp1 libegl1 libgles2 libyaml-0-2 liblttng-ust1 libdw1 libyuv0; \
    # wget -O libcamera0.7_${LIBCAMERA_VERSION}_arm64.deb https://github.com/${LIBCAMERA_REPO_OWNER}/app-bricks-py/releases/download/libcamera%2F${LIBCAMERA_VERSION}/libcamera0.7_${LIBCAMERA_VERSION}_arm64.deb; \
    # wget -O libcamera-ipa_${LIBCAMERA_VERSION}_arm64.deb https://github.com/${LIBCAMERA_REPO_OWNER}/app-bricks-py/releases/download/libcamera%2F${LIBCAMERA_VERSION}/libcamera-ipa_${LIBCAMERA_VERSION}_arm64.deb; \
    # wget -O gstreamer1.0-libcamera_${LIBCAMERA_VERSION}_arm64.deb https://github.com/${LIBCAMERA_REPO_OWNER}/app-bricks-py/releases/download/libcamera%2F${LIBCAMERA_VERSION}/gstreamer1.0-libcamera_${LIBCAMERA_VERSION}_arm64.deb; \
    # dpkg -i libcamera0.7_${LIBCAMERA_VERSION}_arm64.deb libcamera-ipa_${LIBCAMERA_VERSION}_arm64.deb gstreamer1.0-libcamera_${LIBCAMERA_VERSION}_arm64.deb; \
    # Install other runtime dependencies
    apt-get install -y --no-install-recommends --no-install-suggests inotify-tools libzbar0; \
    mkdir -p /home/app/.fonts; \
    wget -O /home/app/.fonts/OpenSans.ttf https://raw.githubusercontent.com/googlefonts/opensans/main/fonts/ttf/OpenSans-Regular.ttf; \
    apt-get remove -y wget; \
    apt-get autoclean -y; \
    apt-get autoremove -y; \
    # NOTE: original Dockerfile did `dpkg -r --force-depends libegl-mesa0 mesa-libgallium libllvm19`
    # to strip 200+MB of mesa/llvm. With Debian 12 bookworm and libgl1 properly
    # installed, we keep mesa-libgallium in place — `mediapipe` and
    # `opencv-contrib-python` both need libGL.so.1 to load. The size hit is
    # acceptable for fork builds; trim again if you ship to production.
    # cleanup unnecessary files to reduce image size
    rm -rf /tmp/* /var/tmp/*; \
    rm -rf /var/lib/apt/lists/*; \
    rm -fr /var/cache/apt/archives/*.deb \
        /var/cache/apt/archives/partial/*.deb \
        /usr/share/man/* \
        /usr/share/locale/* \
        /var/cache/debconf/* \
        /var/lib/dpkg/info/* \
        /var/cache/apt/*.bin; \
    find /usr/share/doc -type f ! -name 'copyright' -delete; \
    find /usr/share/doc -type d -empty -delete; \
    # precompile python files to .pyc to speed up startup time
    python -m compileall /usr/local/bin; \
    python -m compileall /usr/local/lib

COPY libcamera.yaml /etc/libcamera/configuration.yaml
