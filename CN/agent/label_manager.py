class LabelManager:

    def __init__(self, device_id, label="Human", bot_tier="None"):
        self.device_id = device_id
        self.label = label
        self.bot_tier = bot_tier

    def add_labels(self, features):

        features["device_id"] = self.device_id
        features["label"] = self.label
        features["bot_tier"] = self.bot_tier

        return features