from pathlib import Path
import re, uuid, json, os

OUT = Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)
LIB = Path(os.environ.get('KICAD_SYMBOL_DIR',r'C:\Program Files\KiCad\10.0\share\kicad\symbols'))
uid = lambda: str(uuid.uuid4())
q = lambda s: json.dumps(s)

def block_at(s, start):
    depth=0; quoted=False; escape=False
    for i in range(start,len(s)):
        c=s[i]
        if c=='"' and not escape: quoted=not quoted
        if not quoted:
            if c=='(': depth+=1
            elif c==')':
                depth-=1
                if depth==0: return s[start:i+1]
        escape=(c=='\\' and not escape)
    raise ValueError('Unclosed expression')

def symbol(lib, name):
    s=(LIB/(lib+'.kicad_sym')).read_text()
    b=block_at(s,s.index('(symbol '+q(name)))
    return b.replace('(symbol '+q(name),'(symbol '+q(lib+':'+name),1)

root=uid(); items=[]
def note(text,x,y,size=1.27):
    items.append(f'(text {q(text)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left top)) (uuid {q(uid())}))')

def wire(x,y,xx,yy):
    items.append(f'(wire (pts (xy {x} {y}) (xy {xx} {yy})) (stroke (width 0) (type default)) (uuid {q(uid())}))')

def label(text,x,y,angle=0):
    items.append(f'(label {q(text)} (at {x} {y} {angle}) (effects (font (size 1 1)) (justify left bottom)) (uuid {q(uid())}))')

def place(lib,name,ref,value,x,y,dy=-8):
    ident=uid()
    items.append(f'''(symbol (lib_id {q(lib+':'+name)}) (at {x} {y} 0) (unit 1)
      (in_bom yes) (on_board yes) (dnp no) (uuid {q(ident)})
      (property "Reference" {q(ref)} (at {x+5} {y+dy} 0) (effects (font (size 1.27 1.27))))
      (property "Value" {q(value)} (at {x+5} {y+dy+3} 0) (effects (font (size 1.27 1.27))))
      (instances (project "LAUNCHPAD-draft" (path {q('/'+root)} (reference {q(ref)}) (unit 1)))))''')

