# Research: iPhone Widget Tech Choice — Scriptable vs Native WidgetKit

**Issue:** #107 (child of #106 "iPhone Weather Widget")
**Date:** 2026-08-13
**Goal being served:** Home-screen widget showing today's temp trend chart, light-intensity trend chart, and wind-speed distribution, fetched from a new public no-auth `doGet` JSON endpoint on the existing Apps Script.
**Constraint:** User has zero Swift/Xcode/Scriptable experience.

---

## TL;DR recommendation

**Scriptable.** It runs entirely on the iPhone (no Mac needed), is free, supports small/medium/large home-screen widgets, and its `DrawContext` API is sufficient to draw a sparkline and a histogram. WidgetKit is technically capable of more polished, native charts (via the Swift Charts framework) and does **not** require a paid Apple Developer account for personal-device installs — but it requires a Mac + Xcode + learning Swift/SwiftUI, which is a much bigger lift for a zero-experience hobbyist than the stated goal justifies.

---

## 1. Cost breakdown (the single most important fact, verified)

**Verified claim: a free Apple ID + Xcode is enough to build and run a WidgetKit widget on your own personal iPhone. The $99/year Apple Developer Program fee is NOT required for this.**

Source — Apple's own official FAQ, "Do I need to enroll in the Apple Developer Program to develop and run apps on my devices?":

