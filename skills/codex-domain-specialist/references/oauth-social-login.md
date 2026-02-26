# OAuth and Social Login Patterns

## Scope
Use when implementing social login (Google, GitHub, Facebook) or OAuth2 integrations.

## Authorization Code Flow
1. User clicks social login.
2. Redirect user to provider authorization endpoint.
3. Provider returns authorization code.
4. Backend exchanges code for tokens.
5. Backend fetches profile and links or creates local user.
6. Backend issues first-party tokens/session.

## Passport.js Google Strategy

```javascript
import passport from "passport";
import { Strategy as GoogleStrategy } from "passport-google-oauth20";

passport.use(
  new GoogleStrategy(
    {
      clientID: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      callbackURL: "/api/auth/google/callback",
      scope: ["profile", "email"],
    },
    async (accessToken, refreshToken, profile, done) => {
      try {
        let user = await User.findOne({ "oauth.googleId": profile.id });
        if (!user) {
          user = await User.create({
            firstName: profile.name?.givenName || profile.displayName,
            lastName: profile.name?.familyName || "",
            email: profile.emails?.[0]?.value,
            avatar: profile.photos?.[0]?.value,
            oauth: { googleId: profile.id, provider: "google" },
            isEmailVerified: true,
          });
        }
        done(null, user);
      } catch (err) {
        done(err);
      }
    }
  )
);

router.get("/auth/google", passport.authenticate("google", { scope: ["profile", "email"] }));
```

## GitHub Strategy

```javascript
import { Strategy as GitHubStrategy } from "passport-github2";

passport.use(
  new GitHubStrategy(
    {
      clientID: process.env.GITHUB_CLIENT_ID,
      clientSecret: process.env.GITHUB_CLIENT_SECRET,
      callbackURL: "/api/auth/github/callback",
      scope: ["user:email"],
    },
    async (accessToken, refreshToken, profile, done) => {
      try {
        let user = await User.findOne({ "oauth.githubId": profile.id });
        if (!user) {
          const email = profile.emails?.[0]?.value;
          user = await User.create({
            firstName: profile.displayName?.split(" ")[0] || profile.username,
            lastName: profile.displayName?.split(" ").slice(1).join(" ") || "",
            email,
            avatar: profile.photos?.[0]?.value,
            oauth: { githubId: profile.id, provider: "github" },
          });
        }
        done(null, user);
      } catch (err) {
        done(err);
      }
    }
  )
);
```

## Account Linking Pattern

```javascript
let user = await User.findOne({ email });
if (user && !user.oauth?.googleId) {
  user.oauth = { ...user.oauth, googleId: profile.id };
  await user.save();
}
```

## Security Rules
- Keep OAuth client secrets in environment variables only.
- Use Authorization Code flow (or PKCE where applicable), not implicit flow.
- Validate `state` to prevent CSRF.
- Verify provider email before trusting account identity.
- Support social account disconnect flows.
