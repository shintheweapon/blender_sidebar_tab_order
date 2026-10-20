# Sidebar Tab Order

A Blender 4.5 extension that puts the tabs of the 3D Viewport sidebar (the N panel) in the order you choose.

## Use

1. Install `dist\sidebar_tab_order-<version>.zip`: Edit > Preferences > Get Extensions > the menu at the top right > Install from Disk.
2. In Edit > Preferences > Add-ons > Sidebar Tab Order, the list shows every sidebar tab.
3. Select a tab and move it with the up and down buttons.
4. Click **Apply**.

The order is saved with your preferences and applied each time Blender starts. **Refresh List** adds tabs from add-ons enabled since, at the end of the list, and removes tabs that no longer exist.

## How it works

Blender shows the sidebar tabs in the order in which each tab's first panel appears in its list of panel types. A newly registered panel goes behind the last panel whose `bl_order` is the same or lower. The add-on unregisters every sidebar panel and registers them again tab by tab. Each top-level panel gets a temporary `bl_order` of its tab's place × 1000 plus its own `bl_order`, so the panels inside each tab keep their order.

## Limits

- **Item always comes first.** Its Transform and Vertex Weights panels are built into Blender (written in C) and cannot be registered again from Python.
- **A tab can jump to the front in some modes.** A panel without a header goes ahead of every panel with one. Tool has two such panels, which show only in some modes. While one of them is shown, Tool comes first, as it does without this add-on.
- **Re-enabling an add-on** puts its tab at the end until you click Apply or restart Blender.
- **Tabs whose panels are hidden** in the current context (for example Rigify's, outside a rig) stay in the list but do not show.

## Develop

```
blender.exe --factory-startup -b -P tests/run_tests.py
blender.exe --factory-startup -b --command extension validate src
.\build.ps1
```

`src\order.py` holds Blender's ordering rule and the plan in plain Python. `src\tabs.py` applies the plan to Blender's panels, and `src\prefs.py` holds the preferences, the list and its commands.
