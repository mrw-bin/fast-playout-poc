
import base64
from threefive import Cue, SpliceInsert

def make_splice_insert_b64(duration: int) -> str:
    '''Create a simple splice_insert() cue and return base64 payload for EXT-X-DATERANGE.
    This is a minimal POC; in production populate descriptors properly (segmentation type id etc.).'''
    cue = Cue(out=True)
    si = SpliceInsert(time_specified_flag=False, duration=duration)
    cue.command = si
    cue.pack()
    return base64.b64encode(cue.b).decode('ascii')


def daterange_tags(event_id: str, start_iso: str, duration: float, scte35_b64: str) -> str:
    return (
        f'#EXT-X-DATERANGE:ID="{event_id}",START-DATE="{start_iso}",'
        f'DURATION={duration:.3f},SCTE35-OUT=0x{scte35_b64}\n'
        f'#EXT-OATCLS-SCTE35:/{scte35_b64}\n'
    )
