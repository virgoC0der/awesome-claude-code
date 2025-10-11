# Claude Code Slack Notification System

A lightweight tool for sending Slack notifications when Claude Code requires human intervention or when tasks are completed.

## ✨ Features

- 🔔 **Automatic Notifications**: Automatically send Slack messages when Claude Code needs approval or tasks complete
- 🎨 **Rich Messages**: Create beautiful notifications using Slack Block Kit
- ⚙️ **Flexible Configuration**: Support for multiple event types and custom triggers
- 🔒 **Secure**: Manage sensitive information through environment variables
- 📬 **Dual Mode Support**: Send via Webhook or Direct Message (DM)
- 📦 **Minimal Dependencies**: Webhook mode uses only Python stdlib, DM mode requires `slack-sdk`

## 📦 Files

| File | Description |
|------|-------------|
| `claude_slack_notifier.py` | Main notification script |
| `hooks_minimal.json` | Minimal configuration example (recommended) |
| `hooks_example.json` | Complete configuration example |

## 🚀 Quick Start

### Option 1: Direct Message Mode (Recommended)

Send notifications as direct messages to your Slack account.

#### Step 1: Create Slack App and Get Credentials

1. Visit https://api.slack.com/apps and create a new app
2. Go to **OAuth & Permissions** and add these scopes:
   - `chat:write`
   - `users:read`
3. Install the app to your workspace
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)
5. Get your **Member ID**:
   ```bash
   # Visit Slack in browser, click your profile -> Copy member ID
   # Or use: https://api.slack.com/methods/users.list/test
   ```

#### Step 2: Install Slack SDK

```bash
pip install slack-sdk
```

#### Step 3: Set Environment Variables

```bash
export SLACK_CLAUDE_CODE_BOT_TOKEN="xoxb-your-bot-token-here"
export SLACK_MEMBER_ID="U01234567"
```

Add to `~/.bashrc` or `~/.zshrc` to make it permanent.

#### Step 4: Configure Claude Code

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
            "command": "python3 ~/bin/claude_slack_notifier.py --event-type notification --mode dm",
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
            "command": "python3 ~/bin/claude_slack_notifier.py --event-type stop --mode dm",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

#### Step 5: Activate in Claude Code

Run in Claude Code:
```
/hooks
```
Then review and approve the configuration.

---

### Option 2: Webhook Mode

Send notifications to a Slack channel via Incoming Webhooks.

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
            "command": "python3 ~/bin/claude_slack_notifier.py --event-type notification --mode webhook",
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
            "command": "python3 ~/bin/claude_slack_notifier.py --event-type stop --mode webhook",
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
# Test DM mode
echo '{"notification":"Test message"}' | \
  python3 ~/bin/claude_slack_notifier.py \
  --event-type notification \
  --mode dm \
  --message "This is a test message"

# Test Webhook mode
echo '{"notification":"Test message"}' | \
  python3 ~/bin/claude_slack_notifier.py \
  --event-type notification \
  --mode webhook \
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

**For DM Mode:**

1. Verify environment variables:
   ```bash
   echo $SLACK_CLAUDE_CODE_BOT_TOKEN | head -c 20
   echo $SLACK_MEMBER_ID
   ```

2. Verify slack-sdk is installed:
   ```bash
   python3 -c "import slack_sdk; print('OK')"
   ```

3. Test the script:
   ```bash
   echo '{}' | python3 ~/bin/claude_slack_notifier.py --event-type stop --mode dm --message "Test"
   ```

**For Webhook Mode:**

1. Verify Webhook URL:
   ```bash
   echo $SLACK_WEBHOOK_URL
   ```

2. Test the script:
   ```bash
   echo '{}' | python3 ~/bin/claude_slack_notifier.py --event-type stop --mode webhook --message "Test"
   ```

**Common Issues:**

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

### "slack_sdk not installed" Error?

Install the Slack SDK:
```bash
pip install slack-sdk
# or
pip3 install slack-sdk
```

## 📚 Resources

- [Claude Code Official Documentation](https://docs.claude.com/en/docs/claude-code/hooks)
- [Slack API Documentation](https://api.slack.com/methods/chat.postMessage)
- [Slack Webhooks Documentation](https://api.slack.com/messaging/webhooks)
- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder)
- [slack-sdk Documentation](https://slack.dev/python-slack-sdk/)

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

MIT License

## 🙏 Acknowledgments

Built on Claude Code's hooks system and Slack's Incoming Webhooks API.

