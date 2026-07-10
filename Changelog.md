# Changelog

All notable changes to Jello Bello are documented here.

## [Unreleased]

### Added
- `/apply` — role application system: members apply via a form, the server owner reviews and accepts/refuses via buttons
- `/config` command group — server configuration (logs channel, autorole, API key, per-command role permissions)
- `/config allow` / `/config disallow` — let the server owner grant specific roles access to specific commands
- `/botlock` / `/botunlock` — server owner can lock/unlock the bot on their server
- Anti-raid protection — automatically locks a server if too many members join in a short window, with an alert to the server owner
- Per-server API keys (`/config apikey`) for the companion Android app, in addition to the master key
- `on_guild_join` — welcome DM to the server owner with setup instructions
- `on_guild_remove` — automatic cleanup of all stored data (config, warnings, sanctions, notes, reaction roles) when the bot is removed from a server
- `/help`, `/ping`, `/botinfo` — utility commands
- `/poll` — quick polls with up to 4 options or a simple 👍/👎
- `/slowmode` — set or disable channel slowmode
- `/nickname` — change a member's nickname
- `/groupnickname` — add or remove a prefix on the nickname of every member with a role
- `/note` / `/notes` — internal staff notes on a member, not visible to them
- `/softban` — kick a member and delete their recent messages
- `/purgeuser` — erase all stored data for a member on a server (Administrator only)
- `README.md` with full command reference, invite link, getting started guide, and legal links
- `TERMS.md` and `PRIVACY.md` published
- `.gitignore` to prevent secrets and local files from being committed

### Changed
- Warnings are now scoped per server (previously shared across all servers a user was in)
- Bot lock (`bot.locked`) is now per-server instead of a single global flag
- The bot's lock/logs/API behavior no longer relies on a single hardcoded owner account — fully multi-server
- `/apply` DMs now go to the server owner instead of the bot developer
- Auto-moderation exemptions are now role/permission-based instead of exempting one hardcoded account
- Mobile app action logs now post to each server's configured logs channel instead of a single hardcoded channel

### Removed
- `/safemode` and the old password-protected `/config` system
- Hardcoded default configuration for a single server

### Security
- Purged two exposed Discord bot tokens from the entire git history
- Regenerated the bot token
- Per-command permissions can now be restricted to specific roles, separate from Discord's default permission set
- `/config allow` / `/config disallow` and `/botlock` / `/botunlock` restricted to the server owner specifically, not just Administrator
