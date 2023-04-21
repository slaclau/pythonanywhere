def get_shields_endpoint(label,message,color='blue'):
    schema = {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": color
    }
    return json.dumps(schema)