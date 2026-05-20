# MAST GUI Overview

## Note to Mission Writers

Few mission writers will need to leverage the GUI capabilities of MAST outside of comms buttons and science scans. Those capabilites are documented elsewhere.  
The GUI capabilites described here are much more invovled and are probably unncessary unless you have found a need for major UI changes.

## Overview

In sbs_utils, GUI calls do not immediately draw to screen. They build pending layout objects on the current page, then `await gui()` activates that queued layout for interaction.

The runtime flow is:

1. Build layout containers (`gui_section`, `gui_sub_section`, `gui_region`, `gui_row`).
2. Add controls/content to the active layout context.
3. Bind interaction through labels, `on gui_message(...)`, `on change ...`, or `var` values.
4. Call `await gui()` to swap in the active GUI promise and wait for input.
5. Handle the event and usually jump back to a view label to redraw or refresh.

This is the same pattern used throughout LegendaryMissions (for example in the console selection, server menu, and gamemaster screens): build several sections/rows, register change/message handlers, then `await gui()` at the end of the label.

Practical mental model:

- Layout calls define structure.
- Element calls fill that structure.
- Event bindings define behavior.
- `await gui()` makes the screen live.
- Handler labels update state and return to a render label.

---


## Row/Column Layout Model

The most important layout rule is this:

- Inside a `gui_section`, `gui_sub_section`, or `gui_region` container, content is laid out in rows.
- Inside each row, most GUI calls create columns.
- A `gui_row()` call starts a new row.

That means layout is naturally grid-like, even if you never define an explicit grid.

```python
with gui_section():
    gui_button()
    gui_row()
    gui_button()
    gui_button()
```

How this renders:

- Row 1 has one column, so the first button stretches across the full row.
- Row 2 has two columns, so the two buttons split that row evenly.

Style attributes then modify space usage:

- `row-height` changes row height.
- `col-width` changes how wide a column wants to be.
- `area` sets container bounds.
- `padding`/`margin` adjust internal and external spacing.

### `gui_sub_section`

A `gui_sub_section` behaves like a nested layout container inside the current row. It occupies a column in the parent layout, and then its own contents are laid out using rows and columns inside that smaller area.

```python
with gui_section("area:10,10,90,90;"):
    with gui_sub_section("col-width:40%;"):
        gui_text("$text: Left Panel")
        gui_row()
        gui_button("Overview")
        gui_button("Details")

    with gui_sub_section("col-width:60%;"):
        gui_text("$text: Right Panel")
        gui_row()
        gui_text_area("$text: This subsection has its own internal rows and columns.")
```

Here the parent section is split into two columns, and each column gets its own internal row/column flow.

---

## Event Block Overview

MAST GUI code uses three event block styles. They all follow the same idea: watch for an event, run a small handler block, and then continue or redraw as needed.

### `on gui_message(...)` (button/message-style events)

Use this when you want to handle a direct message from a specific GUI element instance.

- Most common inline form: `on gui_message(gui_button("...")):`
- Also works with stored widget references, like inputs or custom controls.
- Best for local, explicit interactions where the control and its handler are close together.

```python
gui_row()
on gui_message(gui_button("Apply")):
    # Immediate action for this specific button
    jump apply_settings
```

### `on change ...` (value/state change events)

Use this when behavior should run whenever a value changes, not just when a button is clicked.

- Works with GUI values (`ship_select_lb.get_value()`, `picker.get_selected_index()`, `var_name`, etc.).
- Great for reactive UI updates (show/hide regions, refresh details, update previews).
- Keep handlers lightweight to avoid redraw loops or noisy updates.

```python
on change mission_picker.get_selected_index():
    selected_mission = mission_picker.get_value()
    jump show_server_menu
```

### `on signal ...` (cross-system or shared events)

Use this for broader events emitted by gameplay systems, comms systems, or shared mission logic.

- Signals are good for decoupling UI from gameplay producers.
- Useful when UI must react to events not caused by local widget interaction.
- In practice, often followed by a jump or scheduled sub-task to refresh relevant UI state.

```python
on signal player_ship_destroyed:
    await delay_app(0)
    jump select_console_clear_ship
```

### Use of event blocks

- Use `on gui_message(...)` for direct per-widget actions.
- Use `on change ...` for reactive data-driven UI behavior.
- Use `on signal ...` for signal-driven changes.

All three can be used in one screen label in any combination.

---

## One Cohesive Example

This example pulls the earlier sections together into one screen: one outer section, two subsection columns, variable-driven controls, and all three event block styles.

