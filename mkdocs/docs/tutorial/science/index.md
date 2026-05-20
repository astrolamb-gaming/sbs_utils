# MAST Science Overview

## Overview

Science in MAST is route-driven. You do not usually build science interactions from a normal mission label. Instead, you define route labels that run when a science console scans a target.

The core model is:

1. Enable science for matching targets.
2. Define scan tabs for those same targets.
3. Return scan text (and optionally run logic) when a tab is used.

---

## Science Route Variables

When science routes run, these variables are available:

- `SCIENCE_ORIGIN_ID`: id of the player ship doing the scan.
- `SCIENCE_ORIGIN`: object of the player ship doing the scan.
- `SCIENCE_SELECTED_ID`: id of the scanned target.
- `SCIENCE_SELECTED`: object of the scanned target.

These are the primary variables you use for logic inside the route labels.

---

## Minimal Setup

Use both routes with matching conditions:

```python
//enable/science if has_role(SCIENCE_SELECTED_ID, "wreck")

//science if has_role(SCIENCE_SELECTED_ID, "wreck")
	+ "scan":
		<scan>
			% Battle-scarred wreckage with severe hull rupture.
```

Why both are needed:

- `//enable/science` makes targets eligible for science processing.
- `//science` defines what tabs/results are shown when scanned.

---

## Scan Tabs and Results

Each `+ "tab name":` block creates one science tab button. Inside the block, `<scan>` returns the result text.

```python
//science if has_role(SCIENCE_SELECTED_ID, "wreck")
	+ "scan":
		<scan>
			% Hulk of a destroyed starship.
			% Debris field indicates catastrophic reactor failure.

	+ "status":
		<scan>
			% Radiation leak detected. Boarding not advised.

	+ "bio":
		<scan>
			% No life signs detected.
```

Notes:

- Multiple `%` lines inside `<scan>` are used as random variations - one of these will be selected when scanning is complete.
- Keep tab names short and purpose-specific (`scan`, `status`, `bio`, `intel`).

---

## One Cohesive Example

This example shows a complete science flow for a hidden treasure asteroid.

```python
# Enable science only for treasure asteroids.
//enable/science if has_role(SCIENCE_SELECTED_ID, "treasure")

# Provide science tabs/results for those same targets.
//science if has_role(SCIENCE_SELECTED_ID, "treasure")
	+ "scan":
		<scan>
			% This asteroid has unusual radiation pockets.
			% Scans show inconsistent internal density.

	+ "status":
		<scan>
			% A dense inner core is surrounded by weaker outer material.
			% Recommend precision fire to expose the center.

	+ "intel":
		<scan>
			% Passive signatures match a concealed metallic object.

		# Optional mission logic triggered by scanning this tab.
		if not get_inventory_value(SCIENCE_SELECTED_ID, "treasure_discovered", False):
			set_inventory_value(SCIENCE_SELECTED_ID, "treasure_discovered", True)
			signal_emit("treasure_found", {"target_id": SCIENCE_SELECTED_ID})
```

Why this pattern works:

- The route condition is consistent between enable/scan routes.
- Tabs separate player-facing information by purpose.
- Scan actions can push mission state forward without needing GUI labels.

---

## Advanced Variations

### Procedural/Scripted Updates

For dynamic cases (debug tools, special consoles, or scripted actors), you can set scan data directly:

```python
science_set_scan_data(SCIENCE_ORIGIN_ID, SCIENCE_SELECTED_ID, "Some Custom Scan Text")
```

You can also redirect a science focus in scripted flows:

```python
set_science_selection(SCIENCE_ORIGIN_ID, SCIENCE_SELECTED_ID)
```

These are useful for admin/debug experiences, but most mission content should stay route-based.
