"""Readable, directly wired KiCad schematic. Reuses standard-symbol loading helpers."""
from pathlib import Path
import json,uuid
HERE=Path(__file__).resolve().parent
base=(HERE/'build_schematic.py').read_text().split("name='Conn_02x20_Odd_Even'")[0]
B={'__file__':str(HERE/'build_schematic.py')};exec(base,B)
symbol=B['symbol'];q=json.dumps
uid=lambda:str(uuid.uuid4())
root=uid();items=[]
def line(x,y,xx,yy):
    items.append(f'(wire (pts (xy {x} {y}) (xy {xx} {yy})) (stroke (width 0) (type default)) (uuid "{uid()}"))')
def text(value,x,y,size=1.27):
    items.append(f'(text {q(value)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left top)) (uuid "{uid()}"))')
def label(value,x,y):
    items.append(f'(label {q(value)} (at {x} {y} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{uid()}"))')
def junction(x,y):items.append(f'(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))')
def place(lib,name,ref,value,x,y,angle=0,prop=None):
    px,py=prop or (x+7,y-5)
    items.append(f'''(symbol (lib_id {q(lib+':'+name)}) (at {x} {y} {angle}) (unit 1)
      (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")
      (property "Reference" {q(ref)} (at {px} {py} {angle}) (effects (font (size 1.27 1.27))))
      (property "Value" {q(value)} (at {px} {py+3} {angle}) (effects (font (size 1.27 1.27))))
      (instances (project "LAUNCHPAD" (path "/{root}" (reference {q(ref)}) (unit 1)))))''')
def pin(num,name,x,y,angle,length=5.08):
    return f'(pin passive line (at {x} {y} {angle}) (length {length}) (name {q(name)} (effects (font (size 1 1)))) (number "{num}" (effects (font (size 1 1)))))'

# Used Pi pins are grouped by function; numbers remain the actual 40-pin header numbers.
signals=[(2,'5V','5V'),(6,'GND','GND'),(21,'GPIO9 / MISO','SPI0_MISO'),(19,'GPIO10 / MOSI','SPI0_MOSI'),(23,'GPIO11 / SCLK','SPI0_SCLK'),(24,'GPIO8 / CE0','SPI0_CE0'),(22,'GPIO25 / DC','GPIO25'),(13,'GPIO27 / RESET','GPIO27'),(12,'GPIO18 / BACKLIGHT','GPIO18'),(26,'GPIO7 / CE1','SPI0_CE1'),(18,'GPIO24 / TOUCH_IRQ','GPIO24')]
picx,picy=76.2,83.82;lcdcx,lcdcy=215.9,76.2
pi='(symbol "LAUNCHPAD:PiZero2W" (pin_names (offset 1)) (symbol "PiZero2W_0_1" (rectangle (start -25.4 50.8) (end 25.4 -55.88) (stroke (width .254) (type default)) (fill (type background)))) (symbol "PiZero2W_1_1" '
lcd='(symbol "LAUNCHPAD:Waveshare16446" (pin_names (offset 1)) (symbol "Waveshare16446_0_1" (rectangle (start -30.48 43.18) (end 25.4 -30.48) (stroke (width .254) (type default)) (fill (type background)))) (symbol "Waveshare16446_1_1" '
lcd_names=['5V','GND','MISO','MOSI','SCLK','LCD_CS','LCD_DC','LCD_RST','LCD_BL','TP_CS','TP_IRQ']
for i,(number,name,net) in enumerate(signals):
    y=round(45.72+i*5.08,3)
    pi+=pin(number,name,30.48,round(picy-y,3),180)
    lcd+=pin(i+1,lcd_names[i],-35.56,round(lcdcy-y,3),0)
    line(106.68,y,180.34,y);label(net,128.27,y)
pi+=pin(11,'GPIO17 / BUZZER',30.48,round(picy-116.84,3),180)
pi+=pin(4,'5V',30.48,round(picy-124.46,3),180)
pi+=pin(9,'GND',30.48,round(picy-132.08,3),180)
used={n for n,_,_ in signals}|{11,4,9}
names={1:'3V3',3:'GPIO2',5:'GPIO3',7:'GPIO4',8:'GPIO14',10:'GPIO15',14:'GND',15:'GPIO22',16:'GPIO23',17:'3V3',20:'GND',25:'GND',27:'ID_SD',28:'ID_SC',29:'GPIO5',30:'GND',31:'GPIO6',32:'GPIO12',33:'GPIO13',34:'GND',35:'GPIO19',36:'GPIO16',37:'GPIO26',38:'GPIO20',39:'GND',40:'GPIO21'}
for i,number in enumerate(n for n in range(1,41) if n not in used):
    y=round(38.1+i*3.81,3);pi+=pin(number,names[number],-30.48,round(picy-y,3),0)
    items.append(f'(no_connect (at 45.72 {y}) (uuid "{uid()}"))')
