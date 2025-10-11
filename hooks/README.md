# Claude Code Slack 通知系统

一个轻量级的工具，用于在 Claude Code 需要人工操作或任务完成时通过 Slack 发送通知。

## ✨ 功能特性

- 🔔 **自动通知**: 当 Claude Code 需要审批或任务完成时自动发送 Slack 消息
- 🎨 **富文本消息**: 使用 Slack Block Kit 创建美观的通知
- ⚙️ **灵活配置**: 支持多种事件类型和自定义触发条件
- 🔒 **安全**: 通过环境变量管理敏感信息
- 📦 **零依赖**: 仅使用 Python 标准库

## 📦 文件说明

| 文件 | 说明 |
|-----|------|
| `claude_slack_notifier.py` | 主通知脚本 |
| `quick_install.sh` | 快速安装脚本 |
| `SETUP_GUIDE.md` | 详细的安装和配置指南 |
| `hooks_minimal.json` | 最小化配置示例（推荐） |
| `hooks_example.json` | 完整配置示例 |

## 🚀 快速开始

#### 步骤 1: 获取 Slack Webhook URL

1. 访问 https://api.slack.com/apps
2. 创建新应用并启用 Incoming Webhooks
3. 复制生成的 Webhook URL

#### 步骤 2: 设置环境变量

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

添加到 `~/.bashrc` 或 `~/.zshrc` 使其永久生效。

#### 步骤 3: 配置 Claude Code

编辑 `~/.claude/settings.json`:

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

#### 步骤 4: 在 Claude Code 中激活

在 Claude Code 中运行:
```
/hooks
```
然后审核并批准配置。

## 📖 使用示例

### 基本用法

安装完成后，Claude Code 会在以下情况自动发送通知：

1. **需要审批时** (Notification 事件)
   - 例如：需要执行危险命令时
   - 例如：需要修改重要文件时

2. **任务完成时** (Stop 事件)
   - 任何对话结束时
   - 可以查看结果并决定下一步

### 手动测试

```bash
# 测试发送通知
echo '{"notification":"测试消息"}' | \
  python3 ~/bin/claude_slack_notifier.py \
  --event-type notification \
  --message "这是一条测试消息"
```

### 监听特定工具

只在文件修改时通知：

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

## 📊 支持的事件类型

| 事件 | 触发时机 | 推荐 |
|-----|---------|-----|
| `Notification` | Claude Code 请求用户批准 | ✅ |
| `Stop` | 任务完成 | ✅ |
| `UserPromptSubmit` | 用户提交新任务 | 可选 |
| `PreToolUse` | 工具执行前 | 可选 |
| `PostToolUse` | 工具执行后 | 可选 |
| `PreCompaction` | 上下文压缩前 | 可选 |
| `SessionStart` | 会话开始 | 可选 |

## 🎨 消息示例

### Notification 事件
```
🔔 Claude Code 需要您的操作

时间: 2025-10-11 10:30:15
事件类型: notification

通知内容:
即将执行命令 'rm -rf /tmp/*'，需要确认
```

### Stop 事件
```
✅ Claude Code 任务完成

时间: 2025-10-11 10:35:42
事件类型: stop

会话 ID: abc123-def456
```

## 🔧 高级配置

### 针对不同项目使用不同频道

在项目目录创建 `.claude/settings.json`:

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

### 自定义消息格式

修改脚本中的 `create_notification_blocks` 函数来定制消息布局。

### 添加条件过滤

使用环境变量或脚本逻辑来过滤某些通知：

```bash
# 只在工作时间发送通知
if [ $(date +%H) -ge 9 ] && [ $(date +%H) -le 18 ]; then
  python3 ~/bin/claude_slack_notifier.py --event-type stop
fi
```

## 🐛 故障排查

### 没有收到通知？

1. 验证 Webhook URL:
   ```bash
   echo $SLACK_WEBHOOK_URL
   ```

2. 测试脚本:
   ```bash
   echo '{}' | python3 ~/bin/claude_slack_notifier.py --event-type stop --message "测试"
   ```

3. 检查 Claude Code 是否加载了配置:
   ```
   /hooks
   ```

4. 查看日志:
   ```bash
   ls -la ~/.claude/logs/
   ```

### 通知太频繁？

只保留关键事件（Notification 和 Stop），或使用 matcher 过滤特定工具。

### Python 相关错误？

确保使用 Python 3.6+:
```bash
python3 --version
```

## 📚 资源链接

- [完整设置指南](./SETUP_GUIDE.md)
- [Claude Code 官方文档](https://docs.claude.com/en/docs/claude-code/hooks)
- [Slack Webhooks 文档](https://api.slack.com/messaging/webhooks)
- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

基于 Claude Code 的 hooks 系统和 Slack 的 Incoming Webhooks API 构建。

---

**提示**: 查看 `SETUP_GUIDE.md` 获取更详细的配置说明和故障排查指南。
