// Tiny global toast queue (reactive). Toasts are announced via an aria-live
// region rendered by the ToastHost component.

const { reactive } = window.Vue;

export const toastState = reactive({ items: [] });
let counter = 0;

export function pushToast(message, opts = {}) {
  counter += 1;
  const item = {
    id: counter,
    message,
    tone: opts.tone || 'info',
    actionLabel: opts.actionLabel || null,
    action: opts.action || null,
    sticky: opts.sticky === true,
  };
  toastState.items.push(item);
  if (!item.sticky) {
    setTimeout(() => dismissToast(item.id), opts.duration || 4000);
  }
  return item.id;
}

export function dismissToast(id) {
  const index = toastState.items.findIndex((t) => t.id === id);
  if (index >= 0) toastState.items.splice(index, 1);
}
