from CN.agent.flow.flow_tracker import FlowTracker
from CN.agent.session.session_tracker import SessionTracker
from CN.agent.features import extract_features
from CN.agent.label_manager import LabelManager
from CN.agent.csv_writer import save_to_csv


class FlowProcessor:

    def __init__(
        self,
        device_id="PC01",
        label="Human",
        bot_tier="None",
        csv_file="sentinelnet_dataset.csv"
    ):
        self.tracker = FlowTracker()
        self.session_tracker = SessionTracker(
    timeout=5,
    device_id=device_id
)

        self.label_manager = LabelManager(
            device_id=device_id,
            label=label,
            bot_tier=bot_tier
        )

        self.csv_file = csv_file

    def process_packet(self, packet_data):

        flow = self.tracker.add_packet(packet_data)

        session = self.session_tracker.add_flow(flow)

        features = extract_features(session)

        labeled_features = self.label_manager.add_labels(features)

        return labeled_features

    def save_features(self, features):

        save_to_csv(
            features,
            self.csv_file
        )

    def save_all_sessions(self):

        for session in self.session_tracker.sessions.values():

            features = extract_features(session)

            labeled_features = self.label_manager.add_labels(features)

            self.save_features(labeled_features)