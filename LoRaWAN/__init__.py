from .PhyPayload import PhyPayload

def new(nwkey = [], appkey = []):
    return PhyPayload(nwkey, appkey)
