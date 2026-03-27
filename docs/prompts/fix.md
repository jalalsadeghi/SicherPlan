You are fixing a specific bug in the /admin/planning map picker dialog.

Current observed bug
- When the user clicks "Pick on map", the dialog still opens at 0,0 / ocean.
- The dialog text says something like:
  "Start point: existing record coordinates"
  and shows:
  Latitude 0.000000
  Longitude 0.000000
- This means the bug is NOT only a Leaflet centering issue.
- The real problem is that empty form values are being coerced into numeric zero before the initial map-center resolution runs.

Your goal
Fix the initialization pipeline so blank/unset coordinates are NOT treated as existing coordinates.

Critical diagnosis to verify in code
Inspect the real implementation and find where latitude/longitude are normalized before the map dialog opens.
Look specifically for patterns such as:
- Number(value)
- +value
- value || 0
- value ?? 0
- parseFloat(value) with zero fallback
- helper functions returning 0 for invalid input
- ref(0), shallowRef(0), reactive({ lat: 0, lng: 0 })
- computed/derived values that convert empty strings to 0
- "hasCoordinates" or "existing record coordinates" checks that run after coercion

This bug is likely caused by one of these flows:
1) the form stores lat/lng as empty strings, but Number('') becomes 0
2) a parse helper returns 0 instead of null for empty/invalid values
3) the dialog state initializes with 0/0 before the resolver decides which source should be used
4) the source-priority logic incorrectly treats 0/0 as a valid existing coordinate set

Required behavior
Implement the initial map center resolution with this exact priority:

1. Use current form latitude/longitude only if BOTH values are truly present and valid.
   - "truly present" means they came from non-empty existing form values
   - empty string, null, undefined, NaN must NOT become 0
2. Otherwise use the selected customer's saved exact coordinates, if available.
3. Otherwise geocode the selected customer's saved address/city and center there.
4. Otherwise fall back to:
   latitude: 51.662973
   longitude: 8.174013

Important rule
- Blank values must stay "unset", not 0.
- Do not use numeric zero as the default for missing coordinates.
- Preserve the distinction between:
  - no coordinate
  - valid coordinate 0
- However, for this page's initial-center logic, only treat coordinates as "existing record coordinates" when they were explicitly present in the form data source, not manufactured from empty state.

Implement a robust parser
Create or refactor a small helper, e.g. parseOptionalCoordinate(value), with this behavior:

- input: '', '   ', null, undefined -> return null
- input: NaN / invalid number string -> return null
- input: number or numeric string -> return parsed number
- must not default missing values to 0

Then create a helper like resolveInitialMapCenter(...) that returns:
- lat
- lng
- source: 'existing-record' | 'customer-coordinates' | 'customer-geocode' | 'fallback'

Validation rules
- Only use existing form coordinates if BOTH lat and lng are non-null valid numbers.
- If only one side exists, treat the pair as incomplete and move to the next source.
- If geocoding fails, fall back cleanly to 51.662973 / 8.174013.
- Never open the map at 0,0 unless the user truly and explicitly stored 0,0 as both coordinates.
- The marker, the map center, and the visible coordinate preview in the dialog must all initialize from the SAME resolved source.

UI text behavior
- The source label in the dialog must be truthful.
- For example:
  - "Start point: existing record coordinates"
  - "Start point: customer coordinates"
  - "Start point: customer address"
  - "Start point: default Germany fallback"
- In the current bug, it incorrectly claims "existing record coordinates" while using coerced 0/0. Fix that.

Leaflet/map behavior
- Ensure center order is [latitude, longitude], not [longitude, latitude].
- After the dialog opens, make sure the map uses the resolved center for:
  - map.setView(...)
  - marker position
  - coordinate preview state
- If needed, call invalidateSize after the modal becomes visible, but do not confuse this with the main bug.

What to inspect in code
Find the actual files/components/functions responsible for:
- the planning detail form latitude/longitude state
- the "Pick on map" button click handler
- map dialog props/state initialization
- any computed current coordinates
- any customer address / customer coordinate resolution
- any geocoding helper
- any source-label text such as "existing record coordinates"

Search for keywords like:
- Pick on map
- existing record coordinates
- latitude
- longitude
- map dialog
- center
- marker
- geocode
- customer location
- Number(
- || 0
- ?? 0

Constraints
- Do not do a broad UI refactor.
- Fix the bug at the state-resolution level.
- Keep current UX and modal structure intact unless a tiny cleanup is needed.
- Preserve tenant scoping.
- Do not hardcode customer-specific data except the fallback coordinates:
  51.662973, 8.174013

Definition of done
- For a new record with empty lat/lng, the map opens centered on 51.662973 / 8.174013 unless customer location/address provides a better center.
- The dialog no longer shows 0.000000 / 0.000000 for empty records.
- The dialog no longer claims "existing record coordinates" for empty records.
- Existing valid form coordinates still win when they are actually present.
- Selected customer coordinates/address correctly override the fallback when available.
- Marker, preview text, and map center are always in sync.
- No 0/0 ocean fallback remains.

Before coding
Briefly state:
1) which files own the current initialization flow
2) where the false 0/0 values are being introduced
3) which helper you will refactor or add

After coding
Report:
1) root cause of the bug
2) exact code path that converted empty values to 0
3) changed files
4) which source was used for initial centering in your final implementation
5) whether you added/updated tests for the resolver