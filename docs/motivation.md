# Motivation

I use [Todoist](https://todoist.com) for a [GTD](https://en.wikipedia.org/wiki/Getting_Things_Done) approach to the things I do. Real appointments live in _one_ calendar. I follow
[Inbox Zero](https://en.wikipedia.org/wiki/Inbox_Zero), keep a Post-it pad on the fridge for shopping, and use a digital notepad ([Boox](https://www.boox.com)) for daily
scribbling. That's all the magic, really - and it works very well.

But there were two gaps in my setup:

- **Weekly routine** - my _planned_ schedule of when I do what in general: getting up, work time, break time,
  cooking, exercise, bed time. Recurring Todoist tasks would be silly, and wouldn't give me the "overview" I'm after.
- **Year planner** - I love the 20,000-ft view of an old-school wall planner. The real ones have two problems:
  editing is cumbersome and unforgiving, and "the year" becomes fairly useless by November/December.

So I grabbed my mate Claude and built timeglance to fill those gaps:

- **Weekly** - simple YAML config; I want to see it in a browser, print it on paper, and set it as a wallpaper.
- **Year** - same, but with a bit more power: pull in existing `.ics` calendars, and control the layout - e.g. a
  _rolling_ year instead of staring at 10 months of history in November. I'm ok with entering school holidays from the government website manually, but public holidays should be automatic.

Pulling in `.ics` calendars means I can keep birthdays and other "layers" where they already are - maybe a dedicated calendar just for this overview - and leave calendar editing to my existing calendar software.

Both of these have a notion of "today", and they're just images - so I also wanted a nightly re-render, to highlight the current day (and advance the rolling-year view).

I use [Kubuntu](https://kubuntu.org/) ([KDE](https://kde.org/) [Plasma](https://kde.org/plasma-desktop/)), where each screen can have its own wallpaper. I never store files on the desktop, so it's only windows sitting on top of the wallpaper. My laptop is often connected to an ultrawide monitor:

- Weekly as the wallpaper on the laptop
- Year as the wallpaper on the widescreen monitor
- Nightly refresh to sync calendars and update "today" highlighting

A quick [Meta](https://en.wikipedia.org/wiki/Meta_key)+D gives me that glance I wanted.

You may be in a similar situation. I'm grateful for any and all ideas and PRs - patches welcome!
