import Keycloak, { type KeycloakInstance } from "keycloak-js";

let client: KeycloakInstance | null = null;
let initialization: Promise<boolean> | null = null;

function getClient(): KeycloakInstance {
  if (client) return client;

  const url = process.env.NEXT_PUBLIC_KEYCLOAK_URL;
  const realm = process.env.NEXT_PUBLIC_KEYCLOAK_REALM;
  const clientId = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID;
  if (!url || !realm || !clientId) {
    throw new Error(
      "Set NEXT_PUBLIC_KEYCLOAK_URL, NEXT_PUBLIC_KEYCLOAK_REALM, and NEXT_PUBLIC_KEYCLOAK_CLIENT_ID.",
    );
  }

  client = new Keycloak({ url, realm, clientId });
  return client;
}

export function initializeKeycloak(): Promise<boolean> {
  if (!initialization) {
    initialization = getClient().init({
      onLoad: "check-sso",
      pkceMethod: "S256",
      checkLoginIframe: false,
    });
  }
  return initialization;
}

export async function getCurrentAccessToken(): Promise<string | null> {
  const keycloak = getClient();
  if (!keycloak.authenticated) return null;

  await keycloak.updateToken(30);
  return keycloak.token ?? null;
}

export async function startKeycloakLogin(): Promise<void> {
  await getClient().login();
}

export async function endKeycloakSession(): Promise<void> {
  const keycloak = getClient();
  if (keycloak.authenticated) {
    await keycloak.logout({ redirectUri: window.location.origin });
  }
}

export function clearKeycloakToken(): void {
  client?.clearToken();
}