```python
== settings_screen
    # Defaults make the screen stable on first render and after resets.
    default status_text = "Adjust the settings, then apply them."
    default difficulty = "Normal"
    default friendly_fire = False
    default spawn_rate = 50

    # One outer container for the whole settings UI.
    gui_section(style="area:10,10,90,90;padding:0.5em;")

    # Header row.
    gui_row(style="row-height:2.2em;")
    gui_text(props="$text: Mission Settings")

    # Left column: navigation/status.
    with gui_sub_section("col-width:35%;padding:0,0.5em,0,0;"):
        gui_row(style="row-height:1.6em;")
        gui_text(props="$text: Sections")

        gui_row()
        gui_button("General", on_press="settings_screen")
        gui_button("Advanced", on_press="settings_screen")

        gui_row(style="row-height:1.6em;")
        gui_text(props="$text: Status")

        gui_row()
        gui_text_area(props=f"$text: {status_text}")

    # Right column: editable settings controls.
    with gui_sub_section("col-width:65%;"):
        gui_row()
        gui_text(props="$text: Difficulty")
        gui_drop_down(props="Easy,Normal,Hard", var="difficulty")

        gui_row()
        gui_text(props="$text: Friendly Fire")
        gui_checkbox(msg="Enable", var="friendly_fire")

        gui_row()
        gui_text(props="$text: Spawn Rate")
        gui_slider(msg="0,100", var="spawn_rate")

        gui_row(style="row-height:2.2em;")
        # Direct per-widget message handling for action buttons.
        on gui_message(gui_button("Apply")):
            jump apply_settings
        on gui_message(gui_button("Close")):
            jump close_settings

    # Reactive update when a bound value changes.
    on change difficulty:
        status_text = f"Difficulty changed to {difficulty}."
        jump settings_screen

    # External/shared event hook.
    on signal reset_settings:
        difficulty = "Normal"
        friendly_fire = False
        spawn_rate = 50
        status_text = "Settings reset from signal."
        jump settings_screen

    # Activate queued layout and wait for interaction.
    await gui()

== apply_settings
    # Read back values from GUI task variables.
    current_difficulty = gui_get_variable("difficulty")
    current_friendly_fire = gui_get_variable("friendly_fire")
    current_spawn_rate = gui_get_variable("spawn_rate")

    # Update status, then redraw the same screen.
    status_text = f"Applied: {current_difficulty}, FF={current_friendly_fire}, Spawn={current_spawn_rate}"
    jump settings_screen

== close_settings
    # In a real flow this would usually jump to another label/menu.
    status_text = "Settings screen closed."
    jump settings_screen
```


---

## Additional Variations

### 1. Screen + Handler Pair

The smallest useful GUI pattern is one render label and one handler label.

```python
== inventory_screen
    gui_section(style="area:20,20,80,80;")

    gui_row(style="row-height:2em;")
    gui_text(props="$text: Inventory")

    gui_row()
    gui_button("Sort", on_press="inventory_sort")
    await gui()

== inventory_sort
    # Sort data, then redraw
    jump inventory_screen
```

### 2. Variable-Driven Controls

Controls that write to `var` can all be read back in the same way.

```python
== controls_demo
    gui_section(style="area:15,15,85,85;")

    gui_row()
    gui_text(props="$text: Captain Name")
    gui_input(props="$text: Name", var="captain_name")

    gui_row()
    gui_text(props="$text: Route")
    gui_radio("Alpha,Beta,Gamma", var="route")

    gui_row()
    gui_text(props="$text: Threat Level")
    gui_int_slider(msg="1,10", var="threat_level")

    gui_row(style="row-height:2em;")
    gui_button("Continue", on_press="read_values")
    await gui()

== read_values
    captain_name = gui_get_variable("captain_name")
    route = gui_get_variable("route")
    threat_level = gui_get_variable("threat_level")
```

### 3. List UIs

List boxes are the usual choice when the number of items is dynamic.

```python
== ship_picker
    ships = ~~ ["TSN Artemis", "TSN Valkyrie", "TSN Aegis"] ~~

    gui_section(style="area:15,10,85,90;")
    gui_row(style="row-height:2em;")
    gui_text(props="$text: Select a Ship")

    gui_row()
    gui_list_box(items=ships, style="background:#1572;", select=True)

    gui_row(style="row-height:2em;")
    gui_button("Select", on_press="ship_pick_confirm")
    await gui()
```

---

## Layout and Styling Guidelines

- Start with one top-level `gui_section` and define `area` first.
- Keep style strings minimal and consistent.
- Use percentage geometry for most screens, then add `px`/`em` where precision matters.

Style strings are semicolon-separated property lists. They can be applied to sections, rows, and most controls.

```python
style="area:10,10,90,90;padding:0.5em;background-color:#102030;"
```

### Common layout properties

- `area` places a section or region within its parent or screen.
- `row-height` controls how tall a row should be.
- `col-width` controls how wide a column or subsection wants to be.
- `padding` adds space inside the element.
- `margin` adds space outside the element.

### Common visual properties

- `background` or `background-color` sets background fill.
- `color` sets text color.
- `justify` aligns text or button content, usually `left`, `center`, or `right`.
- `font` selects a specific GUI font when needed.
- `tag` gives an element or row a useful name for later updates.

### Units and expressions

Styles can mix several sizing styles:

- Plain numbers are usually percentages.
- `px` gives fixed pixel sizes.
- `em` scales relative to text size.
- Expressions such as `100-50px` or `41+1em` are common for offsets from edges.

Examples used in the codebase:

```python
gui_section(style="area:0,45px,100,100;")
gui_section(style="area:50-200px,0,50+200px,50px;")
gui_row(style="row-height:45px;margin:0,0,0,10px;")
with gui_sub_section("col-width:280px;"):
```

### Style usage patterns

#### Full-screen shell + fixed header

Use percentages for the main shell, then fixed pixel offsets for top or bottom bars.

```python
gui_section(style="area:0,0,100,100;")
gui_section(style="area:0,45px,100,100;")
```

#### Split panels

Use `col-width` on subsections when one side should stay narrow and the other should expand.

```python
with gui_sub_section("col-width:280px;"):
    gui_text("$text: Navigation")

with gui_sub_section("col-width:70;"):
    gui_text("$text: Detail View")
```

#### Compact action rows

Use row height and margin together to create denser button or toggle strips.

```python
gui_row("row-height:35px;margin:0,0,0,10px;")
gui_button("Apply", style="justify:center;")
```

#### Styled list panels

List boxes commonly carry much of the visible panel styling.

```python
gui_list_box(items, "row-height:7em;background:#1578;", select=True)
gui_list_box(items, "background:#1572;padding:0,0,10px,0;", select=True)
```

