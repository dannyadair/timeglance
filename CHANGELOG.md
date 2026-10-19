# CHANGELOG

<!-- version list -->

## v3.10.0 (2026-10-19)

### Features

- **legend**: Configurable legend with empty/hidden add-ons
  ([`c70a411`](https://github.com/dannyadair/timeglance/commit/c70a41101329722ee5dea4cea9cce346373b2d4d))


## v3.9.3 (2026-10-19)

### Bug Fixes

- **year**: Show relative range tokens in the control panel
  ([`fb779cb`](https://github.com/dannyadair/timeglance/commit/fb779cbb997ac5260a4abd557499ffeb61b9358f))

### Build System

- **deps**: Bump actions/download-artifact from 4.3.0 to 8.0.2
  ([`66d1124`](https://github.com/dannyadair/timeglance/commit/66d11241c63aa504d1d85fce1b3a47e54c0d4523))

- **deps**: Bump actions/upload-artifact from 4.6.2 to 7.0.2
  ([`cc38b66`](https://github.com/dannyadair/timeglance/commit/cc38b660442fa2c55abe254c56c107c0584bcccb))

- **deps**: Bump ossf/scorecard-action from 2.4.4 to 2.5.0
  ([`a01cfe9`](https://github.com/dannyadair/timeglance/commit/a01cfe9c88ed6218b04f6045ec84255f869fd8ac))

- **deps-dev**: Bump pre-commit from 4.6.2 to 4.7.0
  ([`faa706f`](https://github.com/dannyadair/timeglance/commit/faa706fc3fca4c278036a1c2ddb30c1661b2ec20))

### Chores

- Gitignore local .cursor project config
  ([`47f0e3c`](https://github.com/dannyadair/timeglance/commit/47f0e3c725cf6c28e6b52ac9827879f14140b5eb))

- Point the project Homepage at timeglance.app
  ([`36b4ab9`](https://github.com/dannyadair/timeglance/commit/36b4ab95e8492b2d7c06cf6cd7ac25efe1823ba4))

### Documentation

- Add an illustration of the everyday productivity setup to motivation
  ([`f4b6d5b`](https://github.com/dannyadair/timeglance/commit/f4b6d5b42ec8e5ab312f338647890165da6dbae3))


## v3.9.2 (2026-10-17)

### Bug Fixes

- Fill the weekly page margin with the theme background
  ([`bebda49`](https://github.com/dannyadair/timeglance/commit/bebda491010507188f7478fe5cd6ebb461e0d76f))

### Documentation

- Refresh for the schedule dead switch, theme-driven wallpaper canvas and friendly screen names
  ([`b3de52f`](https://github.com/dannyadair/timeglance/commit/b3de52f4f853ac8bcd6511c802b55bc781778653))


## v3.9.1 (2026-10-17)

### Bug Fixes

- Make the dark wallpaper canvas actually dark
  ([`fe92ab3`](https://github.com/dannyadair/timeglance/commit/fe92ab3600056c04dddcc02c5fd2c431d64ced4a))


## v3.9.0 (2026-10-17)

### Documentation

- State test-adding policy for new functionality
  ([`f9774cf`](https://github.com/dannyadair/timeglance/commit/f9774cfb12ba4c9f4d85d7554c542b3c589e5ae0))

### Features

- Weekly wallpaper canvas follows the theme
  ([`2e59a23`](https://github.com/dannyadair/timeglance/commit/2e59a23a3e3aa4c0a17b538be5ceb6cc14fc7e50))


## v3.8.0 (2026-10-17)

### Features

- PySide6 system tray, schedule dead switch, friendly screen names
  ([`77a38ce`](https://github.com/dannyadair/timeglance/commit/77a38ced9fee91a92f60c66598bb0d8a0c1abc0c))


## v3.7.1 (2026-10-17)

### Bug Fixes

- Skip the tray test when no display backend is available
  ([`29cdb7f`](https://github.com/dannyadair/timeglance/commit/29cdb7fc69c64d2b6ff24e9f115ead17b5503faf))


## v3.7.0 (2026-10-17)

### Continuous Integration

- Run the full test suite per distro and report coverage to Codecov
  ([`c7306ca`](https://github.com/dannyadair/timeglance/commit/c7306ca6186afaf71cd17426479fdac669a58ac4))

- Run the full test suite per distro and report coverage to Codecov
  ([`5305fc1`](https://github.com/dannyadair/timeglance/commit/5305fc1a7e99c50e86323c96a0761bfa3b06fc2f))

### Features

- Control-panel version, layer all/none, Weekly-first order, paper from config
  ([`ed0d103`](https://github.com/dannyadair/timeglance/commit/ed0d10383d80e620d5bcbabdf232fe79be97ed08))

### Refactoring

- **config**: Group templates into settings / sources / events sections
  ([`9ceb341`](https://github.com/dannyadair/timeglance/commit/9ceb34164d744c39841ec25611884b820542f8b7))


## v3.6.0 (2026-10-17)

### Bug Fixes

- Top-align the control-panel preview (was vertically centred)
  ([`2885e55`](https://github.com/dannyadair/timeglance/commit/2885e551318f7fdef1566017538de721138b1435))

### Features

- Add a Sunday|Monday week divider to the aligned year grid
  ([`72e384f`](https://github.com/dannyadair/timeglance/commit/72e384fa5ad1842b8ce534289da2189927528bd9))

- Sharpen year weekdays and aligned day numbers, mark the current month
  ([`e4516d3`](https://github.com/dannyadair/timeglance/commit/e4516d3f5f14e994c3a1dbb6e2a3c9b0da0de70a))


## v3.5.5 (2026-10-16)

### Bug Fixes

- Don't paint disconnected screens' parked desktops
  ([`e57f11c`](https://github.com/dannyadair/timeglance/commit/e57f11c667f86a3e75acbc3f936f604ca2187660))

### Continuous Integration

- Pin CI deps and Docker base image by hash (OSSF Scorecard Pinned-Dependencies)
  ([`e1bffb1`](https://github.com/dannyadair/timeglance/commit/e1bffb142ab22c6a08bbf24a36d391fcb82635ec))


## v3.5.4 (2026-10-16)

### Bug Fixes

- Step-by-step wallpaper log, config-date errors, and override hint
  ([`7ace580`](https://github.com/dannyadair/timeglance/commit/7ace58009816690fc89b20562dcc3a483658e716))


## v3.5.3 (2026-10-16)

### Bug Fixes

- Size weekly day lanes in mm so blocks don't collapse on WeasyPrint 63-65
  ([`3900f51`](https://github.com/dannyadair/timeglance/commit/3900f5100ac5685547d257f22d20f44bada74f45))


## v3.5.2 (2026-10-16)

### Bug Fixes

- Keep year events in one lane across month boundaries
  ([`be1b695`](https://github.com/dannyadair/timeglance/commit/be1b69586fba75545208f699018fa73921ea428c))


## v3.5.1 (2026-10-16)

### Bug Fixes

- Lay weekly lanes out with flexbox so blocks fill their day lane
  ([`dc9a21b`](https://github.com/dannyadair/timeglance/commit/dc9a21b7bdb49536bf2539b4f56eab633c3323c3))


## v3.5.0 (2026-10-16)

### Continuous Integration

- Pin workflow actions by SHA and set minimal token permissions
  ([`2841847`](https://github.com/dannyadair/timeglance/commit/284184754c31bdaacfc99035aa612821bbfb918c))

### Features

- Sign released .deb with SLSA build provenance
  ([`1d28e47`](https://github.com/dannyadair/timeglance/commit/1d28e47bf25b613d5f3155074fa4766a76a8e3cf))

### Testing

- Add a render-correctness DEP-8 test
  ([`6079ef7`](https://github.com/dannyadair/timeglance/commit/6079ef7740a6b4d986f6dcdbca817d96146e3ac1))


## v3.4.2 (2026-10-13)

### Bug Fixes

- Weekly blocks collapse to text width on WeasyPrint < 63
  ([`da82eb0`](https://github.com/dannyadair/timeglance/commit/da82eb0402a80cd95f5e6e764486664fb0b48fc4))


## v3.4.1 (2026-10-13)

### Bug Fixes

- Keep blank query params so an empty hide shows all topics
  ([`a507da8`](https://github.com/dannyadair/timeglance/commit/a507da81a66b102aa743b471eb3595ed2adcaeec))


## v3.4.0 (2026-10-13)

### Features

- Lay out overlapping weekly activities side by side
  ([`99d44bb`](https://github.com/dannyadair/timeglance/commit/99d44bb880423ab75966218cc885aee18435180e))


## v3.3.5 (2026-10-13)

### Bug Fixes

- Make timeglance uninstall fully tear down user-level bits
  ([`714a3e4`](https://github.com/dannyadair/timeglance/commit/714a3e4073a50dde331eca7ceb89be55199624b1))


## v3.3.4 (2026-10-13)

### Bug Fixes

- Clearer timeglance uninstall output (disambiguate from systemctl)
  ([`65398e6`](https://github.com/dannyadair/timeglance/commit/65398e6fc2b09e04432b233396d513b4038ac0e8))

### Documentation

- Show rrule recurrence examples in the year config guide
  ([`6c30559`](https://github.com/dannyadair/timeglance/commit/6c30559cae843fb448365dbd472498fb7017f503))

- Tell Debian users to run timeglance uninstall before apt remove
  ([`afa34e9`](https://github.com/dannyadair/timeglance/commit/afa34e9fb6ec3d7567c38e2ec457cc5a4c1f2d08))


## v3.3.3 (2026-10-13)

### Bug Fixes

- Expand year-planner event bars to fill lanes free of overlap
  ([`7e899b7`](https://github.com/dannyadair/timeglance/commit/7e899b716600c5c132960a13eb99b10b9e195424))


## v3.3.2 (2026-10-11)

### Bug Fixes

- Build the .deb in an ubuntu:25.10 container
  ([`20de88b`](https://github.com/dannyadair/timeglance/commit/20de88be2c7b17fb1aea4bc663d695347d731794))


## v3.3.1 (2026-10-11)

### Bug Fixes

- Install build-essential in the .deb build job
  ([`6cd3704`](https://github.com/dannyadair/timeglance/commit/6cd3704f7c6cd83e5da90a13f45a3967b3199887))


## v3.3.0 (2026-10-11)

### Continuous Integration

- Attach the .deb without a checkout and gate PyPI on the deb matrix
  ([`732d62a`](https://github.com/dannyadair/timeglance/commit/732d62a2a1a829dc6df5138834b6570ecc1fc50e))

### Features

- Build the .deb as a proper Debian source package
  ([`31fc2cc`](https://github.com/dannyadair/timeglance/commit/31fc2cc241e0652c2a150b926b9da855b2dab859))


## v3.2.1 (2026-10-11)

### Bug Fixes

- Make the .deb installable on current Ubuntu
  ([`e36ebe3`](https://github.com/dannyadair/timeglance/commit/e36ebe3842cd0299affe81b766543c1e8d908933))

### Documentation

- Refresh control-panel screenshots for themes/layouts and the day/night toggle
  ([`b0612e4`](https://github.com/dannyadair/timeglance/commit/b0612e46f3b8f3967adb3a24702e5117fabc720e))


## v3.2.0 (2026-10-11)

### Documentation

- **weekly**: Document light/dark themes and vertical/horizontal layouts
  ([`4e4965a`](https://github.com/dannyadair/timeglance/commit/4e4965a83e981be26ccee827fac43898828d55f3))

### Features

- **panel**: Add a light/dark theme toggle for the control panel
  ([`55ad658`](https://github.com/dannyadair/timeglance/commit/55ad658d136354f4383a19053957f0e3cd816f53))

- **weekly**: Add light/dark themes and horizontal layout to the renderer
  ([`d6cabee`](https://github.com/dannyadair/timeglance/commit/d6cabee14465a8beb77b7b9b8c039ad35a04be1e))

- **weekly**: Expose themes and layouts in the CLI, control panel and wallpaper
  ([`ec88bb2`](https://github.com/dannyadair/timeglance/commit/ec88bb2ffb9323605d8a71319d9d16d45825b7d0))


## v3.1.0 (2026-10-11)

### Build System

- **deps**: Bump actions/upload-artifact from 7.0.1 to 7.0.2
  ([`d78d91a`](https://github.com/dannyadair/timeglance/commit/d78d91a5244e6c414d2560b7020d421becba5073))

- **deps**: Bump holidays from 0.105 to 0.106
  ([`56e7021`](https://github.com/dannyadair/timeglance/commit/56e7021d17e812f9b4da6840d26075d5fa43ecb4))

- **deps**: Bump pypdfium2 from 5.13.0 to 5.14.0
  ([`4a74dbd`](https://github.com/dannyadair/timeglance/commit/4a74dbd79f97609b8a802d5846d3f4235cfc61eb))

### Documentation

- Tray-in-.deb, Docker wallpaper framing, singular "sheet"
  ([`4a9732a`](https://github.com/dannyadair/timeglance/commit/4a9732a845b9d461c680a78b1f1263bd7b2b07ec))

### Features

- Ship the tray in the .deb with a desktop launcher
  ([`b5d5d1e`](https://github.com/dannyadair/timeglance/commit/b5d5d1e5227888bbc4bf921c55b3e38c5daf7a69))


## v3.0.0 (2026-10-11)

### Bug Fixes

- Control-panel first-run polish
  ([`ab2e908`](https://github.com/dannyadair/timeglance/commit/ab2e9083170806704dc4a2dfcbf66dadbbc43c84))

- Label the tray toggle "Autostart"
  ([`348afa5`](https://github.com/dannyadair/timeglance/commit/348afa54bd77570540c2347baf458a63bde463b6))

- Let the weekly legend fill the sheet width
  ([`73a6c79`](https://github.com/dannyadair/timeglance/commit/73a6c799d0f6aa6283044d6d34e0c9d438189c92))

- Log render resolution instead of file size
  ([`e5a7066`](https://github.com/dannyadair/timeglance/commit/e5a7066256e2f0c2dc851328aa6e48a6e1aac8f8))

- Widen the config editor so long YAML comments stop wrapping
  ([`f04d24f`](https://github.com/dannyadair/timeglance/commit/f04d24ffc6022275cb22bae632b848dd2bde1549))

- Year preview and init messaging on first run
  ([`d37f23d`](https://github.com/dannyadair/timeglance/commit/d37f23dfc017dc958c1915c5bfa6d25102f9e7ba))

### Chores

- Group year/weekly out/ with their configs in .gitignore
  ([`8399104`](https://github.com/dannyadair/timeglance/commit/8399104ea5bdbb14126652633db17f167affef26))

### Documentation

- Clarify tray install (uv run vs pipx)
  ([`07bd55d`](https://github.com/dannyadair/timeglance/commit/07bd55dcbdcd325e768a8b2fd5c3803bb370893b))

- Present Docker as a test drive, not a deployment target
  ([`e8626ad`](https://github.com/dannyadair/timeglance/commit/e8626ad6b0da0e5b191f37828b252cc640dd0c35))

- Refresh control-panel screenshots for the topics rename and preview fit
  ([`e1ab773`](https://github.com/dannyadair/timeglance/commit/e1ab773592cf59afa0f2d18e63e279496cadb422))

- Split install into Ubuntu/Debian (.deb) and Python/uv
  ([`3e2b0f1`](https://github.com/dannyadair/timeglance/commit/3e2b0f1d63fc9a0c5415db3a7b9b15f2f51ffe0d))

- Use uv run in the systemd section; clarify weekly wallpaper
  ([`e03bade`](https://github.com/dannyadair/timeglance/commit/e03bade65ddfe2eb949e33d193a88b5482094362))

### Features

- Add optional system tray controller
  ([`17759c8`](https://github.com/dannyadair/timeglance/commit/17759c8243cadb3a49b3d357eee83641eb42d178))

- Build a .deb and attach it to each release
  ([`0b0e58a`](https://github.com/dannyadair/timeglance/commit/0b0e58a7a4d89b10e9e907ddae8941381d7ed1bc))

- Consolidate entry points into a single timeglance CLI
  ([`d3a445b`](https://github.com/dannyadair/timeglance/commit/d3a445b38c011544892bee6fdf5541657530b04b))

- Narrate app lifecycle through the activity log
  ([`9a1efd6`](https://github.com/dannyadair/timeglance/commit/9a1efd6545a38e3aaa46c500b34307755a679d15))

- Resolve config/state/cache/output to XDG base directories
  ([`61b29b9`](https://github.com/dannyadair/timeglance/commit/61b29b95fc3a25d6d0e34c09a31d283d6d8788b2))

- Schedule screen reflects the real trigger, with Save and Install
  ([`91a3eaf`](https://github.com/dannyadair/timeglance/commit/91a3eaf62a7959327be60009765dd7927e6cd0c4))

- Support Python 3.12
  ([`3d9d69b`](https://github.com/dannyadair/timeglance/commit/3d9d69b87520af9c1fb9cce747b2929e5896f8a3))

- Timeglance install - nightly render via a systemd user timer
  ([`80ea5d8`](https://github.com/dannyadair/timeglance/commit/80ea5d875291fac40218193ef41fcacc10117c5f))

- Tray "Start at login" and a clearer tray --help
  ([`b0c713f`](https://github.com/dannyadair/timeglance/commit/b0c713fb0cb4667a3577b14caf53da86fa1e0091))

### Refactoring

- Name the render units timeglance-render.service/.timer
  ([`60620eb`](https://github.com/dannyadair/timeglance/commit/60620eb10e82cca52887a3b763781c7d43d784d2))


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
