// Next.js only inlines NEXT_PUBLIC_* vars into the client bundle when the
// exact `process.env.NAME` expression is statically visible at build time —
// a helper doing `process.env[key]` with a variable key defeats that, so the
// override always silently fell back to the hardcoded default in the
// browser regardless of .env.local. Reference each var literally instead.
export const authConfig = {
  issuer: process.env.NEXT_PUBLIC_CYIDENTITY_ISSUER ?? "http://localhost:8080/realms/cybercom",
  clientId: process.env.NEXT_PUBLIC_CYIDENTITY_ADMIN_CLIENT_ID ?? "cybercom-admin-panel",
  scopes: (process.env.NEXT_PUBLIC_CYIDENTITY_SCOPES ?? "openid profile email").split(" "),
};
