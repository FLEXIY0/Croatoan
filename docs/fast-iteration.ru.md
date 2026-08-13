# Быстрая правка и сборка CBPP

Цель — чтобы правка «пары строк» не превращалась в получасовую пересборку.

## Как это устроено

Раньше все настройки образа были размазаны по десятку файлов в `config/`:
версия релиза лежала в метке тома ISO, кодовое имя Debian — отдельно в
`config/bootstrap`, в `config/binary`, в двух файлах `config/archives/*`, в
скрипте `usr/lib/cbpp/apt-setup` и в хуке установки ядра. Смена релиза
означала правку в шести местах, и любое забытое место всплывало только в
собранном образе.

Теперь единственный источник правды — **`cbpp.conf`** в корне репозитория.
`make apply` разносит его значения по всем производным файлам.

```
cbpp.conf  ──make apply──▶  config/common
                            config/bootstrap
                            config/chroot
                            config/binary
                            config/build
                            config/archives/cbpp.list.{binary,chroot}
                            config/hooks/normal/0990-backports-kernel.hook.chroot
                            config/includes.chroot_after_packages/.../apt-setup
```

`apply` трогает только те ключи, которыми владеет `cbpp.conf`. Всё остальное
в `config/` можно спокойно править руками — оно переживёт `make apply`.

## Цикл правки

```sh
$EDITOR cbpp.conf     # изменили одну строку
make apply show       # разнесли по конфигам и увидели, что именно изменилось
make rebuild          # пересобрали только ISO, chroot переиспользуется
```

`apply`, `show`, `diff`, `lint` — чистый shell, работают меньше секунды и
docker им не нужен.

### `make show`

Печатает три вещи: итоговые настройки образа (уже с раскрытыми производными
значениями — полное имя пакета ядра, метка тома, адрес архива), список
пакетов, и полный diff `cbpp.conf` + `config/` относительно HEAD. Это и есть
ответ на вопрос «покажи результат изменений».

### `make lint`

Ловит то, о чём live-build молчит и что иначе выясняется через полчаса сборки
или, хуже, в уже собранном образе:

- `config/` разошёлся с `cbpp.conf`;
- **обе** директории `config/hooks/normal` и `config/hooks/live` непусты —
  `chroot_hooks` в live-build заходит в цикл выполнения хуков только если в
  `normal/` есть `*.chroot` **и** в `live/` есть `*.chroot` или `*.container`.
  Опустошите любую из них — и молча не выполнится **ни один** хук;
- хуки исполняемые и синтаксически валидные;
- `CBPP_KERNEL` не заканчивается на `-amd64` — live-build сам дописывает
  флейвор, и получилось бы `linux-image-amd64-amd64`;
- метка тома ISO укладывается в 32 символа ISO9660 уже после раскрытия
  `@ISOVOLUME_TS@`;
- кодовое имя Debian согласовано между архивами и debian-installer;
- в списке пакетов нет CRLF (apt воспримет `\r` как часть имени пакета);
- шаблоны загрузчика не потеряли подстановки `@LINUX@`, `@INITRD@`,
  `@APPEND_LIVE@`.

## Сборка

| Цель | Что делает | Когда нужна |
|---|---|---|
| `make image` | собирает контейнер-сборщик | один раз, дальше из кэша |
| `make build` | полная сборка с нуля | первый раз, смена релиза |
| `make rebuild` | **только** binary-стадия | правки загрузчика, splash, cmdline, метки тома, сжатия squashfs |
| `make rechroot` | пересборка chroot, bootstrap из кэша | правки списка пакетов и хуков |
| `make shell` | shell внутри сборщика | разбор полётов |

`make rebuild` — главный быстрый путь. Почти всё время полной сборки уходит
на debootstrap и установку пакетов в chroot; всё, что живёт в binary-стадии,
переспинывается отдельно и переиспользует готовый chroot.

Что именно требует какой цели:

- **`make rebuild`** — `CBPP_VERSION`, `CBPP_BOOTAPPEND_*`, `CBPP_MEMTEST`,
  `CBPP_ZSYNC`, `CBPP_SQUASHFS_*`, всё в `config/bootloaders/`.
- **`make rechroot`** — `config/package-lists/`, `config/hooks/`,
  `config/includes.chroot*`, `CBPP_KERNEL*`, `CBPP_INITRAMFS_COMPRESSION`.
- **`make build`** — `CBPP_DISTRIBUTION`, `CBPP_ARCH`, зеркала.

### Кэширующий apt-прокси

Самая большая статья расходов при пересборке chroot — повторная выкачка
~1.5 ГБ пакетов.

```sh
make apt-cache                          # поднимает apt-cacher-ng
$EDITOR cbpp.conf                       # CBPP_APT_PROXY="http://172.17.0.1:3142"
make apply
```

После этого каждая следующая пересборка chroot читает пакеты с локального
диска.

`CBPP_CACHE_INDICES="true"` (значение по умолчанию) дополнительно кэширует
файлы `Packages` между сборками. Если понадобится свежий индекс —
`make clean-cache`.

## Почему `lb config` не запускается

`make` создаёт stage-файл `.build/config` вручную. `lb config` перегенерировал
бы всё дерево `config/` с нуля и снёс бы то, что версионируется в этом
репозитории. Именно поэтому в исходном README стоял `touch .build/config` —
здесь это просто вынесено в `Makefile`.
