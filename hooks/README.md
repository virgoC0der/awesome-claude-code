# Claude Code Slack Notification System

A lightweight tool for sending Slack notifications when Claude Code requires human intervention or when tasks are completed.

## ✨ Features

- 🔔 **Automatic Notifications**: Automatically send Slack messages when Claude Code needs approval or tasks complete
- 🎨 **Rich Messages**: Create beautiful notifications using Slack Block Kit
- ⚙️ **Flexible Configuration**: Support for multiple event types and custom triggers
- 🔒 **Secure**: Manage sensitive information through environment variables
- 📦 **Zero Dependencies**: Uses only Python standard library

## 📦 Files

| File | Description |
|------|-------------|
| `claude_slack_notifier.py` | Main notification script |
| `quick_install.sh` | Quick installation script |
| `SETUP_GUIDE.md` | Detailed installation and configuration guide |
| `hooks_minimal.json` | Minimal configuration example (recommended) |
| `hooks_example.json` | Complete configuration example |

## 🚀 Quick Start

#### Step 1: Get Slack Webhook URL

1. Visit https://api.slack.com/apps
2. Create a new app and enable Incoming Webhooks
3. Copy the generated Webhook URL

#### Step 2: Set Environment Variable

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

Add to `~/.bashrc` or `~/.zshrc` to make it permanent.

#### Step 3: Configure Claude Code

Edit `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/bin/claude_slack_notifier.py --event-type notification",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/bin/claude_slack_notifier.py --event-type stop",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

#### Step 4: Activate in Claude Code

Run in Claude Code:
```
/hooks
```
Then review and approve the configuration.

## 📖 Usage Examples

### Basic Usage

After installation, Claude Code will automatically send notifications in the following situations:

1. **When Approval is Needed** (Notification event)
   - Example: When executing dangerous commands
   - Example: When modifying important files

2. **When Tasks Complete** (Stop event)
   - At the end of any conversation
   - Review results and decide next steps

### Manual Testing

```bash
# Test sending notifications
echo '{"notification":"Test message"}' | \
  python3 ~/bin/claude_slack_notifier.py \
  --event-type notification \
  --message "This is a test message"
```

### Monitor Specific Tools

Notify only on file modifications:

```json
{
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        {
          "type": "command",
          "command": "python3 ~/bin/claude_slack_notifier.py --event-type post_tool_use"
        }
      ]
    }
  ]
}
```

## 📊 Supported Event Types

| Event | Trigger | Recommended |
|-------|---------|-------------|
| `Notification` | Claude Code requests user approval | ✅ |
| `Stop` | Task completion | ✅ |
| `UserPromptSubmit` | User submits new task | Optional |
| `PreToolUse` | Before tool execution | Optional |
| `PostToolUse` | After tool execution | Optional |
| `PreCompaction` | Before context compression | Optional |
| `SessionStart` | Session begins | Optional |

## 🎨 Message Examples

### Notification Event
```
🔔 Claude Code Needs Your Action

Time: 2025-10-11 10:30:15
Event Type: notification

Notification:
About to execute command 'rm -rf /tmp/*', confirmation needed
```

### Stop Event
```
✅ Claude Code Task Completed

Time: 2025-10-11 10:35:42
Event Type: stop

Session ID: abc123-def456
```

## 🔧 Advanced Configuration

### Use Different Channels for Different Projects

Create `.claude/settings.json` in project directory:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/bin/claude_slack_notifier.py --event-type stop --webhook-url 'https://hooks.slack.com/services/PROJECT/SPECIFIC/URL'"
          }
        ]
      }
    ]
  }
}
```

### Customize Message Format

Modify the `create_notification_blocks` function in the script to customize message layout.

### Add Conditional Filtering

Use environment variables or script logic to filter certain notifications:

```bash
# Only send notifications during work hours
if [ $(date +%H) -ge 9 ] && [ $(date +%H) -le 18 ]; then
  python3 ~/bin/claude_slack_notifier.py --event-type stop
fi
```

## 🐛 Troubleshooting

### Not Receiving Notifications?

1. Verify Webhook URL:
   ```bash
   echo $SLACK_WEBHOOK_URL
   ```

2. Test the script:
   ```bash
   echo '{}' | python3 ~/bin/claude_slack_notifier.py --event-type stop --message "Test"
   ```

3. Check if Claude Code loaded the configuration:
   ```
   /hooks
   ```

4. View logs:
   ```bash
   ls -la ~/.claude/logs/
   ```

### Notifications Too Frequent?

Keep only critical events (Notification and Stop), or use matcher to filter specific tools.

### Python Related Errors?

Ensure you're using Python 3.6+:
```bash
python3 --version
```

## 📚 Resources

- [Complete Setup Guide](./SETUP_GUIDE.md)
- [Claude Code Official Documentation](https://docs.claude.com/en/docs/claude-code/hooks)
- [Slack Webhooks Documentation](https://api.slack.com/messaging/webhooks)
- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder)

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

MIT License

## 🙏 Acknowledgments

Built on Claude Code's hooks system and Slack's Incoming Webhooks API.

---

**Tip**: Check `SETUP_GUIDE.md` for more detailed configuration instructions and troubleshooting guide.
