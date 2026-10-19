# Reference

One command with subcommands: `timeglance serve` (control panel), `timeglance render year|weekly` (one-shot render,
flags below), `timeglance init` (scaffold configs), `timeglance install` / `uninstall` (systemd user timer for the
scheduled render), `timeglance run` (render the scheduled planners once - what the timer invokes), and
`timeglance tray` (system-tray launcher + schedule toggles, needs the `[tray]` extra).

Precedence everywhere is **built-in defaults < YAML < CLI flags**. All planners share `--data PATH`, `--out DIR`,
`--wallpaper`, `--screen NAMES`, and `--list-screens`. Working data follows the XDG base directories by default -
config in `~/.config/timeglance/`, state in `~/.local/state/timeglance/`, cache in `~/.cache/timeglance/`, rendered
output in `~/.local/share/timeglance/` - or set `TIMEGLANCE_HOME` to put it all under one root (config and output at
the root, state and cache beneath it), the layout Docker and the dev loop use.

## Weekly - `timeglance render weekly` (or `python -m timeglance.weekly.build`)

| Flag           | YAML       | Values / default                                           | Notes                                              |
| -------------- | ---------- | ---------------------------------------------------------- | -------------------------------------------------- |
| `--theme`      | `theme`    | `light` \| `dark` \| comma; omit → all                     | One value → single variant; omitted → render both. |
| `--layout`     | `layout`   | `vertical` (default) \| `horizontal` \| comma; omit → both | Orientation: days as columns vs rows.              |
| `--paper`      | `paper`    | `A4` \| `A3` (default `A4`)                                | Landscape page size; sets the timeline height.     |
| `--format`     | `format`   | `pdf` \| `html` \| `both` (`pdf`)                          | `both` writes `weekly.pdf` **and** `weekly.html`.  |
| `--only IDS`   | -          | comma list of topic ids                                    | Show only these topics.                            |
| `--hide TOPIC` | `visible:` | repeatable                                                 | Hide a topic id (adds to YAML defaults).           |
| `--wallpaper`  | -          | flag                                                       | Set the sheet as the desktop wallpaper.            |

**`weekly/config.yaml`**

