## cbpp
# #!++, A CrunchBang revival project.

In 2015, Philip Newborough -- Corenominal -- had officially discontinued his efforts with the fast and light distro. While Philip believes that the project no longer serves the Linux space in the way he had originally intended, we believe that #! still has great potential and serves the Linux community as the perfect combination of elegance and efficiency.

While we intend to keep the distro very much the same as it has been over the years, some changes must be made to adapt to newer dependencies. Most notably, #!++ will have a new gtk3 theme and a new default iconset using the faenza-crunchbang-icon-theme package.

A few more changes have been made under the hood over the years with the advent of systemd, the deprecation of slim and some userspace utilities, the changes to gtk-3.0 and soon gtk-4.0, but the original experience is largely unchanged.

Lastly, we'd like to thank Philip for all his hard work through the years, the legacy he's created, and the bar he's set for sleek high-performance distros.

### The ISO

In this repository, you'll find the sources used to generate the actual system image, with installer, along with some configurations.

### Building

Everything the image is configured with lives in `cbpp.conf` at the root of the
repository. Edit a value there, then let the Makefile stamp it through the
live-build tree under `config/`:

```
$ $EDITOR cbpp.conf
$ make apply show      # stamp it in, and print exactly what changed
$ make build           # full ISO build, in docker
```

`make apply`, `make show`, `make diff` and `make lint` are plain shell, need no
docker, and run in well under a second. `make lint` catches the things
live-build itself will not tell you about until half an hour into a build.

After the first build, re-spin only the parts you actually changed:

| Target | Rebuilds | Use it after changing |
| --- | --- | --- |
| `make rebuild` | the ISO, reusing the chroot | bootloader, splash, kernel cmdline, ISO label, squashfs compression |
| `make rechroot` | the chroot, reusing the bootstrap | package lists, hooks, chroot includes, kernel |
| `make build` | everything | suite, architecture, mirrors |

`make apt-cache` starts a caching apt proxy, which takes most of the download
cost out of repeated chroot rebuilds. `make help` lists every target.

See [docs/fast-iteration.ru.md](docs/fast-iteration.ru.md) for the details.

If you would rather not use docker, run live-build directly as root. Note the
`touch .build/config`: it stops live-build from regenerating `config/` and
discarding everything this repository tracks.

```
# apt-get update && apt-get install -y live-build && mkdir -p .build && touch .build/config && lb build
```

### Packages

For the most part, CBPP is just a thin layer of configuration files added on top of Debian Stable. However, we do package those files for distribution. While the packages have been made available at several URLs over the years, you can currently find them at:

- Committed in binary form at [CBPP/crunchbangplusplus.org/packages](https://github.com/CBPP/packages.crunchbangplusplus.org)
- Hosted for consumption via apt at [crunchbangplusplus.org/packages](crunchbangplusplus.org/packages) though not browseable in the web browser(yet)

### Package Sources

All of the sources for CBPP's custom packages are available here on Github

- [cbpp-metapackage](https://github.com/CBPP/cbpp-metapackage) - a virtual package responsible for pulling in all of the packages required to build the entire environment, literally just a list of dependencies
- [cbpp-exit](https://github.com/CBPP/cbpp-exit) - a python script which presents a gtk window of logout/power options
- [cbpp-pipemenus](https://github.com/CBPP/cbpp-pipemenus) - pipemenus (dynamic menu items) for the Openbox menu, and supporting scripts
- [cbpp-configs](https://github.com/CBPP/cbpp-configs) - the meat and potatoes of crunchbang configuration, mostly dotfiles
- [cbpp-welcome](https://github.com/CBPP/cbpp-welcome) - source for the welcome script that runs on first boot
- [cbpp-lxdm-theme](https://github.com/CBPP/cbpp-lxdm-theme) - theme and config file for lxdm
- [obmenu](https://github.com/CBPP/obmenu) - a configuration tool for openbox menus
- [obapps](https://github.com/CBPP/obapps) - a configuration tool for openbox application settings
- [cbpp-wallpapers](https://github.com/CBPP/cbpp-wallpapers) - wallpapers
- [cbpp-ui-theme](https://github.com/CBPP/cbpp-ui-theme) - Default UI themes (gtk, openbox, etc)
- [cbpp-icon-theme](https://github.com/CBPP/cbpp-icon-theme) - Default icon theme (a desaturated fork of faenza)