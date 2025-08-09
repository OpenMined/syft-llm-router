// Terminology constants for easy customization
export const GATEKEEPER_TERM = "Gatekeeper";
export const GATEKEEPER_TERM_PLURAL = "Gatekeepers";
export const GATEKEEPER_ACTION = "Gatekeeping";

// API endpoints for delegation/gatekeeper features
export const GATEKEEPER_API = {
  OPT_IN: '/delegate/opt-in',
  STATUS: '/delegate/status',
  LIST: '/router/delegate/list',
  GRANT: '/router/delegate/grant',
  REVOKE: '/router/delegate/revoke',
  LOGS: '/router/delegate/logs',
  CONTROL: '/router/delegate/control',
  ACCESS_TOKEN: '/router/delegate/access-token'
} as const;