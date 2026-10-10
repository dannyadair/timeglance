# CHANGELOG

<!-- version list -->

## v2.0.0 (2026-10-10)

### Bug Fixes

- Fit year and weekly previews to the pane for readability
  ([`7093f6c`](https://github.com/dannyadair/timeglance/commit/7093f6c6268f123bd28dcebbcb4508e6c9f3bf16))

### Documentation

- Correct the wallpaper filename and resolution description
  ([`7d8ea10`](https://github.com/dannyadair/timeglance/commit/7d8ea10ce051e9c4d22c812145ef3d7d7d2ec15c))

- Registry, per-planner schedule, overrides, disconnected/unseen screens
  ([`9b62230`](https://github.com/dannyadair/timeglance/commit/9b62230e482419524bfc32da16eecc80370319db))

### Features

- Consistent screen targeting in the wallpaper dialog and schedule panel
  ([`029fe7b`](https://github.com/dannyadair/timeglance/commit/029fe7b1f3b3a17d8b48cf61b7e102fe9875d5ba))

- Dedicated schedule.yaml with a trigger-agnostic runner
  ([`aed633c`](https://github.com/dannyadair/timeglance/commit/aed633c05e79f2a50049abe86acdc580ef92b682))

- Per-planner render overrides (YAML) in the schedule panel
  ([`25c1f24`](https://github.com/dannyadair/timeglance/commit/25c1f247e87044675e31a767154cdac2bbe51ca9))

- Per-planner schedule blocks with disconnected-screen targeting
  ([`ca47511`](https://github.com/dannyadair/timeglance/commit/ca475119e049f6ec12ad27a05e8a80b69e507e3e))

- Remember screens so disconnected ones stay targetable
  ([`f1099a0`](https://github.com/dannyadair/timeglance/commit/f1099a0a1e107e469bec293f8aa118cc8230ab5f))

- Rename weekly `activities`→`topics` and `blocks`→`activities`
  ([`9bd3a4a`](https://github.com/dannyadair/timeglance/commit/9bd3a4a5bf62b9603321819c75c8fe930fc06691))

- Surface configured-but-unseen screens as FYI instead of erroring
  ([`cd01ee7`](https://github.com/dannyadair/timeglance/commit/cd01ee72857ea976f7eb04d8693f4816d1a043ed))

### Refactoring

- Rename "tool" → "planner" throughout
  ([`a820515`](https://github.com/dannyadair/timeglance/commit/a8205158ca56b633f2df97e14c714fa0a0c5e043))

- Schedule.py into a Schedule class; extract format helpers
  ([`4d7fae0`](https://github.com/dannyadair/timeglance/commit/4d7fae0c2b1f23ad7a77e5cabc1a130d440f3f7b))

- Split app.js into native ES modules
  ([`321c2b0`](https://github.com/dannyadair/timeglance/commit/321c2b0d56dfd3581558ec07bc11a3b37fc4f665))

- Split serve.py into planners, scheduler, log and config modules
  ([`0c6db85`](https://github.com/dannyadair/timeglance/commit/0c6db859f857fa35303b91700436391336494502))

### Breaking Changes

- Weekly configs must rename `activities:`→`topics:`, `blocks:`→`activities:`, and each entry's
  `activity:` field to `topic:`.


## v1.3.0 (2026-10-10)

### Documentation

- Say "current resolution" not "native" for wallpaper rendering
  ([`56a2c0a`](https://github.com/dannyadair/timeglance/commit/56a2c0a6ce0d07fd5a96ea80c1ced957fe704dea))

### Features

- Show a spinner in the wallpaper dialog while setting
  ([`7a6dd6f`](https://github.com/dannyadair/timeglance/commit/7a6dd6f77804cdc958014b5239c0793284bfaf41))

- Stable per-screen wallpaper filenames so disconnected screens update on reconnect
  ([`cb36ddf`](https://github.com/dannyadair/timeglance/commit/cb36ddf47deedbe2414a7c3e85a569939e04ce4b))


## v1.2.0 (2026-10-09)

### Features

- In-app help popover for the year range-date notations
  ([#15](https://github.com/dannyadair/timeglance/pull/15),
  [`7d3844c`](https://github.com/dannyadair/timeglance/commit/7d3844ce4095d895c531c350398772f6ec74d0ea))


## v1.1.2 (2026-10-09)

### Bug Fixes

- Wallpaper dialog pre-selects screens from the YAML wallpaper.screens config
  ([#14](https://github.com/dannyadair/timeglance/pull/14),
  [`e175a74`](https://github.com/dannyadair/timeglance/commit/e175a746e791e1033e3acf0d8b436e97f87b3bff))


## v1.1.1 (2026-10-06)

### Bug Fixes

- Default the year template to the current year (span: this_year, auto title)
  ([#13](https://github.com/dannyadair/timeglance/pull/13),
  [`5e2d9d1`](https://github.com/dannyadair/timeglance/commit/5e2d9d10ba219b3132ba1ebee93e968946bcfcde))

### Documentation

- Add committed demo config + gitignore guards for reproducible screenshots
  ([#13](https://github.com/dannyadair/timeglance/pull/13),
  [`5e2d9d1`](https://github.com/dannyadair/timeglance/commit/5e2d9d10ba219b3132ba1ebee93e968946bcfcde))

- Add committed demo config + gitignore guards for reproducible screenshots
  ([#12](https://github.com/dannyadair/timeglance/pull/12),
  [`7816740`](https://github.com/dannyadair/timeglance/commit/7816740cecf286521e83c12646a7449d15755805))

- Refresh year planner screenshot for today-weekday highlight and 3-letter labels
  ([#11](https://github.com/dannyadair/timeglance/pull/11),
  [`2ca5c63`](https://github.com/dannyadair/timeglance/commit/2ca5c63a746676eef53c74a39476b4257966a47d))


## v1.1.0 (2026-10-06)

### Features

- Highlight today's weekday and use 3-letter labels in the year planner rail
  ([#10](https://github.com/dannyadair/timeglance/pull/10),
  [`b887519`](https://github.com/dannyadair/timeglance/commit/b88751940f1757af6de281c80d94173169d1dbf0))


## v1.0.3 (2026-10-03)

### Bug Fixes

- Scale year planner preview to fit the pane ([#3](https://github.com/dannyadair/timeglance/pull/3),
  [`5f18bf8`](https://github.com/dannyadair/timeglance/commit/5f18bf8aca19855c4f6609aaf727841af5ddb002))


## v1.0.2 (2026-10-03)

### Bug Fixes

- Republish README to PyPI so screenshots and badges render on the shop page
  ([#2](https://github.com/dannyadair/timeglance/pull/2),
  [`597e0d7`](https://github.com/dannyadair/timeglance/commit/597e0d7868ebc3e77b2a0410f8c241a3c7960cae))

### Continuous Integration

- Run tests/pre-commit on main, add OSSF Scorecard, enable PyPI badges
  ([`7c74ab3`](https://github.com/dannyadair/timeglance/commit/7c74ab327691476143cb89f10a2b3cd410c40015))


## v1.0.1 (2026-10-03)

### Bug Fixes

- Tidy and correct the control-panel --help text
  ([`d14dddd`](https://github.com/dannyadair/timeglance/commit/d14dddd86414ec5b3c9871343fe75b0f2bb3ea09))


## v1.0.0 (2026-10-03)

- Initial Release
