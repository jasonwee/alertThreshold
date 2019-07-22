class Config:
    def __init__(self, description, enable, script, metric, value, operator, threshold_operator, alert_value):
        self.description = description
        self.enable = enable
        self.script = script
        self.metric = metric
        self.value = value
        self.operator = operator
        self.threshold_operator = threshold_operator
        self.alert_value = alert_value

    def __str__(self):
        return "description: %s, enable: %, script : %s, metric: %s, value: %s, operator: %s, threshold_operator: %s, alert_value: %s" % (self.description, self.enable, self.script, self.metric, self.value, self.operator, self.threshold_operator, self.alert_value)

    def __repr__(self):
        return self.__str__()