
from pydantic import BaseModel
from typing import List, Optional

class VodItem(BaseModel):
    file: str
    title: str
    duration: int
    vtt: Optional[str] = None

class BreakEvent(BaseModel):
    start_utc: float  # epoch seconds
    duration: int     # sec
    scte35_b64: str

class HlsVariant(BaseModel):
    name: str
    width: int
    height: int
    v_bitrate: str
    a_bitrate: str

class ChannelConfig(BaseModel):
    mode: str
    channel_id: str
    channel_name: str
    audio_loudness_lufs: float
    ihls: dict
    vod: dict
    live: dict
    ads: dict
    output: dict
    ssai: dict
