/**
 * useLogging composable
 * Provides a consistent logging system across all Vue components
 *
 * Usage:
 *   const { debugLog, infoLog, warnLog, errorLog, DEBUG } = useLogging("ComponentName");
 *
 * - debugLog: Only logs if VITE_DEBUG=true in .env
 * - infoLog: Always logs
 * - warnLog: Always logs with ⚠️ prefix
 * - errorLog: Always logs with ❌ prefix
 */

export function useLogging(componentName) {
  const DEBUG = import.meta.env.VITE_DEBUG === "true";

  const debugLog = (msg, data) => {
    if (DEBUG) console.log(`[${componentName}] ${msg}`, data || "");
  };

  const infoLog = (msg, data) => {
    console.log(`[${componentName}] ${msg}`, data || "");
  };

  const warnLog = (msg, data) => {
    console.warn(`[${componentName}] ⚠️ ${msg}`, data || "");
  };

  const errorLog = (msg, data) => {
    console.error(`[${componentName}] ❌ ${msg}`, data || "");
  };

  return { debugLog, infoLog, warnLog, errorLog, DEBUG };
}
