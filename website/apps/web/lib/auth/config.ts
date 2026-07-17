function env(key: string, fallback: string): string {
  return process.env[key] ?? fallback;
}

export const authConfig = {
  issuer: env("NEXT_PUBLIC_CYIDENTITY_ISSUER", "http://localhost:8080/realms/cybercom"),
  clientId: env("NEXT_PUBLIC_CYIDENTITY_ADMIN_CLIENT_ID", "cybercom-admin-panel"),
  scopes: env("NEXT_PUBLIC_CYIDENTITY_SCOPES", "openid profile email").split(" "),
};
