# aocstat

A command line tool for interacting with Advent of Code.

## Installation

The best way to install aocstat is with `pipx`.

```bash
pipx install aocstat
```

## Usage

Usage is broken up into 4 main commands:

| Command | Description                                                    |
| ------- | -------------------------------------------------------------- |
| lb      | For interacting with global and private leaderboards.          |
| purge   | Purges local cache -- including authentication token.          |
| config  | Manages setting and viewing configuration options.             |
| pz      | Manages viewing puzzle prompts, input, and submitting answers. |

Each has a comprehensive help message accessible with `-h`, or `--help`.

## Known Issues

- Automatic authentication with Google doesn't work.
- Automatic authentication is clunky and annoying.

## Planned features

- Configurable directory templating, with automatic input downloading.
- Example input extraction.
- Personal timers and stats.
