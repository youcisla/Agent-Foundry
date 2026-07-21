# 2FA Setup for npm Publishing

npm requires two-factor authentication (or a granular access token) to
publish public packages. This is the security policy since the 2024
deprecation of bypass-2fa tokens.

## Enable 2FA on your npm account

### Step 1: Open settings
https://www.npmjs.com/settings/youraccount

### Step 2: Find "Two-Factor Authentication"
Click "Enable" → choose **"Authenticator App"** (TOTP).

### Step 3: Scan QR
Scan the QR code with any TOTP app:
- Google Authenticator (mobile)
- 1Password (desktop / mobile)
- Authy (mobile)
- Bitwarden (desktop)
- Microsoft Authenticator (mobile)

### Step 4: Save recovery codes
npm will show ~10 recovery codes **once**. Save them in a password manager.
These are your only way back in if you lose your phone.

### Step 5: Confirm
Enter the 6-digit TOTP code shown in your authenticator app. Done.

## Use it during publish

```bash
bash scripts/publish.sh
# When prompted: "Enter OTP:" → type the 6-digit code from your app
```

For CI / non-interactive:
```bash
NPM_CONFIG_OTP=123456 bash scripts/publish.sh
```

## Alternative: Granular access token

If you don't want 2FA on your npm account (e.g. shared with a team), use a
granular access token:

### Step 1: Generate token
https://www.npmjs.com/settings/youraccount → "Tokens" → "Generate New Token"

- Type: **Granular Access Token**
- Name: anything (e.g. "agent-foundry-publish")
- Scope: **Publish** (or "Read and Publish")
- Expiry: 90 days (or your preference)

### Step 2: Configure npm
```bash
npm config set //registry.npmjs.org/:_authToken=npm_xxxxxxxxxxxxxxxxxx
```

This writes to `~/.npmrc`. Verify:
```bash
npm whoami    # should still show your username
```

### Step 3: Publish
```bash
bash scripts/publish.sh
# No OTP prompt — token has publish permission
```

### Step 4: Rotate
Tokens expire. When `npm publish` returns 401, generate a new token and
re-run the `npm config set` command.

## Why this is required

As of npm's 2024 security update:
- Granular access tokens are the recommended path for CI / shared accounts
- Legacy "bypass 2FA" tokens are being deprecated
- Publishing without 2FA / valid token returns `E403 Forbidden`

If you see this error:
```
npm error code E403
npm error 403 403 Forbidden - PUT https://registry.npmjs.org/agent-foundry
  - Two-factor authentication or granular access token with bypass 2fa
    enabled is required to publish packages.
```

The fix is to enable 2FA or set a granular token. See above.

## Troubleshooting

- **OTP rejected repeatedly** — your phone clock may be off. TOTP requires
  ±30 second sync. Check your device clock.
- **Lost phone** — use one of your saved recovery codes. Each is single-use.
  After recovery, immediately re-enroll a new device.
- **Token expired** — generate a new granular token (no impact on your 2FA).