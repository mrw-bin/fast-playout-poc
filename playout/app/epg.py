
import os, datetime, xml.etree.ElementTree as ET

class EPG:
    def __init__(self, out_dir: str, channel_id: str):
        self.out_dir = out_dir
        self.channel_id = channel_id

    def write_day(self, day: datetime.date, programs):
        root = ET.Element('tv', date=day.strftime('%Y-%m-%d'))
        ch = ET.SubElement(root, 'channel', id=str(self.channel_id))
        ET.SubElement(ch, 'display-name', lang='en').text = 'FAST Demo Channel'
        for p in programs:
            pr = ET.SubElement(root, 'programme', start=p['start_iso'], stop=p['stop_iso'], channel=str(self.channel_id))
            ET.SubElement(pr, 'title', lang='en').text = p['title']
            ET.SubElement(pr, 'desc', lang='en').text = p.get('desc','')
            ET.SubElement(pr, 'length', units='seconds').text = str(p['duration'])
            ET.SubElement(pr, 'category', lang='en').text = 'Entertainment'
        os.makedirs(self.out_dir, exist_ok=True)
        fp = os.path.join(self.out_dir, f"{day.strftime('%Y-%m-%d')}.xml")
        ET.indent(root)  # Python 3.9+
        ET.ElementTree(root).write(fp, encoding='utf-8', xml_declaration=True)
        return fp