pi+='))';lcd+='))'
place('LAUNCHPAD','PiZero2W','J1','Raspberry Pi Zero 2 W / GPIO',picx,picy,prop=(76.2,24.13))
place('LAUNCHPAD','Waveshare16446','LCD1','Waveshare SKU16446 / ST7789',lcdcx,lcdcy,prop=(215.9,24.13))
for y,net in [(124.46,'5V'),(132.08,'GND')]:line(106.68,y,114.3,y);label(net,114.3,y)

# Continuous transistor driver wiring, with explicit junction dots on branches.
place('Device','R','R1','1k',139.7,147.32,90,prop=(139.7,139.7))
place('Transistor_BJT','Q_NPN_EBC','Q1','2N3904',172.72,147.32,prop=(186.69,145))
place('Device','R','R2','100k',154.94,158.75,prop=(141,157.48))
place('Device','Buzzer','BZ1','5V active <=20mA',205.74,127,prop=(213.36,106.68))
place('Device','D','D1','1N4148',228.6,127,270,prop=(242.57,121.92))
line(106.68,116.84,124.46,116.84);line(124.46,116.84,124.46,147.32);line(124.46,147.32,135.89,147.32)
line(143.51,147.32,154.94,147.32);line(154.94,147.32,167.64,147.32);junction(154.94,147.32)
line(154.94,147.32,154.94,154.94);line(154.94,162.56,154.94,168.91)
line(154.94,168.91,175.26,168.91);line(175.26,152.4,175.26,168.91);junction(175.26,168.91);label('GND',160.02,168.91)
line(175.26,142.24,175.26,137.16);line(175.26,137.16,203.2,137.16);line(203.2,137.16,228.6,137.16);junction(203.2,137.16)
line(203.2,129.54,203.2,137.16);line(228.6,130.81,228.6,137.16);label('BUZZ_LOW',203.2,137.16)
line(203.2,124.46,203.2,116.84);line(203.2,116.84,228.6,116.84);line(228.6,123.19,228.6,116.84);label('5V',203.2,116.84)
label('GPIO17_BUZZER_CTRL',114.3,116.84);label('BUZZ_BASE',154.94,147.32)
text('DIRECT-WIRED ASSEMBLY / REV 0.4',25.4,13.97,1.8)
text('Display: 5V power, 3.3V logic. Shared SPI0; separate LCD and touch chip selects.',25.4,19.05)
text('Logical harness numbering only.\nConnect to board by signal NAME.',190.5,100.33,1)
text('POWER AND ASSEMBLY\nSupply Pi through its power micro-USB port.\nUnused header pins are intentionally marked NC.\nNo physical controls: navigation and flight controls are on-screen.\nD1 cathode (bar) to 5V; anode to switched buzzer negative.\nVerify Q1 E/B/C pinout and buzzer current before assembly.',25.4,153.67,1.1)
text('ALERT DRIVER',132.08,108,1.27)
text('No custom PCB or Gerbers. See wiring.csv and production/BUILD.md.',25.4,184.15,1.1)
libs=pi+lcd+symbol('Device','R')+symbol('Device','D')+symbol('Device','Buzzer')+symbol('Transistor_BJT','Q_NPN_EBC')
doc=f'''(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root}") (paper "A4")
 (title_block (title "LAUNCHPAD - Display and Alert Circuit") (date "2026-11-07") (rev "0.4"))
 (lib_symbols {libs}) {''.join(items)} (sheet_instances (path "/" (page "1"))) (embedded_fonts no))'''
(HERE/'LAUNCHPAD.kicad_sch').write_text(doc)
custom=pi.replace('"LAUNCHPAD:PiZero2W"','"PiZero2W"',1)+lcd.replace('"LAUNCHPAD:Waveshare16446"','"Waveshare16446"',1)
(HERE/'LAUNCHPAD.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor") '+custom+')')
(HERE/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "LAUNCHPAD") (type "KiCad") (uri "${KIPRJMOD}/LAUNCHPAD.kicad_sym") (options "") (descr "LAUNCHPAD module interface symbols")))')
(HERE/'LAUNCHPAD.kicad_pro').write_text(json.dumps({'meta':{'filename':'LAUNCHPAD.kicad_pro','version':1}},indent=2))
print(HERE/'LAUNCHPAD.kicad_sch')