> "No. You can install apps on your personal device with Xcode. You'll only need to enroll if you'd like to distribute apps, access beta software, and integrate with capabilities such as Siri, Apple Pay, and iCloud."
— [Apple Developer — Program Enrollment Help](https://developer.apple.com/help/account/membership/program-enrollment/)

This is corroborated by Apple's Swift Student Challenge page, which states a plain Apple Account (no paid program) is enough to "test your apps on your devices" using Xcode, Swift Playground, and related tools.

**Practical caveat found during research (not from Apple's FAQ page directly, but consistent across community/forum sources referencing Apple's provisioning behavior):** the "free provisioning" / Personal Team signing method has real limitations that matter for a hobbyist:
- Signing certificates issued this way expire roughly every **7 days**, requiring the widget to be rebuilt and reinstalled from Xcode weekly to keep working.
- A free account is capped at a small number of App IDs it can register concurrently (historically ~10 per rolling week across an Apple ID) and a low device-registration ceiling.
- No access to TestFlight, App Store distribution, push notifications, iCloud, or other capabilities requiring "App Services" entitlements — irrelevant here since the goal is a purely personal local widget with no push/iCloud dependency.

Net cost: **$0** either way for "install on my own phone only." Scriptable adds **$0** with no recurring build/re-sign chore. WidgetKit via free provisioning is also **$0** but comes with a recurring 7-day re-sign maintenance burden unless the user later pays $99/yr for a permanent signing certificate.

Sources:
- [Apple Developer — Program Enrollment FAQ](https://developer.apple.com/help/account/membership/program-enrollment/)
- [Apple Developer Program — Membership Details](https://developer.apple.com/programs/whats-included/) (confirms paid-tier scope: beta OS, App Store, CloudKit, Push Notifications, etc. — none of which are needed for a personal local widget)

---

## 2. Setup / tooling needed

### Scriptable
- **iOS-only app, no Mac required.** Everything — writing the script, testing, and adding the widget to the home screen — happens on the iPhone itself.
- Install once from the App Store (free, with optional tip-jar in-app purchases).
- Write JavaScript (ES6) directly in the app's in-app code editor; long-press home screen → add widget → choose Scriptable → pick script + size.

Source: [Scriptable on the App Store](https://apps.apple.com/us/app/scriptable/id1405459188) — "Free" app, category Developer Tools, compatible with iPhone/iPad, no Mac mentioned or needed; [Scriptable website](https://scriptable.app/) — "Automate iOS using JavaScript."

### WidgetKit
- **Requires a Mac** running Xcode (Xcode itself is free from the Mac App Store, but a Mac is mandatory — there is no iOS/iPadOS-only path to build a WidgetKit extension).
- Requires learning Swift + SwiftUI (WidgetKit widgets are built as SwiftUI views inside a Widget Extension target).
- Build/run/install flow: write code in Xcode → connect iPhone via cable or same-network wireless debugging → Xcode signs with the free "Personal Team" and installs directly to the device → re-sign every ~7 days if using free provisioning.

Source: [Apple Developer — Program Enrollment FAQ](https://developer.apple.com/help/account/membership/program-enrollment/) (confirms Xcode is the install mechanism); general WidgetKit framework documentation confirms SwiftUI is the view layer for widget extensions ([WidgetKit — SwiftUI views for widgets](https://developer.apple.com/documentation/widgetkit/swiftui-views), [Building Widgets Using WidgetKit and SwiftUI](https://developer.apple.com/documentation/widgetkit/building-widgets-using-widgetkit-and-swiftui)).

**This is a hard blocker consideration:** if the user does not own a Mac, WidgetKit is not viable at all regardless of cost. (Not stated in the ticket whether a Mac is available — flag this to the user explicitly.)

---

## 3. Chart rendering capability

### Scriptable — `DrawContext`
Scriptable's `DrawContext` API is a low-level 2D canvas: `fillRect`/`strokeRect`, `fillEllipse`/`strokeEllipse`, custom paths (`addPath`), `drawText`/`drawTextInRect`, `drawImageInRect`/`drawImageAtPoint`, plus stroke/fill color and line-width control. It renders to an `Image` object via `getImage()`, which can then be set as a widget's background image or dropped into a `WidgetImage` element inside a `ListWidget`/`WidgetStack` layout.

- There is **no built-in chart type** — a sparkline (temp/light trend) or histogram (wind-speed distribution) must be hand-drawn using paths/rects/lines. This is straightforward for a sparkline (poly-line through normalized points) and a histogram (a series of `fillRect` bars), but it is manual coding, not a chart library call.
- Because it renders to a static `Image`, this works within widget rendering constraints without special handling — the widget just displays a pre-rendered PNG-like image, which is cheap and reliable.

Source: [Scriptable Docs — DrawContext](https://docs.scriptable.app/drawcontext/), [Scriptable Docs — ListWidget](https://docs.scriptable.app/listwidget/)

### WidgetKit — Swift Charts
Apple's **Swift Charts** framework (introduced WWDC22) is a native SwiftUI charting library — line charts, bar charts, and more — built with declarative syntax, and it is usable inside SwiftUI views, including WidgetKit widget views. This would give a more polished, native-feeling chart with less manual pixel-math than Scriptable's `DrawContext`, at the cost of needing to learn both SwiftUI and Swift Charts' declarative API.

Source: [Apple Developer — Swift Charts](https://developer.apple.com/documentation/charts), [WWDC22 — "Hello Swift Charts"](https://developer.apple.com/videos/play/wwdc2022/10136/), [WWDC23 — "Explore pie charts and interactivity in Swift Charts"](https://developer.apple.com/videos/play/wwdc2023/10037/)

### Refresh budget / static-vs-live constraints (applies to both)
Widgets on iOS are fundamentally **snapshot-based, not live views** — regardless of Scriptable or WidgetKit, a widget renders a fixed snapshot of a SwiftUI/Scriptable view/image at a point in time and the OS decides when to re-render it next; there is no continuously-running/animating code inside a widget.
- Apple's own widget documentation states the refresh cadence is **system-determined**, not developer-controlled — influenced by device battery level, how often the user views the widget, and a background "refresh budget" iOS allocates per widget per day (commonly cited informally as on the order of tens of refreshes/day, but Apple deliberately does not publish an exact guaranteed number — it's adaptive).
- Scriptable's own docs describe this identically: *"The widget will refresh periodically and the rate at which the widget refreshes is largely determined by the operating system."* (Source: [Scriptable Docs — ListWidget](https://docs.scriptable.app/listwidget/))
- Both platforms let the developer set a "please don't refresh me before this time" hint (WidgetKit: `TimelineEntry`/`Timeline` reload policy; Scriptable: `refreshAfterDate`) but neither guarantees exact timing — iOS treats it as a lower bound, not a schedule.
- Scriptable explicitly documents a **memory limit for widget execution**, separate from the full-app memory ceiling: *"There are memory limitations when running a script in a widget. When using too much memory the widget will crash and not render correctly."* This matters if the JS fetches + processes a full day of sensor data client-side inside the widget — keep the payload/parsing lightweight (which aligns well with the plan to have the Apps Script pre-aggregate into a compact JSON endpoint rather than shipping raw rows).

For this project's use case (widget refreshes a few times a day showing "today's" trend so far), the OS-controlled refresh budget is not a practical blocker for either technology — a weather station doesn't need second-by-second widget updates.

---

## 4. Home-screen widget size support

Both support the standard home-screen sizes:

- **WidgetKit** (`WidgetFamily` enum): `systemSmall`, `systemMedium`, `systemLarge`, and `systemExtraLarge` (iPad only), plus Lock Screen accessory families (`accessoryCircular`, `accessoryRectangular`, `accessoryInline`) on iOS 16+. Confirmed via Apple's documentation index for `WidgetFamily.systemMedium` and `WidgetFamily.systemLarge`. ([Apple Developer — WidgetFamily.systemMedium](https://developer.apple.com/documentation/widgetkit/widgetfamily/systemmedium), [WidgetFamily.systemLarge](https://developer.apple.com/documentation/widgetkit/widgetfamily/systemlarge))
- **Scriptable**: small, medium, large home-screen sizes, extra-large (iPad, iOS 15+), and the same three Lock Screen accessory sizes (inline, circular, rectangular) on iOS 16+. (Source: [Scriptable Docs — ListWidget](https://docs.scriptable.app/listwidget/))

Given three charts are wanted (temp trend, light trend, wind distribution), a **medium or large** widget size will be needed to fit more than one chart per widget, or three separate small widgets can be placed side by side — this is a layout decision independent of which technology is chosen.

---

## 5. Hard blockers for a zero-experience hobbyist

| Factor | Scriptable | WidgetKit |
|---|---|---|
| Requires a Mac | No | **Yes** — Xcode is Mac-only |
| Requires learning a new language | JavaScript (likely already familiar-ish, and this repo's `payload_formatter` is already JS) | Swift + SwiftUI (new language + new declarative UI paradigm) |
| Apple Developer account signup | Not needed — just install from App Store with existing Apple ID | Free Apple ID sufficient for local install (verified above), but Xcode account setup, provisioning profiles, and code signing are extra concepts to learn |
| Cost | $0 | $0 for personal use (verified); $99/yr only if later wanting App Store distribution or avoiding the 7-day re-sign cycle |
| Maintenance overhead | None — script keeps working indefinitely once installed | Re-build & re-install from Xcode roughly every 7 days under free provisioning, or pay $99/yr to avoid this |
| Chart rendering | Manual pixel-level drawing via `DrawContext` (no chart library) | Native declarative charts via Swift Charts, but requires learning SwiftUI first |
| Existing project overlap | Fetching JSON + transforming data is conceptually identical to the existing `payload_formatter` JS work in this repo | No overlap with existing repo skills |

**Bottom line for a zero-Swift/Xcode/Scriptable hobbyist:** WidgetKit's "free for personal use" cost claim is confirmed true, so cost is not the deciding factor. The deciding factors are (a) the mandatory Mac dependency, (b) the Swift/SwiftUI learning curve, and (c) the recurring 7-day re-signing chore under free provisioning. Scriptable removes all three: no Mac, JavaScript (which this project already uses for the TTN payload formatter), and no re-signing since it's a normal App Store app, not a self-signed dev build.

---

## Sources (primary, consulted directly)

- [Apple Developer — Program Enrollment FAQ](https://developer.apple.com/help/account/membership/program-enrollment/) — confirms free personal-device installs, paid-only features
- [Apple Developer Program — Membership Details](https://developer.apple.com/programs/whats-included/) — confirms scope of paid tier
- [Apple Developer — WidgetKit framework index](https://developer.apple.com/documentation/widgetkit)
- [Apple Developer — SwiftUI views for widgets](https://developer.apple.com/documentation/widgetkit/swiftui-views)
- [Apple Developer — Building Widgets Using WidgetKit and SwiftUI](https://developer.apple.com/documentation/widgetkit/building-widgets-using-widgetkit-and-swiftui)
- [Apple Developer — WidgetFamily.systemMedium](https://developer.apple.com/documentation/widgetkit/widgetfamily/systemmedium)
- [Apple Developer — WidgetFamily.systemLarge](https://developer.apple.com/documentation/widgetkit/widgetfamily/systemlarge)
- [Apple Developer — Swift Charts](https://developer.apple.com/documentation/charts)
- [WWDC22 — Hello Swift Charts](https://developer.apple.com/videos/play/wwdc2022/10136/)
- [WWDC23 — Explore pie charts and interactivity in Swift Charts](https://developer.apple.com/videos/play/wwdc2023/10037/)
- [Scriptable — official website](https://scriptable.app/)
- [Scriptable — App Store listing](https://apps.apple.com/us/app/scriptable/id1405459188)
- [Scriptable Docs — DrawContext](https://docs.scriptable.app/drawcontext/)
- [Scriptable Docs — ListWidget](https://docs.scriptable.app/listwidget/)

## Open question to flag back to the human

Does the user own a Mac? This single fact eliminates WidgetKit as an option entirely if the answer is no, independent of everything else in this report.
