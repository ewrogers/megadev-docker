# syntax=docker/dockerfile:1
ARG BASE_IMAGE=debian:trixie-slim@sha256:a29215f6a35e51e22adffa17f89e9d2ef06214e64a2bad10d765c46aea49f11f
FROM ${BASE_IMAGE} AS compiler
ARG BUILD_JOBS=4
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates build-essential bison flex texinfo python3 xz-utils \
    libgmp-dev libmpfr-dev libmpc-dev zlib1g-dev libzstd-dev \
    && rm -rf /var/lib/apt/lists/*
COPY sources.lock.json /build/sources.lock.json
COPY scripts/fetch-sources.py scripts/build-compiler.sh /build/
RUN /build/build-compiler.sh

FROM compiler AS debugger
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreadline-dev libncurses-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*
COPY debugger.lock.json /build/debugger.lock.json
COPY scripts/build-debugger.sh /build/
RUN /build/build-debugger.sh
COPY scripts/strip-host-tools.py /build/
RUN python3 /build/strip-host-tools.py

FROM compiler AS megadev
RUN python3 /build/fetch-sources.py megadev \
    && mkdir /opt/megadev \
    && tar -xf /opt/sources/megadev.tar.gz --strip-components=1 -C /opt/megadev

FROM ${BASE_IMAGE} AS toolchain
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates make git python3 xz-utils genisoimage xxd \
    libgmp10 libmpfr6 libmpc3 libzstd1 zlib1g \
    libreadline8t64 libncursesw6 libpython3.13 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash megadev \
    && mkdir /workspace && chown megadev:megadev /workspace
COPY --from=debugger /opt/m68k /opt/m68k
COPY --from=megadev /opt/megadev /opt/megadev
COPY --from=megadev /opt/sources /usr/local/share/megadev/sources
COPY --from=debugger /opt/sources/gdb.tar.xz /usr/local/share/megadev/sources/gdb.tar.xz
COPY sources.lock.json debugger.lock.json /usr/local/share/megadev/
COPY scripts/build-compiler.sh scripts/build-debugger.sh scripts/fetch-sources.py \
    scripts/install-compiler-workarounds.py scripts/m68000-as.sh /usr/local/share/megadev/recipes/
RUN python3 /usr/local/share/megadev/recipes/install-compiler-workarounds.py \
    && chmod a+r /usr/local/share/megadev/sources/*
COPY scripts/entrypoint.sh /usr/local/bin/megadev
COPY scripts/doctor.sh /usr/local/bin/megadev-doctor
COPY scripts/project.py /usr/local/bin/megadev-project
ENV MEGADEV_PATH=/opt/megadev M68K_PREFIX=m68k-elf-
ENV PATH=/opt/m68k/bin:$PATH
LABEL org.opencontainers.image.title="Megadev toolchain" \
    org.opencontainers.image.description="Native ARM64 and AMD64 Sega CD development tools" \
    org.opencontainers.image.source="https://github.com/ewrogers/megadev-docker" \
    org.opencontainers.image.version="7a7246c-gcc16.2.0-binutils2.47"
USER megadev
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/megadev"]
CMD ["build"]
