#!/usr/bin/env python3
"""
Claude Code Slack Notifier
Send Claude Code event notifications to Slack
"""

import os
import sys
import json
import argparse
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def send_slack_message(webhook_url, message, blocks=None):
    """
    Send message to Slack
    
    Args:
        webhook_url: Slack Webhook URL
        message: Message text
        blocks: Optional Slack block layout
    """
    payload = {
        "text": message
    }
    
    if blocks:
        payload["blocks"] = blocks
    
    try:
        request = Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        response = urlopen(request)
        if response.status == 200:
            print(f"✓ Slack message sent successfully")
            return True
        else:
            print(f"✗ Failed to send Slack message: {response.status}")
            return False
            
    except HTTPError as e:
        print(f"✗ HTTP error: {e.code} - {e.reason}")
        return False
    except URLError as e:
        print(f"✗ URL error: {e.reason}")
        return False
    except Exception as e:
        print(f"✗ Unknown error: {str(e)}")
        return False


def create_notification_blocks(event_type, details):
    """
    Create rich text Slack notification blocks

    Args:
        event_type: Event type
        details: Event details
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Choose icon and color based on event type
    event_config = {
        "notification": {
            "emoji": "🔔",
            "color": "#FFA500",
            "title": "Claude Code Needs Your Action"
        },
        "stop": {
            "emoji": "✅",
            "color": "#36a64f",
            "title": "Claude Code Task Completed"
        },
        "user_prompt_submit": {
            "emoji": "💬",
            "color": "#2196F3",
            "title": "Claude Code New Task Started"
        },
        "pre_tool_use": {
            "emoji": "⚠️",
            "color": "#FF9800",
            "title": "Claude Code About to Execute Tool"
        },
        "post_tool_use": {
            "emoji": "✔️",
            "color": "#4CAF50",
            "title": "Claude Code Tool Execution Completed"
        }
    }
    
    config = event_config.get(event_type, {
        "emoji": "ℹ️",
        "color": "#808080",
        "title": "Claude Code Event"
    })
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{config['emoji']} {config['title']}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Time:*\n{timestamp}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Event Type:*\n`{event_type}`"
                }
            ]
        }
    ]

    path = details.get('CWD')
    
    # Add project information (if available)
    if path:
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Path:*\n`{path}`"
                }
            ]
        })
    
    # Add detailed information
    if details:
        detail_text = ""
        for key, value in details.items():
            if key == 'CWD':
                continue
            if value:
                # Truncate long values
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."
                detail_text += f"*{key}:*\n```{value}```\n"
        
        if detail_text:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": detail_text
                }
            })

    # Add IDE jump button (if project path is available)
    if path:
        ide_url = f"goland://open?file={path}"
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🚀 Open in GoLand",
                        "emoji": True
                    },
                    "url": ide_url,
                    "style": "primary"
                }
            ]
        })
    
    blocks.append({"type": "divider"})

    return blocks


def parse_stdin_json():
    """Read JSON data from stdin"""
    try:
        if not sys.stdin.isatty():
            data = sys.stdin.read()
            if data.strip():
                return json.loads(data)
    except json.JSONDecodeError as e:
        print(f"Warning: Unable to parse JSON input: {e}")
    except Exception as e:
        print(f"Warning: Error reading stdin: {e}")
    return None


def main():
    parser = argparse.ArgumentParser(description='Claude Code Slack Notification Tool')
    parser.add_argument('--event-type', required=True, 
                       choices=['notification', 'stop', 'user_prompt_submit', 
                               'pre_tool_use', 'post_tool_use'],
                       help='Event type')
    parser.add_argument('--webhook-url', 
                       help='Slack Webhook URL (or use SLACK_WEBHOOK_URL environment variable)')
    parser.add_argument('--message', help='Custom message')
    parser.add_argument('--simple', action='store_true', 
                       help='Use simple text message instead of rich text blocks')
    
    args = parser.parse_args()
    
    # Get Webhook URL
    webhook_url = args.webhook_url or os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print("Error: Must provide --webhook-url or set SLACK_WEBHOOK_URL environment variable")
        sys.exit(1)
    
    # Read event data from stdin
    event_data = parse_stdin_json()
    
    # Prepare message content
    details = {}
    if event_data:
        # Extract useful information
        if 'message' in event_data:
            details['Notification'] = event_data['message']
        if 'cwd' in event_data:
            details['CWD'] = event_data['cwd']
        if 'tool_name' in event_data:
            details['Tool Name'] = event_data['tool_name']
        if 'tool_input' in event_data:
            details['Tool Input'] = str(event_data['tool_input'])
        if 'tool_result' in event_data:
            details['Tool Result'] = str(event_data['tool_result'])
        if 'prompt' in event_data:
            details['Prompt'] = event_data['prompt']
        if 'session_id' in event_data:
            details['Session ID'] = event_data['session_id']
    
    # Send message
    if args.simple:
        message = args.message or f"Claude Code {args.event_type} event"
        send_slack_message(webhook_url, message)
    else:
        blocks = create_notification_blocks(args.event_type, details)
        default_message = f"Claude Code {args.event_type} event"
        send_slack_message(webhook_url, args.message or default_message, blocks)


if __name__ == "__main__":
    main()
