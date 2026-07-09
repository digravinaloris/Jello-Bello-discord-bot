# Jello Bello

A full-featured Discord moderation & utility bot — auto-moderation, anti-raid protection, tempbans, reaction roles, a role-application system, music playback, and a companion Android app for managing your server on the go.

Built with Python (discord.py) + Flask, backed by MongoDB Atlas, hosted on Render.

---

## Features

- **Moderation** — ban, kick, mute, warn, tempban, clear messages, full sanction history
- **Auto-moderation** — anti-spam, anti-invite-link, anti-caps, all configurable
- **Anti-raid** — automatically locks the server if too many members join in a short window, with an instant alert to the server owner
- **Channel locking** — lock/unlock text or voice channels on demand
- **Reaction roles** — self-assignable roles via emoji reactions
- **Role applications** (`/apply`) — members apply through a form, the server owner reviews and accepts/refuses with one click
- **Per-command permissions** — the server owner decides exactly which role can use which command
- **Music** — play, queue, and search YouTube audio directly in voice channels
- **Companion Android app** — moderate your server, view stats, and manage config from your phone

Jello Bello works across multiple servers — each server has its own independent configuration, sanctions, warnings, and permissions.

---

## Commands

### Moderation
| Command | Description |
|---|---|
| `/ban` `/unban` | Ban / unban a member |
| `/kick` | Kick a member |
| `/mute` `/unmute` | Timeout a member |
| `/tempban <duration>` | Temporary ban (`30m`, `2h`, `1d`, `1w`), lifted automatically |
| `/warn` `/unwarn` `/warnings` `/warnlist` | Manage warnings |
| `/banlist` `/mutelist` | List active bans / mutes |
| `/history` | Full sanction history for a member |
| `/clear` | Bulk-delete messages, with user/role/bot filters |

### Channels & Roles
| Command | Description |
|---|---|
| `/lock` `/unlock` | Lock / unlock a text channel |
| `/vlock` `/vunlock` | Lock / unlock a voice channel |
| `/lockedchannels` | List currently locked channels |
| `/roleadd` `/roleremove` | Add / remove a role from a member |
| `/reactionrole` | Create a reaction-role message |

### Applications & Utilities
| Command | Description |
|---|---|
| `/apply <role>` | Apply for a role via a short form; the server owner accepts or refuses |
| `/userinfo` `/serverinfo` | Member / server information |
| `/broadcast` | Send an announcement as the bot |

### Music
| Command | Description |
|---|---|
| `/play` `/search` `/pause` `/resume` `/skip` `/stop` `/queue` `/volume` | Standard music controls, with YouTube search & autocomplete |

### Server Configuration (`/config`)
| Command | Access | Description |
|---|---|---|
| `/config logs <channel>` | Administrator | Set the logs channel |
| `/config autorole <role>` | Administrator | Role given automatically to new members |
| `/config apikey` | Administrator | Generate an API key for the mobile app |
| `/config view` | Administrator | View the current configuration |
| `/config allow <command> <role>` | **Server owner only** | Let a specific role use a specific command |
| `/config disallow <command> <role>` | **Server owner only** | Remove that permission |
| `/botlock` | **Server owner only** | Lock the bot on this server |
| `/botunlock` | **Server owner only** | Unlock the bot on this server |

By default, commands fall back to their standard Discord permission (e.g. Ban Members for `/ban`). The server owner can override this per-command with `/config allow`/`disallow` to grant access to specific roles instead.

---

## How permissions work

1. **Administrators** can always use every command.
2. If the server owner has configured specific roles for a command (`/config allow`), only those roles (or an admin) can use it.
3. Otherwise, the command falls back to its default Discord permission.
4. While the bot is locked (`/botlock`, or automatically after a detected raid), only Administrators can use protected commands until `/botunlock`.

---

## Tech Stack

- **Python** + [discord.py](https://discordpy.readthedocs.io/)
- **Flask** — REST API powering the Android companion app
- **MongoDB Atlas** — warnings, sanctions, configuration, locked channels, reaction roles
- **yt-dlp** + **imageio-ffmpeg** — music playback
- **Render** — hosting

---

## Companion Android App

Built with Kotlin + Jetpack Compose, connecting to the bot's REST API to let server admins moderate, check stats, and manage configuration from their phone. Each server gets its own API key via `/config apikey`.

---

## Legal

- [Terms of Service](https://gist.github.com/digravinaloris/48698cf1c84609c688f7ba86c3a2b958)
- [Privacy Policy](https://gist.github.com/digravinaloris/17bbe8e1a5c8db6a299331a430a45a42)
