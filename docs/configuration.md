# Configuration

Working configs (`year/config.yaml`, `weekly/config.yaml`) are git-ignored (personal schedule / calendar
secrets); the packaged `config.yaml.in` files are annotated templates. Run `timeglance init` to scaffold the
working configs from them (or just start `timeglance serve`, which creates samples when none exist). Precedence is **built-in defaults < YAML < CLI flags**, so you can comment defaults out
rather than delete them.

See the [Reference](reference.md) for the full list of flags and YAML keys.

## Year (`year/config.yaml`)

- **`range`** - `start`/`end` accept `today`, `today±N` (months), `year-start`, `year-end`, or `YYYY-MM`.
  A shorter range renders larger. Or set a `span` preset instead of `start`/`end`: `this_year`,
  `upcoming_year` (rolling 12 from this month), or `custom` with `before`/`after` month counts.
- **`holidays`** - auto-populated via the [`holidays`](https://pypi.org/project/holidays/) package
  (`country` + `subdiv`, e.g. `NZ` / `WGN`).
- **`sources`** - external iCalendar feeds (see below).
- **`layers`** / **`events`** - a single day uses `date:`, a span uses `start:`+`end:` (inclusive); recurrence via
  `repeat: yearly|weekly|monthly` or a full `rrule:` (RFC 5545 / dateutil).

### Recurring events

`repeat:` covers the common cases; `rrule:` takes any RFC 5545 rule (parsed by
[`dateutil`](https://dateutil.readthedocs.io/en/stable/rrule.html#dateutil.rrule.rrulestr)) for everything
else. The event's `date:` (or `start:`) is the recurrence anchor (`DTSTART`). Omit it and an `rrule:` anchors
at the start of the render window — which only matters for `INTERVAL` rules. A `start:`+`end:` span keeps its
length on every occurrence, and `repeat: yearly` clamps a Feb-29 anchor to Feb-28 in non-leap years.

```yaml
events:
  # repeat: shorthands (anchor = date/start)
  - { layer: birthdays, date: 1990-02-14, label: Alex, repeat: yearly } # same day every year
  - { layer: work, date: 2026-01-05, label: Standup, repeat: weekly } # same weekday every week
  - { layer: work, date: 2026-01-01, label: Rent due, repeat: monthly } # same day every month

  # rrule: everything else (quote the string)
  - {
      layer: work,
      date: 2026-01-05,
      label: Weekdays,
      rrule: "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
    }
  - {
      layer: work,
      date: 2026-01-07,
      label: Fortnightly,
      rrule: "FREQ=WEEKLY;INTERVAL=2",
    }
  - { layer: meetups, label: Python meetup, rrule: "FREQ=MONTHLY;BYDAY=+3TH" } # 3rd Thursday (no anchor needed)
  - {
      layer: meetups,
      label: Last-Friday drinks,
      rrule: "FREQ=MONTHLY;BYDAY=-1FR",
    } # last Friday
  - {
      layer: work,
      date: 2026-01-01,
      label: Quarterly review,
      rrule: "FREQ=MONTHLY;INTERVAL=3",
    }
  - {
      layer: leave,
      date: 2026-07-04,
      label: Independence Day,
      rrule: "FREQ=YEARLY;BYMONTH=7;BYMONTHDAY=4",
    }
  - {
      layer: work,
      date: 2026-01-05,
      label: Sprint demo,
      rrule: "FREQ=WEEKLY;INTERVAL=2;COUNT=10",
    }
  - {
      layer: work,
      date: 2026-01-05,
      label: Weekly check-in,
      rrule: "FREQ=WEEKLY;UNTIL=20260401",
    }
```

Stop an open-ended rule with `COUNT=N` (N occurrences) or `UNTIL=YYYYMMDD` (inclusive), as in the last two above.

### Calendar sources (.ics)

Let your existing calendars _be_ the editor. Any number of `.ics` feeds are merged into the event stream and mapped
to a layer:

```yaml
sources:
  - url: "https://calendar.proton.me/api/calendar/v1/url/…/calendar.ics" # a Proton share link
    layer: birthdays
  - path: "~/calendars/my-year.ics" # a local file
    label: My Year # creates a layer if `layer:` is omitted
    color: "#7A7F87"
```

Recurrences, `EXDATE`s and all-day/timed spans are expanded within the render window. URL feeds are TTL-cached
(`refresh:` seconds) in the cache directory (`~/.cache/timeglance/ics-cache`), and a failed refresh falls back to the last good copy. Nice trick:
keep a private "year" calendar you never show online and only export here.

> **A share link is a secret.** Proton links embed a passphrase key. Keep them in your git-ignored `config.yaml`,
> never in the tracked `config.yaml.in`.

## Weekly (`weekly/config.yaml`)

`topics` (label + colour; `visible: false` hides one by default) and a flat list of `activities`. Toggle any
topic in the UI (or with `--hide`/`--only`); comment out a single activity to drop a one-off. `theme`
(`light`/`dark`) and `layout` (`vertical` days-as-columns / `horizontal` days-as-rows) pick the palette and
orientation. `wallpaper:` tunes the canvas `background`, `margin`, `shadow`, and `screens`.
