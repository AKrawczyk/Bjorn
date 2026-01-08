import logging
from inky.auto import auto
from PIL import Image, ImageDraw
from init_shared import shared_data
from logger import Logger
from comment import Commentaireia

logger = Logger(name="test_display.py", level=logging.DEBUG)

shared_data = shared_data
config = shared_data.config
# Update scale factors: X is now squeezed, Y is now stretched
scale_factor_x = 1 #p_w / WIDTH
scale_factor_y = 1 #p_h / HEIGHT

main_image = None
shared_data.update_image_randomizer()
main_image = shared_data.imagegen
manual_mode_txt = ""

commentaire_ia = Commentaireia()

# Define frise positions for different display types
frise_positions = {
    "default": {  # Default position for other display types
        "x": 0,
        "y": 160
    }
}

def get_frise_position():
        """Get the frise position based on the display type."""
        display_type = config.get("epd_type", "default")
        position = frise_positions.get(display_type, frise_positions["default"])
        return (
            int(position["x"] * scale_factor_x),
            int(position["y"] * scale_factor_y)
        )
        
def display_comment(status):
        comment = commentaire_ia.get_commentaire(status)
        if comment:
            shared_data.bjornsay = comment
            shared_data.bjornstatustext = status

display = auto()
# Swap width and height for your drawing canvas
WIDTH, HEIGHT = display.resolution
portrait_size = (HEIGHT, WIDTH) 

# Portrait dimensions (Tall: e.g., 122x250)
p_w, p_h = portrait_size 

display_comment(shared_data.bjornorch_status)

# 2. INITIALIZE IMAGE
image = Image.new('RGB', (p_w, p_h), color=(255, 255, 255))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, p_w, p_h), fill=(255, 255, 255))

draw.text((int(37 * scale_factor_x), int(5 * scale_factor_y)), "BJORN", font=shared_data.font_viking, fill=(0, 0, 0))
draw.text((int(110 * scale_factor_x), int(170 * scale_factor_y)), manual_mode_txt, font=shared_data.font_arial14, fill=display.BLACK)

#if shared_data.wifi_connected:
image.paste(Image.open("/home/bjorn/Bjorn/resources/images/static/wifi.bmp").convert("RGBA"), (int(5 * scale_factor_x), int(5 * scale_factor_y)))
# # # if shared_data.bluetooth_active:
# # #     image.paste(shared_data.bluetooth, (int(23 * scale_factor_x), int(4 * scale_factor_y)))
#if shared_data.pan_connected:
image.paste(shared_data.connected, (int(104 * scale_factor_x), int(3 * scale_factor_y)))
#if shared_data.usb_active:
image.paste(shared_data.usb, (int(90 * scale_factor_x), int(4 * scale_factor_y)))

stats = [
    (shared_data.target, (int(8 * scale_factor_x), int(22 * scale_factor_y)), (int(28 * scale_factor_x), int(22 * scale_factor_y)), str(shared_data.targetnbr)),
    (shared_data.port, (int(47 * scale_factor_x), int(22 * scale_factor_y)), (int(67 * scale_factor_x), int(22 * scale_factor_y)), str(shared_data.portnbr)),
    (shared_data.vuln, (int(86 * scale_factor_x), int(22 * scale_factor_y)), (int(106 * scale_factor_x), int(22 * scale_factor_y)), str(shared_data.vulnnbr)),
    (shared_data.cred, (int(8 * scale_factor_x), int(41 * scale_factor_y)), (int(28 * scale_factor_x), int(41 * scale_factor_y)), str(shared_data.crednbr)),
    (shared_data.money, (int(3 * scale_factor_x), int(172 * scale_factor_y)), (int(3 * scale_factor_x), int(192 * scale_factor_y)), str(shared_data.coinnbr)),
    (shared_data.level, (int(2 * scale_factor_x), int(217 * scale_factor_y)), (int(4 * scale_factor_x), int(237 * scale_factor_y)), str(shared_data.levelnbr)),
    (shared_data.zombie, (int(47 * scale_factor_x), int(41 * scale_factor_y)), (int(67 * scale_factor_x), int(41 * scale_factor_y)), str(shared_data.zombiesnbr)),
    (shared_data.networkkb, (int(102 * scale_factor_x), int(190 * scale_factor_y)), (int(102 * scale_factor_x), int(208 * scale_factor_y)), str(shared_data.networkkbnbr)),
    (shared_data.data, (int(86 * scale_factor_x), int(41 * scale_factor_y)), (int(106 * scale_factor_x), int(41 * scale_factor_y)), str(shared_data.datanbr)),
    (shared_data.attacks, (int(100 * scale_factor_x), int(218 * scale_factor_y)), (int(102 * scale_factor_x), int(237 * scale_factor_y)), str(shared_data.attacksnbr)),
]

for img, img_pos, text_pos, text in stats:
    image.paste(img, img_pos)
    draw.text(text_pos, text, font=shared_data.font_arial9, fill=display.BLACK)

shared_data.update_bjornstatus()
image.paste(shared_data.bjornstatusimage, (int(3 * scale_factor_x), int(60 * scale_factor_y)))
draw.text((int(35 * scale_factor_x), int(65 * scale_factor_y)), shared_data.bjornstatustext, font=shared_data.font_arial9, fill=display.BLACK)
draw.text((int(35 * scale_factor_x), int(75 * scale_factor_y)), shared_data.bjornstatustext2, font=shared_data.font_arial9, fill=display.BLACK)

# Get frise position based on display type
frise_x, frise_y = get_frise_position()
image.paste(shared_data.frise, (frise_x, frise_y))

draw.rectangle((1, 1, p_w - 1, p_h - 1), outline=0)
draw.line((1, 20, p_w - 1, 20), fill=display.BLACK)
draw.line((1, 59, p_w - 1, 59), fill=display.BLACK)
draw.line((1, 87, p_w - 1, 87), fill=display.BLACK)

lines = shared_data.wrap_text(shared_data.bjornsay, shared_data.font_arialbold, shared_data.width - 4)
y_text = int(90 * scale_factor_y)

if main_image is not None:
    image.paste(main_image, (22, 172)) # (shared_data.x_center1, shared_data.y_bottom1))
else:
    logger.error("Main image not found in shared_data.")

for line in lines:
    draw.text((int(4 * scale_factor_x), y_text), line, font=shared_data.font_arialbold, fill=display.BLACK)
    y_text += (shared_data.font_arialbold.getbbox(line)[3] - shared_data.font_arialbold.getbbox(line)[1]) + 3

final_image = image.rotate(90, expand=True)

display.set_image(final_image)
display.show()