| Key                                                        | Type / values                              | Meaning                                                                                                                                                           |
| ---------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`, `subtitle`                                        | string                                     | Header text.                                                                                                                                                      |
| `theme`, `layout`                                          | see flags above                            | Light/dark palette and orientation (days as columns vs rows); omit to render all.                                                                                 |
| `paper`                                                    | `A4` \| `A3` (default `A4`)                | Page size (landscape).                                                                                                                                            |
| `format`                                                   | `pdf` \| `html` \| `both` (default `pdf`)  | Output(s) written to `out/`.                                                                                                                                      |
| `days`                                                     | list, e.g. `[Mon, …, Sun]`                 | Columns, in order.                                                                                                                                                |
| `day_start`, `day_end`                                     | `HH:MM`                                    | Vertical extent of the timeline.                                                                                                                                  |
| `hour_marks`                                               | int (hours; default `1`)                   | Spacing of the hour gridlines.                                                                                                                                    |
| `show_legend` / `show_legend_empty` / `show_legend_hidden` | bool (defaults `true` / `false` / `false`) | Draw the colour key; the `_empty` / `_hidden` add-ons also list activity-free or toggled-off topics (greyed), and apply only while `show_legend` is on.           |
| `topics`                                                   | map `id → {label, color, visible}`         | Catalogue; `visible: false` hides a topic by default.                                                                                                             |
| `activities`                                               | list `{days, start, end, topic, label?}`   | Scheduled activities; `label` defaults to the topic label.                                                                                                        |
| `wallpaper`                                                | `{background, margin, screens, shadow}`    | `background: auto` (default) follows the theme, or a colour; `margin` is a fraction of the short edge; `shadow: false` off, or `{opacity, blur, offset, radius}`. |

## Year - `timeglance render year` (or `python -m timeglance.year.build`)

| Flag                               | YAML         | Values / default                                           | Notes                                                                       |
| ---------------------------------- | ------------ | ---------------------------------------------------------- | --------------------------------------------------------------------------- |
| `--theme`                          | `theme`      | `light` \| `dark` \| comma; omit → all                     | One value → single variant; omitted → render both.                          |
| `--layout`                         | `layout`     | `vertical` (default) \| `horizontal` \| comma; omit → both | Orientation: months as columns vs rows.                                     |
| `--week-align` / `--no-week-align` | `week_align` | default `true`                                             | Weekday-aligned slots vs days packed 1..31 flush.                           |
| `--week-start`                     | `week_start` | `Mon` \| `Sun`                                             |                                                                             |
| `--only IDS`                       | -            | comma list of layer ids                                    | Show only these layers.                                                     |
| `--hide LAYER`                     | `visible:`   | repeatable                                                 | Hide a layer id.                                                            |
| `--size`                           | `size`       | named (from `sizes:`) or `WxH`                             | e.g. `laptop` or `3440x1440`.                                               |
| `--wallpaper`                      | -            | flag                                                       | Variant = single `--theme`/`--layout` > `wallpaper.theme/layout` > default. |

**`year/config.yaml`**

| Key                                                        | Type / values                                           | Meaning                                                                                                                                              |
| ---------------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`                                                    | string; omit → from range                               | Header title.                                                                                                                                        |
| `range`                                                    | `{start, end}` or `{span, before?, after?}`             | Tokens: `today`, `today±N` (months), `year-start`, `year-end`, `YYYY-MM`. `span`: `this_year` \| `upcoming_year` \| `custom`.                        |
| `week_start`                                               | `Mon` \| `Sun`                                          |                                                                                                                                                      |
| `theme`, `layout`                                          | see flags above                                         | Omit to render all variants.                                                                                                                         |
| `week_align`                                               | bool (default `true`)                                   | Weekday-aligned slots (weekends in bands) vs days packed 1..31 flush.                                                                                |
| `show_today`                                               | bool                                                    | Box around today.                                                                                                                                    |
| `dim_past`                                                 | bool                                                    | Fade days before today.                                                                                                                              |
| `show_legend` / `show_legend_empty` / `show_legend_hidden` | bool (defaults `true` / `false` / `false`)              | Draw the colour key; the `_empty` / `_hidden` add-ons also list event-free or toggled-off layers (greyed), and apply only while `show_legend` is on. |
| `sizes`                                                    | map `name → WxH`                                        | Named sizes for `size` / `--size`.                                                                                                                   |
| `size`                                                     | named or `WxH`                                          | Output dimensions.                                                                                                                                   |
| `holidays`                                                 | `{country, subdiv, layer, observed}`                    | Auto-populated via the `holidays` package.                                                                                                           |
| `sources`                                                  | list `{url\|path, layer?, label?, color?, refresh?}`    | iCalendar feeds merged into the stream; `refresh` (s) caches URLs.                                                                                   |
| `wallpaper`                                                | `{screens, fill, theme?, layout?, week_align?}`         | `fill`: `preserveAspectCrop` \| `preserveAspectFit` \| `stretch` \| `tile` \| `pad`.                                                                 |
| `layers`                                                   | list `{id, label, color, visible}`                      | Event groups; toggle with `visible` / `--only` / `--hide`.                                                                                           |
| `events`                                                   | list `{layer, date \| start+end, label, repeat\|rrule}` | Single day = `date`; span = `start`+`end` (inclusive); `repeat: yearly\|weekly\|monthly` or full `rrule:`.                                           |

## Schedule - `schedule.yaml`

Drives the daily re-render (`timeglance run`, the timer, the in-server loop) and the panel's **Schedule** view. It
lives in the state directory; the panel writes it, but it's plain YAML you can hand-edit.

| Key         | Type / values                  | Meaning                                                                                                                                                                                                            |
| ----------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `enabled`   | bool (default `true`)          | The dead switch. When `false`, every _automatic_ render is skipped (timer, in-server loop and `timeglance run` all no-op); the panel's **Render now** bypasses it.                                                 |
| `time`      | `HH:MM` (default `06:00`)      | Local time of the daily render.                                                                                                                                                                                    |
| `planners`  | list, e.g. `[weekly, year]`    | Which planners the scheduled run renders.                                                                                                                                                                          |
| `<planner>` | `{wallpaper, screens, render}` | Per-planner block: `wallpaper: true` also sets the render as the desktop wallpaper; `screens` targets outputs (default all); `render:` overrides the scheduled render (same keys as that planner's `config.yaml`). |