name='Conn_02x20_Odd_Even'
place('Connector_Generic',name,'J1','Pi Zero 2 W GPIO header',75,83.82,-30)
pins={1:'3V3',2:'5V',3:'GPIO2_SDA',4:'5V',5:'GPIO3_SCL',6:'GND',7:'GPIO4',8:'GPIO14_TXD',9:'GND',10:'GPIO15_RXD',11:'GPIO17_BUZZER_CTRL',12:'GPIO18',13:'GPIO27',14:'GND',15:'GPIO22',16:'GPIO23',17:'3V3',18:'GPIO24',19:'SPI0_MOSI',20:'GND',21:'SPI0_MISO',22:'GPIO25',23:'SPI0_SCLK',24:'SPI0_CE0',25:'GND',26:'SPI0_CE1',27:'ID_SD_RESERVED',28:'ID_SC_RESERVED',29:'GPIO5',30:'GND',31:'GPIO6',32:'GPIO12',33:'GPIO13',34:'GND',35:'GPIO19',36:'GPIO16',37:'GPIO26',38:'GPIO20',39:'GND',40:'GPIO21'}
for n,net in pins.items():
    y=round(60.96+((n-1)//2)*2.54,3)
    x=69.92 if n%2 else 82.62
    end=45.72 if n%2 else 101.6
    wire(x,y,end,y)
    label(net,end,y,0 if n%2 else 180)

note('LAUNCHPAD | Rocket-shaped mission-control computer',30,22,2)
note('REV 0.3 - Wired assembly / bench validation required',30,29,1.5)
note('PI INTERFACE - physical header pin numbers',30,42,1.5)
note('DISPLAY MODULE',142,40,1.5)
place('LAUNCHPAD','LCD_Unknown','LCD1','Waveshare 16446 ST7789 revision',185,65,-27)
note('SKU16446: 5V supply; 3.3V logic; SPI + XPT2046 touch.\nLCD1 numbers are logical harness positions, not board pin numbers.\nConnect by printed SIGNAL LABEL; buy ST7789 revision.',132,89)

note('BUZZER DRIVER - proposed 5 V active buzzer, <= 20 mA',132,104,1.3)
place('Device','Buzzer','BZ1','5V active, <=20mA',213.36,124.46)
place('Transistor_BJT','Q_NPN_EBC','Q1','2N3904 (check E/B/C)',180.34,147.32,5)
place('Device','R','R1','1k',147.32,129.54)
place('Device','R','R2','100k',154.94,154.94,5)
place('Device','D','D1','1N4148',231.14,139.7,5)
def net(x,y,xx,yy,n):
    wire(x,y,xx,yy); label(n,xx,yy)
net(147.32,125.73,147.32,120.65,'GPIO17_BUZZER_CTRL')
net(147.32,133.35,147.32,139.7,'BUZZ_BASE')
net(175.26,147.32,167.64,147.32,'BUZZ_BASE')
net(154.94,151.13,154.94,146.05,'BUZZ_BASE')
net(154.94,158.75,154.94,165.1,'GND')
net(182.88,152.4,182.88,165.1,'GND')
net(182.88,142.24,182.88,134.62,'BUZZ_LOW')
net(210.82,121.92,200.66,121.92,'5V')
net(210.82,127,200.66,127,'BUZZ_LOW')
net(227.33,139.7,220.98,139.7,'5V')
net(234.95,139.7,246.38,139.7,'BUZZ_LOW')
note('D1 cathode:5V / anode:BUZZ_LOW.\nBuzzer <=20mA; verify transistor E/B/C.\nUSB power only. Never put 5V on a GPIO.',30,166)
note('POWER: Pi micro-USB input; all GPIO signals 3.3V.\nNo battery or physical simulator controls planned.',30,128)
note('MODES: ISS Watch / Launch Clock / Mission Brief\nSkywatch / Flight Sim; touch/app controls.\nST7789 LCD revision selected; calibrate touch.',30,146)

lcd_pins=[('5V','5V'),('GND','GND'),('MISO','SPI0_MISO'),('MOSI','SPI0_MOSI'),('SCLK','SPI0_SCLK'),('LCD_CS','SPI0_CE0'),('LCD_DC','GPIO25'),('LCD_RST','GPIO27'),('LCD_BL','GPIO18'),('TP_CS','SPI0_CE1'),('TP_IRQ','GPIO24')]
lcd='(symbol "LAUNCHPAD:LCD_Unknown" (pin_names (offset 1)) (property "Reference" "LCD" (at 0 25 0) (effects (font (size 1.27 1.27)))) (property "Value" "Waveshare16446" (at 0 22 0) (effects (font (size 1.27 1.27)))) (symbol "LCD_Unknown_0_1" (rectangle (start -20 20) (end 35 -12) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol "LCD_Unknown_1_1" '
for i,(signal,netname) in enumerate(lcd_pins):
    yy=round(17.78-i*2.54,3)
    lcd+=f'(pin passive line (at -25.4 {yy} 0) (length 5.4) (name {q(signal)} (effects (font (size 1 1)))) (number "{i+1}" (effects (font (size 1 1)))))'
    net(159.6,round(65-yy,3),135.4,round(65-yy,3),netname)
lcd+='))'

doc=f'''(kicad_sch (version 20250114) (generator "eeschema")
 (uuid {q(root)}) (paper "A4")
 (title_block (title "LAUNCHPAD - LCD and Buzzer Circuit") (date "2026-11-04") (rev "0.3 WIRED PROTOTYPE"))
 (lib_symbols {symbol('Connector_Generic',name)} {symbol('Device','Buzzer')} {symbol('Device','R')} {symbol('Device','D')} {symbol('Transistor_BJT','Q_NPN_EBC')} {lcd})
 {''.join(items)}
 (sheet_instances (path "/" (page "1")))
 (embedded_fonts no))'''
path=OUT/'LAUNCHPAD-draft.kicad_sch'
path.write_text(doc,encoding='utf-8')
print(path)
