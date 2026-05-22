from user_agents import parse


class DeviceDetector:
    @staticmethod
    def parse_user_agent(user_agent: str) -> dict:
        ua = parse(user_agent or "")
        device_type = "desktop"
        if ua.is_mobile:
            device_type = "mobile"
        elif ua.is_tablet:
            device_type = "tablet"

        return {
            "device_type": device_type,
            "os": ua.os.family.lower() if ua.os.family else None,
            "browser": ua.browser.family.lower() if ua.browser.family else None,
            "is_bot": ua.is_bot,
        }
