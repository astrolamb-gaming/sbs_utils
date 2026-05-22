# Torpedoes

This page covers how to create and use custom torpedo types in MAST missions.

The core process looks like this:

1. Define a torpedo type by function call or prefab.
2. Make that torpedo type available to player ships.
3. (Optional) Add custom behavior when that torpedo hits something.
4. (Optional) Add production capability to stations.

## Define a custom torpedo type

Use `torpedo_type()` when you want clear named arguments.

```py
~~ torpedo_type(
	key="Tag",
	gui_text="Tag",
	speed=12,
	lifetime=20,
	flare_color="yellow",
	trail_color="#99f",
	warhead="standard",
	damage=0,
	explosion_size=1,
	explosion_color="white",
	behavior="homing",
	energy_conversion_value=25
) ~~
```

Important fields:

- `key`: Internal id for the torpedo type. This is also used in ship data keys like `Tag_NUM` and `Tag_MAX`.
- `gui_text`: Name shown in the weapons UI.
- `warhead`: Comma-separated behavior flags. Common values are `standard`, `blast`, and `reduce_shields`.
- `behavior`: Guidance behavior (`homing` or `mine`).
- `damage`, `blast_radius`, `explosion_size`, `explosion_color`: Damage profile and visuals.

If you prefer to define torpedoes from one compact string, use `torpedo_type_string()`:

```py
~~ torpedo_type_string(
	"Pulse",
	"gui_text:Pulse;damage:18;warhead:standard;behavior:homing;"
) ~~
```

## Give the torpedo to a ship

After defining the torpedo type, make it available to ships with `torpedo_make_available()`.

```py
# Enable Tag torpedoes for this player ship with a max count of 5.
torpedo_make_available(SPAWNED_ID, "Tag", 5)
```

You can query what is available and how many remain:

```py
types = torpedo_get_available_types_for_ship(SPAWNED_ID)
count, max_count = torpedo_get_count_for_ship(SPAWNED_ID, "Tag")
```

You can remove torpdoes from a ship's inventory as well. For example, if you want to replace the default Homing torpedo with an upgraded variant:

```py
torpedo_make_unavailable(SPAWNED_ID, "Homing")
torpedo_make_available(SPAWNED_ID, "Homing_Mk2")
```

## Typical spawn-time pattern

This pattern is used by many missions so player ships always receive your custom torpedoes when they spawn.

```py
//spawn if has_role(SPAWNED_ID, "__player__") and not has_role(SPAWNED_ID, "cockpit")
	await delay_sim(1)
	torpedo_make_available(SPAWNED_ID, "Tag", 5)
```

## Prefab-driven setup

For larger projects, keep torpedo definitions in prefabs and call a shared label that applies defaults.

Example structure:

````py
=== prefab_tag_torpedo
metadata: ```
key: Tag
gui_name: Tag
damage: 0
explosion_size: 1
default_max_count: 5
player_ship_roles: tsn
```
	jump prefab_torpedo_type

//shared/signal/game_started
    # Required to actually generate the torpedo type!
    prefab_spawn(prefab_tag_torpedo)
````

This allows one place to control:

- Definition values (speed, warhead, behavior, visuals)
- Which ship roles receive the torpedo
- Default max counts
- Station production metadata

## Add production capability to stations

Station production needs three pieces wired together:

1. Build-time metadata on each torpedo prefab.
2. A station spawn route that assigns per-torp production speeds and available keys.
3. A comms/build flow that queues production tasks.

### Add build times to torpedo prefabs

Include a `build_times` dictionary in each torpedo prefab metadata block.

````py
=== prefab_tag_torpedo
metadata: ```
key: Tag
gui_name: Tag
damage: 0
default_max_count: 5
player_ship_roles: tsn
build_times:
	command: 1
	civil: 3
	industry: 1
	science: 2
	default: 4
```
	jump prefab_torpedo_type
````

These values are the number of minutes required at each station type. The keys in the build_times dictionary are searched for as substrings in the station's shipData.yaml `key`s. 

When a station spawns, the default legendary missions functionality adds the torpedo production to each applicable station.

### Common production issues

- Missing `build_times` in torpedo prefab metadata.
- Not setting `torpedo_production_keys` for stations.
- Station art id does not match any `build_times` key, so no per-torp speed is assigned.
- Comms build menu exists but does not call `build_munition_queue_task()`.

## Add custom behavior on hit

You can detect impact events and branch by torpedo type using `EVENT.sub_tag`.

```py
//damage/object if EVENT.sub_tag == "Tag"
	add_role(DAMAGE_TARGET_ID, "tagged")
	print("Ship Tagged!")
```

This lets you build torpedoes that apply mission-specific effects (marking targets, triggering scripted reactions, disabling systems, etc.) while still using the normal torpedo flight and hit pipeline.

## Live tuning during development

You can tweak values without redefining everything:

```py
torp_update_value("Tag", "damage", 4)
new_damage = torp_get_attribute_value("Tag", "damage")
```

This is useful for balancing during playtests.

## Common mistakes

- Defining a torpedo but never calling `torpedo_make_available()` for a ship.
- Defining a torpedo using a prefab but never calling `prefab_spawn()` for the type.
- Typos in `key` values (for example `tag` vs `Tag`). Ship count fields are key-sensitive.
- Expecting blast behavior without `warhead:blast`.
- Forgetting spawn-time assignment, so late-joining or respawned ships do not receive your custom torpedo.

