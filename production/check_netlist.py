"""Check intended electrical connectivity using KiCad's exported XML netlist."""
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
xml=ET.parse(root/'pcb'/'LAUNCHPAD.net.xml').getroot()
nets={n.attrib['name'].lstrip('/'):{(x.attrib['ref'],x.attrib['pin']) for x in n.findall('node')} for n in xml.findall('./nets/net')}
expected={'5V':{('J1','2'),('LCD1','1'),('BZ1','1'),('D1','1')},'GND':{('J1','6'),('LCD1','2'),('Q1','1'),('R2','2')},'SPI0_MISO':{('J1','21'),('LCD1','3')},'SPI0_MOSI':{('J1','19'),('LCD1','4')},'SPI0_SCLK':{('J1','23'),('LCD1','5')},'SPI0_CE0':{('J1','24'),('LCD1','6')},'GPIO25':{('J1','22'),('LCD1','7')},'GPIO27':{('J1','13'),('LCD1','8')},'GPIO18':{('J1','12'),('LCD1','9')},'SPI0_CE1':{('J1','26'),('LCD1','10')},'GPIO24':{('J1','18'),('LCD1','11')},'GPIO17_BUZZER_CTRL':{('J1','11'),('R1','1')},'BUZZ_BASE':{('R1','2'),('R2','1'),('Q1','2')},'BUZZ_LOW':{('BZ1','2'),('Q1','3'),('D1','2')}}
for name,pins in expected.items():
    if not pins<=nets.get(name,set()):raise AssertionError((name,pins,nets.get(name)))
print('PASS: all LCD signals and buzzer-driver connections match the intended mapping')
