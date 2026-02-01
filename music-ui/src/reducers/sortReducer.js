export const DEFAULT_SORT_STACK = [
  { field: "artist", dir: "asc", locked: false },
  { field: "album",  dir: "asc", locked: false },
  { field: "title",  dir: "asc", locked: false },
];

export function sortReducer(state, action) {
  switch (action.type) {

    case "RESET_SORT":
      return DEFAULT_SORT_STACK.map(k => ({ ...k }));

    case "TOGGLE_DIR":
      return state.map(k =>
        k.field === action.field
          ? { ...k, dir: k.dir === "asc" ? "desc" : "asc" }
          : k
      );

    case "TOGGLE_LOCK": {
      const key = state.find(k => k.field === action.field);
      if (!key) return state;

      const updated = { ...key, locked: !key.locked };

      const locked = state.filter(k => k.locked && k.field !== key.field);
      const unlocked = state.filter(k => !k.locked && k.field !== key.field);

      return updated.locked
        ? [...locked, updated, ...unlocked]
        : [...locked, updated, ...unlocked];
    }

    case "CLICK_COLUMN": {
      const key = state.find(k => k.field === action.field);
      if (!key) return state;

      if (key.locked) {
        return state.map(k =>
          k.field === action.field
            ? { ...k, dir: k.dir === "asc" ? "desc" : "asc" }
            : k
        );
      }

      const toggled = {
        ...key,
        dir: key.dir === "asc" ? "desc" : "asc",
      };

      const locked = state.filter(k => k.locked);
      const unlocked = state.filter(
        k => !k.locked && k.field !== key.field
      );

      return [...locked, toggled, ...unlocked];
    }

    default:
      return state;
  }
}
