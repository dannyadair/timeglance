// Tiny DOM helpers used throughout the UI.

export const $ = (s, r = document) => r.querySelector(s);

export const el = (tag, attrs = {}, html) => {
  const n = Object.assign(document.createElement(tag), attrs);
  if (html != null) n.innerHTML = html;
  return n;
};
