# CBPP image build.
#
# Editing loop:
#     $EDITOR cbpp.conf     # change a line
#     make apply show       # stamp it into config/ and see exactly what moved
#     make rebuild          # re-spin only the ISO, reusing the chroot
#
# apply / show / diff / lint are pure local shell and take well under a second.
# Only the build targets need docker.

SHELL := /bin/sh
.DEFAULT_GOAL := help

# cbpp.conf is shell, so make reads the quotes as part of each value; strip them
# off the handful of settings this file actually uses.
include cbpp.conf
unquote = $(patsubst "%",%,$(1))

ARCH := $(call unquote,$(CBPP_ARCH))
BUILD_IMAGE := $(call unquote,$(CBPP_BUILD_IMAGE))
BUILD_BASE := $(call unquote,$(CBPP_BUILD_BASE))

PWD_ABS := $(shell pwd)
ISO := live-image-$(ARCH).hybrid.iso

# -it breaks when stdin is not a terminal (CI, `make | tee`), so only ask for it
# when we actually have one.
DOCKER_TTY := $(shell [ -t 0 ] && echo -it)

# live-build needs to manipulate loop devices and mounts, hence the privileges.
DOCKER_RUN = docker run --rm $(DOCKER_TTY) \
	--privileged --cap-add=ALL \
	-v /proc:/proc -v /sys:/sys \
	-v $(PWD_ABS):/build -w /build \
	$(BUILD_IMAGE)

# The config stagefile has to exist or live-build refuses to run a stage. We
# create it by hand rather than running `lb config`, which would regenerate
# config/ from scratch and throw away everything tracked in this repo.
STAGE = mkdir -p .build && touch .build/config

.PHONY: help apply show diff lint check image build rebuild rechroot shell \
	clean clean-cache distclean apt-cache qemu ci

help:
	@echo 'Fast (local, no docker, instant):'
	@echo '  make apply        stamp cbpp.conf into config/'
	@echo '  make show         effective settings + everything that changed'
	@echo '  make diff         git diff of cbpp.conf and config/'
	@echo '  make lint         static checks live-build will not do for you'
	@echo '  make check        apply + lint'
	@echo
	@echo 'Build (docker):'
	@echo '  make image        build the builder container (once, then cached)'
	@echo '  make build        full ISO build from scratch'
	@echo '  make rebuild      re-spin the ISO only, keeping the chroot  <- fast path'
	@echo '  make rechroot     redo the chroot stage, keeping the bootstrap'
	@echo '  make shell        shell inside the builder, repo mounted at /build'
	@echo
	@echo 'Housekeeping:'
	@echo '  make apt-cache    start a caching apt proxy for much faster rebuilds'
	@echo '  make clean        drop build artefacts, keep the package cache'
	@echo '  make clean-cache  drop the downloaded package cache'
	@echo '  make distclean    drop everything'
	@echo '  make qemu         boot $(ISO) in qemu'

# -- local, instant ---------------------------------------------------------

apply:
	@scripts/cbpp-apply

show:
	@scripts/cbpp-show

diff:
	@git --no-pager diff -- cbpp.conf config

lint:
	@scripts/cbpp-lint

check: apply lint

ci:
	@scripts/cbpp-apply --check --quiet
	@scripts/cbpp-lint

# -- build ------------------------------------------------------------------

image:
	docker build --build-arg BASE=$(BUILD_BASE) -t $(BUILD_IMAGE) build/

build: check image
	@$(STAGE)
	$(DOCKER_RUN) lb build
	@ls -lh $(ISO) 2>/dev/null || true

# Everything that lives in the binary stage - bootloader configs and splashes,
# the kernel command line, the ISO volume label, squashfs compression - only
# needs this. It reuses the bootstrapped and populated chroot, which is where
# nearly all of a full build's time goes.
rebuild: check image
	@test -d chroot || { echo 'no chroot/ yet - run `make build` first'; exit 1; }
	@$(STAGE)
	$(DOCKER_RUN) lb clean --binary
	@$(STAGE)
	$(DOCKER_RUN) lb binary
	@ls -lh $(ISO) 2>/dev/null || true

# Package list or hook changes need the chroot rebuilt, but the debootstrap
# tarball is cached and reused.
rechroot: check image
	@$(STAGE)
	$(DOCKER_RUN) lb clean --chroot
	@$(STAGE)
	$(DOCKER_RUN) lb build
	@ls -lh $(ISO) 2>/dev/null || true

shell: image
	@$(STAGE)
	$(DOCKER_RUN) /bin/bash

# -- housekeeping -----------------------------------------------------------

# apt-cacher-ng in front of the Debian mirror turns the ~1.5 GB of package
# downloads in a fresh chroot build into a local disk read on every rebuild
# after the first.
apt-cache:
	@docker rm -f cbpp-apt-cache >/dev/null 2>&1 || true
	docker run -d --name cbpp-apt-cache -p 3142:3142 \
		-v cbpp-apt-cache-data:/var/cache/apt-cacher-ng \
		sameersbn/apt-cacher-ng
	@echo
	@echo 'Now set this in cbpp.conf and run `make apply`:'
	@echo '  CBPP_APT_PROXY="http://172.17.0.1:3142"'

clean: image
	@$(STAGE)
	$(DOCKER_RUN) lb clean

clean-cache: image
	@$(STAGE)
	$(DOCKER_RUN) lb clean --cache

distclean: image
	@$(STAGE)
	$(DOCKER_RUN) lb clean --purge

qemu:
	@test -f $(ISO) || { echo 'no $(ISO) - run `make build` first'; exit 1; }
	@command -v qemu-system-x86_64 >/dev/null || { \
		echo 'qemu-system-x86_64 not installed'; exit 1; }
	qemu-system-x86_64 -m 2048 -enable-kvm -cdrom $(ISO) -boot d
