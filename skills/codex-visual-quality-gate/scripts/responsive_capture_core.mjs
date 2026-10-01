export const DEFAULT_VIEWPORTS = Object.freeze([
  { id: "desktop-laptop", width: 1280, height: 800, deviceScaleFactor: 1, class: "desktop", orientation: "landscape" },
  { id: "desktop-standard", width: 1440, height: 900, deviceScaleFactor: 1, class: "desktop", orientation: "landscape" },
  { id: "desktop-wide", width: 1920, height: 1080, deviceScaleFactor: 1, class: "desktop", orientation: "landscape" },
  { id: "tablet-portrait", width: 768, height: 1024, deviceScaleFactor: 1, class: "tablet", orientation: "portrait", mobile: true, touch: true },
  { id: "tablet-landscape", width: 1024, height: 768, deviceScaleFactor: 1, class: "tablet", orientation: "landscape", mobile: true, touch: true },
  { id: "mobile-portrait", width: 390, height: 844, deviceScaleFactor: 1, class: "mobile", orientation: "portrait", mobile: true, touch: true },
  { id: "mobile-landscape", width: 844, height: 390, deviceScaleFactor: 1, class: "mobile", orientation: "landscape", mobile: true, touch: true },
]);

export const RESPONSIVE_RANGE = Object.freeze({ minWidth: 320, maxWidth: 2560, step: 64, scanHeight: 900 });

export function expectedResponsiveWidths(breakpoints, range = RESPONSIVE_RANGE) {
  if (!Array.isArray(breakpoints)) throw new TypeError("breakpoints must be an array");
  if (!Number.isInteger(range.minWidth) || !Number.isInteger(range.maxWidth) || !Number.isInteger(range.step)
    || range.minWidth < 1 || range.maxWidth < range.minWidth || range.step < 1) {
    throw new RangeError("invalid responsive width range");
  }
  const widths = new Set();
  for (let width = range.minWidth; width <= range.maxWidth; width += range.step) widths.add(width);
  widths.add(range.maxWidth);
  for (const breakpoint of breakpoints) {
    if (!Number.isInteger(breakpoint) || breakpoint <= 0) throw new RangeError(`invalid breakpoint: ${breakpoint}`);
    for (const width of [breakpoint - 1, breakpoint, breakpoint + 1]) {
      if (width >= range.minWidth && width <= range.maxWidth) widths.add(width);
    }
  }
  return [...widths].sort((a, b) => a - b);
}

function validateActions(actions, stateId) {
  if (actions === undefined) return [];
  if (!Array.isArray(actions)) throw new TypeError(`state ${stateId} actions must be an array`);
  for (const action of actions) {
    if (!action || typeof action !== "object" || !["click", "fill", "press", "check", "uncheck", "select", "waitFor"].includes(action.type)) {
      throw new TypeError(`state ${stateId} contains an unsupported action`);
    }
    if (typeof action.selector !== "string" || !action.selector.trim()) {
      throw new TypeError(`state ${stateId} action needs a selector`);
    }
  }
  return actions;
}

