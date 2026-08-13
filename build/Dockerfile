# Build host for the CBPP image.
#
# The README used to install live-build inside a throwaway container on every
# single build, which re-downloaded the toolchain each time and made an offline
# rebuild impossible.  Building this image once and reusing it takes that cost
# out of the edit/build loop entirely.

ARG BASE=debian:trixie
FROM ${BASE}

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
	&& apt-get install -y \
		live-build \
		debootstrap \
		xorriso \
		squashfs-tools \
		zstd \
		zsync \
		rsync \
		ca-certificates \
		gnupg \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /build
