/** Bound host calls even when a bridge promise never settles. Late results are ignored. */
export function withDeadline(work, timeoutMs, message) {
  let timer;
  return Promise.race([
    Promise.resolve().then(work),
    new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error(message)), timeoutMs);
    }),
  ]).finally(() => clearTimeout(timer));
}