export function buildCapturePlan(input) {
  if (!input || typeof input !== "object") throw new TypeError("capture manifest must be an object");
  let baseUrl;
  try {
    baseUrl = new URL(input.baseUrl);
  } catch {
    throw new TypeError("baseUrl must be an absolute HTTP(S) URL");
  }
  if (!new Set(["http:", "https:"]).has(baseUrl.protocol)) throw new TypeError("baseUrl must use HTTP(S)");
  if (!Array.isArray(input.routes) || input.routes.length === 0) throw new TypeError("manifest needs at least one route");
  if (!Array.isArray(input.states) || input.states.length === 0) throw new TypeError("manifest needs states");

  const routeIds = new Set();
  for (const route of input.routes) {
    if (!route || typeof route.id !== "string" || !route.id.trim() || typeof route.path !== "string" || !route.path.startsWith("/")) {
      throw new TypeError("routes need unique IDs and absolute paths starting with /");
    }
    if (routeIds.has(route.id)) throw new TypeError(`duplicate route ID: ${route.id}`);
    routeIds.add(route.id);
  }
  const breakpoints = input.breakpoints ?? [];
  if (!Array.isArray(breakpoints)) throw new TypeError("breakpoints must be an array of CSS pixel widths");
  if (new Set(breakpoints).size !== breakpoints.length) throw new TypeError("breakpoints must be unique");
  const responsiveWidths = expectedResponsiveWidths(breakpoints);
  const viewportById = new Map(DEFAULT_VIEWPORTS.map((viewport) => [viewport.id, viewport]));
  const stateIds = new Set();
  const statesByRoute = new Map();
  for (const state of input.states) {
    if (!state || typeof state.id !== "string" || !state.id.trim() || !routeIds.has(state.routeId)) {
      throw new TypeError("states need a unique ID and a known routeId");
    }
    if (stateIds.has(`${state.routeId}|${state.id}`)) throw new TypeError(`duplicate state ${state.id} for route ${state.routeId}`);
    stateIds.add(`${state.routeId}|${state.id}`);
    const viewports = state.id === "default" ? DEFAULT_VIEWPORTS.map((viewport) => viewport.id) : state.viewportIds;
    if (!Array.isArray(viewports) || viewports.length === 0) throw new TypeError(`state ${state.id} needs viewportIds`);
    for (const viewportId of viewports) {
      if (!viewportById.has(viewportId)) throw new TypeError(`state ${state.id} names unknown viewport ${viewportId}`);
    }
    validateActions(state.actions, state.id);
    statesByRoute.set(state.routeId, [...(statesByRoute.get(state.routeId) ?? []), { ...state, viewportIds: viewports }]);
  }
  for (const routeId of routeIds) {
    if (!(statesByRoute.get(routeId) ?? []).some((state) => state.id === "default")) {
      throw new TypeError(`route ${routeId} has no default state`);
    }
  }
  const flows = input.flows ?? [];
  if (!Array.isArray(flows)) throw new TypeError("flows must be an array of UX-contract flow records");
  const flowIds = new Set();
  for (const flow of flows) {
    if (!flow || typeof flow.id !== "string" || !flow.id.trim() || flowIds.has(flow.id)) {
      throw new TypeError("flows need unique non-empty IDs");
    }
    if (!Array.isArray(flow.routeIds) || flow.routeIds.length === 0 || flow.routeIds.some((routeId) => !routeIds.has(routeId))) {
      throw new TypeError(`flow ${flow.id} needs known routeIds`);
    }
    flowIds.add(flow.id);
  }

  const targets = [];
  const addTarget = (route, state, viewport) => {
    const key = `${route.id}|${state.id}|${viewport.id}`;
    if (targets.some((target) => target.key === key)) return;
    targets.push({
      key,
      routeId: route.id,
      path: route.path,
      stateId: state.id,
      viewportId: viewport.id,
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: Boolean(viewport.mobile),
      touch: Boolean(viewport.touch),
      actions: validateActions(state.actions, state.id),
    });
  };

  for (const route of input.routes) {
    const states = statesByRoute.get(route.id) ?? [];
    const defaultState = states.find((state) => state.id === "default");
    for (const viewport of DEFAULT_VIEWPORTS) addTarget(route, defaultState, viewport);
    for (const breakpoint of [...breakpoints].sort((a, b) => a - b)) {
      for (const width of [breakpoint - 1, breakpoint, breakpoint + 1]) {
        if (width < RESPONSIVE_RANGE.minWidth || width > RESPONSIVE_RANGE.maxWidth) continue;
        addTarget(route, defaultState, {
          id: `width-${width}`,
          width,
          height: RESPONSIVE_RANGE.scanHeight,
          deviceScaleFactor: 1,
        });
      }
    }
    for (const state of states.filter((entry) => entry.id !== "default")) {
      for (const viewportId of state.viewportIds) addTarget(route, state, viewportById.get(viewportId));
    }
  }
  return {
    schemaVersion: 1,
    baseUrl: baseUrl.toString(),
    breakpoints: [...breakpoints].sort((a, b) => a - b),
    responsiveWidths,
    viewports: DEFAULT_VIEWPORTS.map((viewport) => ({ ...viewport })),
    routes: input.routes.map((route) => ({ id: route.id, path: route.path })),
    states: input.states.map((state) => ({ ...state, actions: validateActions(state.actions, state.id) })),
    flows: flows.map((flow) => ({ ...flow, routeIds: [...flow.routeIds] })),
    targets,
  };
}
