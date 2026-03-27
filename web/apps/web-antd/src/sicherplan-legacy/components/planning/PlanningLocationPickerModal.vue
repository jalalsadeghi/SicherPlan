<template>
  <Modal
    :open="open"
    :title="title"
    :ok-text="confirmText"
    :cancel-text="cancelText"
    :confirm-loading="loadingMap"
    width="880px"
    @update:open="handleOpenChange"
    @ok="confirmSelection"
    @cancel="cancelSelection"
  >
    <div class="planning-location-modal">
      <p class="field-help">{{ helperText }}</p>
      <p class="field-help planning-location-modal__start">
        {{ startPointLabel }}
      </p>

      <div class="planning-location-modal__coords">
        <label class="field-stack">
          <span>{{ latitudeLabel }}</span>
          <input :value="draftLatitude" readonly />
        </label>
        <label class="field-stack">
          <span>{{ longitudeLabel }}</span>
          <input :value="draftLongitude" readonly />
        </label>
      </div>

      <div v-if="mapError" class="planning-location-modal__error">
        {{ mapError }}
      </div>

      <div ref="mapHost" class="planning-location-modal__map" />
    </div>
  </Modal>
</template>

<script setup>
import { Modal } from "ant-design-vue";
import { nextTick, ref, watch } from "vue";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  latitude: {
    type: [Number, String],
    default: "",
  },
  longitude: {
    type: [Number, String],
    default: "",
  },
  title: {
    type: String,
    required: true,
  },
  confirmText: {
    type: String,
    required: true,
  },
  cancelText: {
    type: String,
    required: true,
  },
  helperText: {
    type: String,
    required: true,
  },
  latitudeLabel: {
    type: String,
    required: true,
  },
  longitudeLabel: {
    type: String,
    required: true,
  },
  loadErrorText: {
    type: String,
    required: true,
  },
  initialCenter: {
    type: Object,
    required: true,
  },
  startPointLabel: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["confirm", "update:open"]);

const mapHost = ref(null);
const loadingMap = ref(false);
const mapError = ref("");
const draftLatitude = ref("");
const draftLongitude = ref("");

let leafletInstancePromise = null;
let mapInstance = null;
let markerInstance = null;

function normalizeCoordinate(value, fallback) {
  const numberValue = Number(value);
  if (Number.isFinite(numberValue)) {
    return Number(numberValue.toFixed(6));
  }
  return fallback;
}

function formatCoordinate(value) {
  return Number.isFinite(value) ? value.toFixed(6) : "";
}

function buildInitialPosition() {
  return {
    lat: normalizeCoordinate(props.initialCenter?.lat, 51.662973),
    lng: normalizeCoordinate(props.initialCenter?.lng, 8.174013),
  };
}

function updateDraft(lat, lng) {
  draftLatitude.value = formatCoordinate(lat);
  draftLongitude.value = formatCoordinate(lng);
}

function ensureLeafletAssets() {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("window unavailable"));
  }

  if (window.L) {
    return Promise.resolve(window.L);
  }

  if (leafletInstancePromise) {
    return leafletInstancePromise;
  }

  leafletInstancePromise = new Promise((resolve, reject) => {
    const stylesheetId = "planning-leaflet-css";
    if (!document.getElementById(stylesheetId)) {
      const link = document.createElement("link");
      link.id = stylesheetId;
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
    }

    const existingScript = document.getElementById("planning-leaflet-js");
    if (existingScript) {
      existingScript.addEventListener("load", () => resolve(window.L), { once: true });
      existingScript.addEventListener("error", () => reject(new Error("leaflet load failed")), {
        once: true,
      });
      return;
    }

    const script = document.createElement("script");
    script.id = "planning-leaflet-js";
    script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    script.async = true;
    script.onload = () => resolve(window.L);
    script.onerror = () => reject(new Error("leaflet load failed"));
    document.body.appendChild(script);
  });

  return leafletInstancePromise;
}

async function openMap() {
  if (!props.open) {
    return;
  }

  loadingMap.value = true;
  mapError.value = "";
  updateDraft(buildInitialPosition().lat, buildInitialPosition().lng);

  try {
    const L = await ensureLeafletAssets();
    await nextTick();

    if (!mapHost.value) {
      return;
    }

    const { lat, lng } = buildInitialPosition();

    if (!mapInstance) {
      mapInstance = L.map(mapHost.value, {
        center: [lat, lng],
        zoom: props.initialCenter?.zoom ?? 11,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(mapInstance);

      markerInstance = L.marker([lat, lng], { draggable: true }).addTo(mapInstance);

      mapInstance.on("click", (event) => {
        markerInstance.setLatLng(event.latlng);
        updateDraft(event.latlng.lat, event.latlng.lng);
      });

      markerInstance.on("dragend", () => {
        const position = markerInstance.getLatLng();
        updateDraft(position.lat, position.lng);
      });
    } else {
      mapInstance.setView([lat, lng], props.initialCenter?.zoom ?? 11);
      markerInstance.setLatLng([lat, lng]);
      mapInstance.invalidateSize();
    }

    updateDraft(lat, lng);
  } catch {
    mapError.value = props.loadErrorText;
  } finally {
    loadingMap.value = false;
  }
}

function confirmSelection() {
  emit("confirm", {
    latitude: draftLatitude.value,
    longitude: draftLongitude.value,
  });
  emit("update:open", false);
}

function cancelSelection() {
  emit("update:open", false);
}

function handleOpenChange(value) {
  emit("update:open", value);
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      await openMap();
    }
  },
  { immediate: true },
);
</script>

<style scoped>
.planning-location-modal {
  display: grid;
  gap: 1rem;
}

.planning-location-modal__start {
  margin-top: -0.35rem;
}

.planning-location-modal__coords {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.planning-location-modal__map {
  min-height: 420px;
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid var(--sp-color-border-soft);
}

.planning-location-modal__error {
  padding: 0.8rem 0.95rem;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, #dc2626 35%, var(--sp-color-border-soft));
  background: color-mix(in srgb, #fee2e2 78%, white 22%);
  color: #991b1b;
}

@media (max-width: 960px) {
  .planning-location-modal__coords {
    grid-template-columns: 1fr;
  }
}
</style>
