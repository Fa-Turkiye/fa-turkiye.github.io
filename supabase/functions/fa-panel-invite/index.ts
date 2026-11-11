const panelUrl = "https://fa-turkiye.github.io/panel/";
const panelOrigin = new URL(panelUrl).origin;

const headers = {
  "Access-Control-Allow-Origin": panelOrigin,
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Cache-Control": "no-store",
};

function reply(status: number, body: Record<string, unknown>) {
  return Response.json(body, { status, headers });
}

function projectKey(dictionaryName: string, legacyName: string): string | undefined {
  const keys = JSON.parse(Deno.env.get(dictionaryName) ?? "{}");
  return keys.default ?? Deno.env.get(legacyName);
}

Deno.serve(async (request) => {
  const origin = request.headers.get("Origin");
  if (origin && origin !== panelOrigin) return reply(403, { error: "origin_not_allowed" });
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers });
  if (request.method !== "POST") return reply(405, { error: "method_not_allowed" });

  const authorization = request.headers.get("Authorization") ?? "";
  if (!/^Bearer \S+$/.test(authorization)) return reply(401, { error: "authentication_required" });

  const body = await request.json().catch(() => null);
  const email = typeof body?.email === "string" ? body.email.trim().toLowerCase() : "";
  const role = body?.role;
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ||
      (role !== "author" && role !== "editor")) {
    return reply(400, { error: "invalid_invitation" });
  }

  try {
    const projectUrl = Deno.env.get("SUPABASE_URL");
    const publicKey = projectKey("SUPABASE_PUBLISHABLE_KEYS", "SUPABASE_ANON_KEY");
    const secretKey = projectKey("SUPABASE_SECRET_KEYS", "SUPABASE_SERVICE_ROLE_KEY");
    if (!projectUrl || !publicKey || !secretKey) return reply(503, { error: "project_not_configured" });

    const assignRole = () => fetch(new URL("/rest/v1/rpc/fa_panel_set_member_role", projectUrl), {
      method: "POST",
      headers: { apikey: publicKey, Authorization: authorization, "Content-Type": "application/json" },
      body: JSON.stringify({ target_email: email, assigned_role: role }),
    });

    // The database verifies the caller's current admin membership before returning an account ID or null.
    let assignment = await assignRole();
    if (assignment.status === 401 || assignment.status === 403) {
      return reply(assignment.status, { error: "panel_admin_required" });
    }
    if (!assignment.ok) return reply(502, { error: "role_check_failed" });
    if (await assignment.json()) return reply(200, { invited: false });

    const inviteUrl = new URL("/auth/v1/invite", projectUrl);
    inviteUrl.searchParams.set("redirect_to", panelUrl);
    const invitation = await fetch(inviteUrl, {
      method: "POST",
      headers: { apikey: secretKey, Authorization: "Bearer " + secretKey, "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    if (!invitation.ok) {
      const error = await invitation.json().catch(() => null);
      if (error?.error_code !== "email_exists" && error?.error_code !== "user_already_exists") {
        return reply(invitation.status === 429 ? 429 : 502, { error: "email_invite_failed" });
      }
    }

    // A retry can finish assigning access to an account the Auth service already invited.
    assignment = await assignRole();
    if (!assignment.ok || !await assignment.json()) {
      return reply(502, { error: "role_assignment_incomplete" });
    }
    return reply(200, { invited: invitation.ok });
  } catch {
    return reply(503, { error: "project_unavailable" });
  }
});
