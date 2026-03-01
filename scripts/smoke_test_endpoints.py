from __future__ import annotations

import argparse
import json
import sys
from urllib import error, request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test ShelfShare Home Assistant endpoints."
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Supabase base URL (example: https://<project-ref>.supabase.co)",
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="ShelfShare Home Assistant API key",
    )
    parser.add_argument(
        "--test-action",
        choices=[
            "none",
            "mark_notification_read",
            "complete_notification",
            "notification_action",
        ],
        default="none",
        help="Optional action endpoint call after summary check",
    )
    parser.add_argument(
        "--notification-id",
        type=int,
        help="Notification id for action tests",
    )
    parser.add_argument(
        "--notification-type",
        choices=[
            "library_invite",
            "event_invite",
            "lend_request",
            "game_table_request",
            "game_event_request",
        ],
        help="Notification type for --test-action notification_action",
    )
    parser.add_argument(
        "--related-id",
        help="Related id for --test-action notification_action",
    )
    parser.add_argument(
        "--decision",
        choices=["accept", "decline", "snooze", "view"],
        default="view",
        help="Decision for --test-action notification_action (default: view)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=20,
        help="HTTP timeout in seconds (default: 20)",
    )
    return parser.parse_args()


def _request_json(
    method: str,
    url: str,
    api_key: str,
    timeout_seconds: int,
    payload: dict | None = None,
) -> tuple[int, dict | list | str]:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        url=url,
        method=method,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-shelfshare-api-key": api_key,
        },
    )

    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
            if not raw.strip():
                return resp.status, ""
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return exc.code, parsed


def main() -> None:
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    summary_url = f"{base_url}/functions/v1/home-assistant-summary"
    action_url = f"{base_url}/functions/v1/home-assistant-action"

    print("[1/2] Checking summary endpoint...")
    summary_status, summary_body = _request_json(
        method="GET",
        url=summary_url,
        api_key=args.api_key,
        timeout_seconds=args.timeout_seconds,
    )

    if summary_status >= 400:
        print(f"Summary check failed: HTTP {summary_status}")
        print(summary_body)
        sys.exit(1)

    summary = summary_body if isinstance(summary_body, dict) else {}
    summary_block = summary.get("summary", {}) if isinstance(summary, dict) else {}

    print(f"Summary check passed: HTTP {summary_status}")
    if isinstance(summary_block, dict):
        print(
            "Counts:",
            {
                "upcoming_events_count": summary_block.get("upcoming_events_count"),
                "lent_out_active_count": summary_block.get("lent_out_active_count"),
                "borrowed_active_count": summary_block.get("borrowed_active_count"),
                "collection_games_count": summary_block.get("collection_games_count"),
                "libraries_count": summary_block.get("libraries_count"),
                "unread_notifications_count": summary_block.get(
                    "unread_notifications_count"
                ),
                "actionable_notifications_count": summary_block.get(
                    "actionable_notifications_count"
                ),
            },
        )

    if args.test_action == "none":
        print("[2/2] Action endpoint test skipped (--test-action none).")
        return

    if args.notification_id is None:
        print("Action test requires --notification-id")
        sys.exit(2)

    print(f"[2/2] Checking action endpoint with {args.test_action}...")

    if args.test_action == "notification_action":
        if args.notification_type is None:
            print("notification_action test requires --notification-type")
            sys.exit(2)
        if args.related_id is None:
            print("notification_action test requires --related-id")
            sys.exit(2)
        action_payload: dict = {
            "action": "notification_action",
            "decision": args.decision,
            "payload": {
                "notificationId": args.notification_id,
                "type": args.notification_type,
                "relatedId": args.related_id,
            },
        }
    else:
        action_payload = {
            "action": args.test_action,
            "notificationId": args.notification_id,
        }

    action_status, action_body = _request_json(
        method="POST",
        url=action_url,
        api_key=args.api_key,
        timeout_seconds=args.timeout_seconds,
        payload=action_payload,
    )

    if action_status >= 400:
        print(f"Action check failed: HTTP {action_status}")
        print(action_body)
        sys.exit(3)

    print(f"Action check passed: HTTP {action_status}")
    print(action_body)


if __name__ == "__main__":
    main()
