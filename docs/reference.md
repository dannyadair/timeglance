# Reference

Precedence everywhere is **built-in defaults < YAML < CLI flags**. All planners share `--data PATH`, `--out DIR`,
`--wallpaper`, `--screen NAMES`, and `--list-screens`. Working data (`config.yaml`, `out/`, `state/`) resolves from
the current directory; override the project root with the `TIMEGLANCE_HOME` environment variable.

## Weekly - `timeglance-weekly` (or `python -m timeglance.weekly.build`)

| Flag              | YAML       | Values / default                  | Notes                                             |
| ----------------- | ---------- | --------------------------------- | ------------------------------------------------- |
| `--paper`         | `paper`    | `A4` \| `A3` (default `A4`)       | Landscape page size; sets the timeline height.    |
| `--format`        | `format`   | `pdf` \| `html` \| `both` (`pdf`) | `both` writes `weekly.pdf` **and** `weekly.html`. |
| `--only IDS`      | -          | comma list of activity ids        | Show only these activities.                       |
| `--hide ACTIVITY` | `visible:` | repeatable                        | Hide an activity id (adds to YAML defaults).      |
| `--wallpaper`     | -          | flag                              | Set the sheet as the desktop wallpaper.           |

**`weekly/config.yaml`**

| Key                    | Type / values                               | Meaning                                                                                              |
| ---------------------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `title`, `subtitle`    | string                                      | Header text.                                                                                         |
| `paper`                | `A4` \| `A3` (default `A4`)                 | Page size (landscape).                                                                               |
| `format`               | `pdf` \| `html` \| `both` (default `pdf`)   | Output(s) written to `out/`.                                                                         |
| `days`                 | list, e.g. `[Mon, …, Sun]`                  | Columns, in order.                                                                                   |
| `day_start`, `day_end` | `HH:MM`                                     | Vertical extent of the timeline.                                                                     |
| `hour_marks`           | int (hours; default `1`)                    | Spacing of the hour gridlines.                                                                       |
| `activities`           | map `id → {label, color, visible}`          | Catalogue; `visible: false` hides an activity by default.                                            |
| `blocks`               | list `{days, start, end, activity, label?}` | Scheduled blocks; `label` defaults to the activity label.                                            |
| `wallpaper`            | `{background, margin, screens, shadow}`     | `margin` is a fraction of the short edge; `shadow: false` off, or `{opacity, blur, offset, radius}`. |

## Year - `timeglance-year` (or `python -m timeglance.year.build`)

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

| Key               | Type / values                                           | Meaning                                                                                                                       |
| ----------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `title`           | string; omit → from range                               | Header title.                                                                                                                 |
| `range`           | `{start, end}` or `{span, before?, after?}`             | Tokens: `today`, `today±N` (months), `year-start`, `year-end`, `YYYY-MM`. `span`: `this_year` \| `upcoming_year` \| `custom`. |
| `week_start`      | `Mon` \| `Sun`                                          |                                                                                                                               |
| `theme`, `layout` | see flags above                                         | Omit to render all variants.                                                                                                  |
| `week_align`      | bool (default `true`)                                   | Weekday-aligned slots (weekends in bands) vs days packed 1..31 flush.                                                         |
| `show_today`      | bool                                                    | Box around today.                                                                                                             |
| `dim_past`        | bool                                                    | Fade days before today.                                                                                                       |
| `sizes`           | map `name → WxH`                                        | Named sizes for `size` / `--size`.                                                                                            |
| `size`            | named or `WxH`                                          | Output dimensions.                                                                                                            |
| `holidays`        | `{country, subdiv, layer, observed}`                    | Auto-populated via the `holidays` package.                                                                                    |
| `sources`         | list `{url\|path, layer?, label?, color?, refresh?}`    | iCalendar feeds merged into the stream; `refresh` (s) caches URLs.                                                            |
| `wallpaper`       | `{screens, fill, theme?, layout?, week_align?}`         | `fill`: `preserveAspectCrop` \| `preserveAspectFit` \| `stretch` \| `tile` \| `pad`.                                          |
| `layers`          | list `{id, label, color, visible}`                      | Event groups; toggle with `visible` / `--only` / `--hide`.                                                                    |
| `events`          | list `{layer, date \| start+end, label, repeat\|rrule}` | Single day = `date`; span = `start`+`end` (inclusive); `repeat: yearly\|weekly\|monthly` or full `rrule:`.                    |
