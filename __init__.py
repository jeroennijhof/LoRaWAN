from PhyPayload import PhyPayload

def new(packet = None):
    phy_payload = PhyPayload()
    if packet:
        phy_payload.packet(packet)
    return phy_payload
