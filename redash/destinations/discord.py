import logging

import requests

from redash.models import Alert
from redash.destinations import BaseDestination, register
from redash.utils import json_dumps

colors = {
    # Colors are in a Decimal format as Discord requires them to be Decimals for embeds
    Alert.OK_STATE: "2600544",  # Green Decimal Code
    Alert.TRIGGERED_STATE: "12597547",  # Red Decimal Code
    Alert.UNKNOWN_STATE: "16776960",  # Yellow Decimal Code
}


class Discord(BaseDestination):
    @classmethod
    def configuration_schema(cls):
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "title": "Discord Webhook URL"}
            },
            "secret": ["url"],
            "required": ["url"],
        }

    @classmethod
    def icon(cls):
        return "fa-discord"

    def notify(self, alert, query, user, new_state, app, host, options):
        # Documentation: https://birdie0.github.io/discord-webhooks-guide/discord_webhook.html
        fields = [
            {
                "name": "Query",
                "value": "{host}/queries/{query_id}".format(
                    host=host, query_id=query.id
                ),
                "inline": True,
            },
            {
                "name": "Alert",
                "value": "{host}/alerts/{alert_id}".format(
                    host=host, alert_id=alert.id
                ),
                "inline": True,
            },
        ]
        if alert.options.get("custom_body"):
            fields.append({"name": "Description", "value": alert.options["custom_body"]})
        if new_state == Alert.TRIGGERED_STATE:
            if alert.options.get("custom_subject"):
                text = alert.options["custom_subject"]
            else:
                text = f"{alert.name} just triggered"
            color = colors.get(new_state, "12597547")  # Red Decimal Code
        else:
            text = f"{alert.name} went back to normal"
            color = colors.get(new_state, "2600544")  # Green Decimal Code
        payload = {"content": text, "embeds": [{"color": color, "fields": fields}]}
        headers = {"Content-Type": "application/json"}
        try:
            resp = requests.post(
                options.get("url"),
                data=json_dumps(payload),
                headers=headers,
                timeout=5.0,
            )
            if resp.status_code != 200 and resp.status_code != 204:
                logging.error(
                    "Discord send ERROR. status_code => {status}".format(
                        status=resp.status_code
                    )
                )
        except Exception as e:
            logging.exception("Discord send ERROR: %s", e)


register(Discord)
