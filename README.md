# Awesome Claude Code

A collection of powerful tools for [Claude Code](https://claude.com/claude-code) including custom slash commands and hooks to streamline development workflows and enhance productivity.

## 📋 Available Commands

### `/code-reviewer`
Expert code review with comprehensive analysis covering:
- Security vulnerabilities and attack vectors
- Performance bottlenecks and optimization opportunities
- Logic errors and edge cases
- Code maintainability and technical debt
- Best practices and conventions

### `/fix-jira`
Automated Jira ticket resolution workflow:
1. Fetches and analyzes Jira ticket details
2. Understands the problem and locates affected code
3. Generates technical solution design
4. Implements fixes using best practices

**Usage**: `/fix-jira TICKET-123`

### `/git-commit-pusher`
Git workflow automation specialist that:
- Reviews staged and unstaged changes
- Generates conventional commit messages
- Verifies changes before committing
- Handles push operations safely

### `/golang-backend-engineer`
Expert Go backend development assistance for:
- Google Cloud Spanner queries and transactions
- Pub/Sub message handling
- Redis caching strategies
- Elasticsearch operations
- Follows systematic analysis → planning → implementation workflow

### `/pr`
GitHub Pull Request creation with:
- Automatic PR template population
- Jira ticket integration (AFD-* pattern)
- Smart upstream branch targeting

**Usage**: `/pr [target-branch]` (defaults to `master`)

### `/repo-analyze`
AI-powered repository analysis using Gemini CLI + Claude collaboration:
- Architecture and design pattern analysis
- Code quality and maintainability assessment
- Security vulnerability scanning
- Performance bottleneck identification
- Automatic documentation generation

**Analysis types**: `architecture`, `functions`, `quality`, `security`, `performance`, `documentation`, `full`

**Usage**: `/repo-analyze [analysis-type] [repo-path] [output-path]`

### `/technical-solution-architect`
Transforms PRDs and requirements into comprehensive technical solutions:
- Requirement analysis and system design
- Architecture diagrams (Mermaid)
- Interface and API specifications
- Integration planning
- Implementation roadmap

## 🔔 Hooks

This repository includes a powerful hooks system that enables **real-time Slack notifications** for Claude Code events, helping you stay informed when:
- Claude Code needs your approval for an action
- Tasks are completed and ready for review
- Important events occur during development

### Features

- 🔔 **Automatic Notifications**: Get Slack alerts when Claude Code requires human intervention
- 🎨 **Rich Messages**: Beautiful notifications using Slack Block Kit
- ⚙️ **Flexible Configuration**: Support for multiple event types with custom triggers
- 🔒 **Secure**: Sensitive information managed through environment variables
- 📬 **Dual Mode Support**: Send via Webhook (to channels) or Direct Message (to yourself)
- 📦 **Minimal Dependencies**: Webhook mode uses only Python stdlib, DM mode requires `slack-sdk`

### Quick Start

**Option 1: Direct Message Mode (Recommended)**

Send notifications directly to your Slack DMs for better privacy.

1. **Create Slack App & Get Credentials**
   - Visit https://api.slack.com/apps
   - Create app, add `chat:write` scope
   - Copy Bot Token (starts with `xoxb-`) and your Member ID

2. **Install Dependencies**
   ```bash
   pip install slack-sdk
   ```

3. **Set Environment Variables**
   ```bash
   export SLACK_CLAUDE_CODE_BOT_TOKEN="xoxb-your-token"
   export SLACK_MEMBER_ID="U01234567"
   # Add to ~/.bashrc or ~/.zshrc to make it permanent
   ```

4. **Install & Configure**
   ```bash
   cp hooks/claude_slack_notifier.py ~/bin/
   chmod +x ~/bin/claude_slack_notifier.py
   ```

   Add to `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "Notification": [{
         "matcher": "",
         "hooks": [{
           "type": "command",
           "command": "python3 ~/bin/claude_slack_notifier.py --event-type notification --mode dm"
         }]
       }],
       "Stop": [{
         "matcher": "",
         "hooks": [{
           "type": "command",
           "command": "python3 ~/bin/claude_slack_notifier.py --event-type stop --mode dm"
         }]
       }]
     }
   }
   ```

5. **Activate**
   ```
   /hooks
   ```

**Option 2: Webhook Mode**

Send notifications to a Slack channel.

1. Get Webhook URL from https://api.slack.com/apps
2. Set `export SLACK_WEBHOOK_URL="..."`
3. Use `--mode webhook` in commands (see [hooks/README.md](./hooks/README.md))

### Supported Events

| Event | Trigger | Recommended |
|-------|---------|-------------|
| `Notification` | Claude Code requests approval | ✅ |
| `Stop` | Task completion | ✅ |
| `UserPromptSubmit` | New task submitted | Optional |
| `PreToolUse` | Before tool execution | Optional |
| `PostToolUse` | After tool execution | Optional |
| `PreCompaction` | Before context compression | Optional |
| `SessionStart` | Session begins | Optional |

### Documentation

For detailed setup instructions, configuration options, and troubleshooting, see:
- [Hooks README](./hooks/README.md) - Complete documentation with both DM and Webhook setup
- [Configuration Examples](./hooks/) - Sample configuration files

## 🚀 Installation

1. Clone this repository:
```bash
git clone https://github.com/virgoC0der/claude-code-slash-commands.git
```

2. Copy the command files to your Claude Code commands directory:
```bash
cp commands/*.md ~/.claude/commands/
```

3. Restart Claude Code or reload commands.

## 📖 Usage

Simply type the slash command in Claude Code:

```
/code-reviewer
/fix-jira AFD-1234
/pr master
/repo-analyze full ./my-project
```

## 🛠️ Customization

Each command is defined in a Markdown file in the `commands/` directory. You can:
- Modify existing commands to fit your workflow
- Create new commands by adding `.md` files
- Adjust prompts and behavior to match your team's standards

## 📚 Requirements

### Commands
Some commands have external dependencies:
- `/repo-analyze`: Requires [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- `/fix-jira`: Requires Atlassian MCP integration
- `/pr`: Requires GitHub CLI (`gh`)

### Hooks
- Python 3.6+
- **DM Mode** (recommended): `slack-sdk` library + Slack Bot Token + Member ID
- **Webhook Mode**: Slack Webhook URL (no additional dependencies)

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Submit bug reports or feature requests
- Create pull requests with improvements
- Share your custom commands

## 📄 License

MIT License - feel free to use and modify these commands for your needs.

## 🔗 Links

### Claude Code Official Docs
- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [Slash Commands Guide](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Hooks Documentation](https://docs.claude.com/en/docs/claude-code/hooks)

### External APIs & SDKs
- [Slack API Documentation](https://api.slack.com/methods/chat.postMessage)
- [Slack Webhooks Documentation](https://api.slack.com/messaging/webhooks)
- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder)
- [slack-sdk Documentation](https://slack.dev/python-slack-sdk/)