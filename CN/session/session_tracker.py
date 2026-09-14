import time


class SessionTracker:

    def __init__(self, timeout=5):
        self.timeout = timeout
        self.sessions = {}

    def add_flow(self, flow):
        flow_key = flow["flow_key"]

        current_time = flow["last_seen"]

        if flow_key not in self.sessions:
            self.sessions[flow_key] = {
                "session_id": len(self.sessions) + 1,
                "flow_key": flow_key,
                "first_seen": flow["first_seen"],
                "last_seen": flow["last_seen"],
                "packet_count": flow["packet_count"],
                "total_bytes": flow["total_bytes"],
                "packet_sizes": list(flow["packet_sizes"]),
                "timestamps": list(flow["timestamps"]),
                "protocol": flow["protocol"]
            }

        else:
            session = self.sessions[flow_key]

            session["last_seen"] = current_time
            session["packet_count"] = flow["packet_count"]
            session["total_bytes"] = flow["total_bytes"]
            session["packet_sizes"] = list(flow["packet_sizes"])
            session["timestamps"] = list(flow["timestamps"])

        return self.sessions[flow_key]

    def get_active_sessions(self, current_time=None):
        if current_time is None:
            current_time = time.time()

        active_sessions = {}

        for key, session in self.sessions.items():
            if current_time - session["last_seen"] <= self.timeout:
                active_sessions[key] = session

        return active_sessions