# display.py updated for Pimoroni Inky pHat – PORTRAIT layout (122x250)
# Modified from by Aaron Krawczyk 2026
# Orignal created by infinition https://github.com/infinition/Bjorn

import threading
import time
import os
import pandas as pd
import signal
import glob
import logging
import random
import sys
import subprocess
from PIL import Image, ImageDraw
from init_shared import shared_data
from comment import Commentaireia
from logger import Logger

# Pimoroni Inky pHat driver - No need for epd_helper
from inky.auto import auto

logger = Logger(name="display.py", level=logging.DEBUG)

class Display:
    WIDTH = 250
    HEIGHT = 122
    display = auto()
    WIDTH, HEIGHT = display.resolution
    
    # Swap width and height for your drawing canvas
    portrait_size = (HEIGHT, WIDTH)

    def __init__(self, shared_data):
        self.shared_data = shared_data
        self.config = self.shared_data.config
        self.shared_data.bjornstatustext2 = "Awakening..."
        self.commentaire_ia = Commentaireia()
        self.semaphore = threading.Semaphore(10)

        # Define frise positions for different display types
        self.frise_positions = {
            "epd2in7": {
                "x": 50,
                "y": 160
            },
            "default": {  # Default position for other display types
                "x": 0,
                "y": 160
            }
        }

        # Force portrait geometry for Pimoroni Inky pHat
        self.shared_data.width = self.WIDTH
        self.shared_data.height = self.HEIGHT
        self.shared_data.x_center1 = 22
        self.shared_data.y_bottom1 = 172
        
        self.manual_mode_txt = ""
        self.main_image = None
        
        self.scale_factor_x = self.shared_data.scale_factor_x
        self.scale_factor_y = self.shared_data.scale_factor_y
        
        # Update scale factors: X is now squeezed, Y is now stretched
        self.scale_factor_x = 1
        self.scale_factor_y = 1

        # ---------------- Threads ----------------

        self.main_image_thread = threading.Thread(target=self.update_main_image)
        self.main_image_thread.daemon = True
        self.main_image_thread.start()

        self.update_shared_data_thread = threading.Thread(target=self.schedule_update_shared_data)
        self.update_shared_data_thread.daemon = True
        self.update_shared_data_thread.start()

        self.update_vuln_count_thread = threading.Thread(target=self.schedule_update_vuln_count)
        self.update_vuln_count_thread.daemon = True
        self.update_vuln_count_thread.start()

    def get_frise_position(self):
        """Get the frise position based on the display type."""
        display_type = self.config.get("epd_type", "default")
        position = self.frise_positions.get(display_type, self.frise_positions["default"])
        return (
            int(position["x"] * self.scale_factor_x),
            int(position["y"] * self.scale_factor_y)
        )

    def schedule_update_shared_data(self):
        while not self.shared_data.display_should_exit:
            self.update_shared_data()
            time.sleep(25)

    def schedule_update_vuln_count(self):
        while not self.shared_data.display_should_exit:
            self.update_vuln_count()
            time.sleep(300)

    def update_main_image(self):
        while not self.shared_data.display_should_exit:
            try:
                self.shared_data.update_image_randomizer()
                self.main_image = self.shared_data.imagegen
                time.sleep(
                    random.uniform(
                        self.shared_data.image_display_delaymin,
                        self.shared_data.image_display_delaymax,
                    )
                )
            except Exception as e:
                logger.error(f"Main image error: {e}")

    # ---------------- Data ----------------

    def get_open_files(self):
        """Get the number of open FD files on the system."""
        try:
            open_files = len(glob.glob('/proc/*/fd/*'))
            logger.debug(f"FD : {open_files}")
            return open_files
        except Exception as e:
            logger.error(f"Error getting open files: {e}")
            return None
        
    def update_vuln_count(self):
        """Update the vulnerability count on the display."""
        with self.semaphore:
            try:
                if not os.path.exists(self.shared_data.vuln_summary_file):
                    df = pd.DataFrame(columns=["IP", "Hostname", "MAC Address", "Port", "Vulnerabilities"])
                    df.to_csv(self.shared_data.vuln_summary_file, index=False)
                    self.shared_data.vulnnbr = 0
                    logger.info("Vulnerability summary file created.")
                else:
                    if os.path.exists(self.shared_data.netkbfile):
                        with open(self.shared_data.netkbfile, 'r') as file:
                            netkb_df = pd.read_csv(file)
                            alive_macs = set(netkb_df[(netkb_df["Alive"] == 1) & (netkb_df["MAC Address"] != "STANDALONE")]["MAC Address"])
                    else:
                        alive_macs = set()

                    with open(self.shared_data.vuln_summary_file, 'r') as file:
                        df = pd.read_csv(file)
                        all_vulnerabilities = set()

                        for index, row in df.iterrows():
                            mac_address = row["MAC Address"]
                            if mac_address in alive_macs and mac_address != "STANDALONE":
                                vulnerabilities = row["Vulnerabilities"]
                                if pd.isna(vulnerabilities) or not isinstance(vulnerabilities, str):
                                    continue

                                if vulnerabilities and isinstance(vulnerabilities, str):
                                    all_vulnerabilities.update(vulnerabilities.split("; "))

                        self.shared_data.vulnnbr = len(all_vulnerabilities)
                        logger.debug(f"Updated vulnerabilities count: {self.shared_data.vulnnbr}")

                    if os.path.exists(self.shared_data.livestatusfile):
                        with open(self.shared_data.livestatusfile, 'r+') as livestatus_file:
                            livestatus_df = pd.read_csv(livestatus_file)
                            livestatus_df.loc[0, 'Vulnerabilities Count'] = self.shared_data.vulnnbr
                            livestatus_df.to_csv(self.shared_data.livestatusfile, index=False)
                            logger.debug(f"Updated livestatusfile with vulnerability count: {self.shared_data.vulnnbr}")
                    else:
                        logger.error(f"Livestatusfile {self.shared_data.livestatusfile} does not exist.")
            except Exception as e:
                logger.error(f"An error occurred in update_vuln_count: {e}")

    def update_shared_data(self):
        """Update the shared data with the latest system information."""
        with self.semaphore:
            try:
                with open(self.shared_data.livestatusfile, 'r') as file:
                    livestatus_df = pd.read_csv(file)
                    self.shared_data.portnbr = livestatus_df['Total Open Ports'].iloc[0]
                    self.shared_data.targetnbr = livestatus_df['Alive Hosts Count'].iloc[0]
                    self.shared_data.networkkbnbr = livestatus_df['All Known Hosts Count'].iloc[0]
                    self.shared_data.vulnnbr = livestatus_df['Vulnerabilities Count'].iloc[0]

                crackedpw_files = glob.glob(f"{self.shared_data.crackedpwddir}/*.csv")

                total_passwords = 0
                for file in crackedpw_files:
                    with open(file, 'r') as f:
                        total_passwords += len(pd.read_csv(f, usecols=[0]))

                self.shared_data.crednbr = total_passwords

                total_data = sum([len(files) for r, d, files in os.walk(self.shared_data.datastolendir)])
                self.shared_data.datanbr = total_data

                total_zombies = sum([len(files) for r, d, files in os.walk(self.shared_data.zombiesdir)])
                self.shared_data.zombiesnbr = total_zombies
                total_attacks = sum([len(files) for r, d, files in os.walk(self.shared_data.actions_dir) if not r.endswith("__pycache__")]) - 2

                self.shared_data.attacksnbr = total_attacks

                self.shared_data.update_stats()
                self.shared_data.manual_mode = self.is_manual_mode()
                if self.shared_data.manual_mode:
                    self.manual_mode_txt = "M"
                else:
                    self.manual_mode_txt = "A"
                self.shared_data.wifi_connected = self.is_wifi_connected()
                self.shared_data.usb_active = self.is_usb_connected()
                self.get_open_files()

            except (FileNotFoundError, pd.errors.EmptyDataError) as e:
                logger.error(f"Error: {e}")
            except Exception as e:
                logger.error(f"Error updating shared data: {e}")


    # ---------------- Helpers ----------------

    def display_comment(self, status):
        comment = self.commentaire_ia.get_commentaire(status)
        if comment:
            self.shared_data.bjornsay = comment
            self.shared_data.bjornstatustext = status
            
    def is_wifi_connected(self):
        """Check if WiFi is connected by checking the current SSID."""
        try:
            result = subprocess.Popen(['iwgetid', '-r'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ssid, error = result.communicate()
            if result.returncode != 0:
                logger.error(f"Error executing 'iwgetid -r': {error}")
                return False
            return bool(ssid.strip())
        except Exception as e:
            logger.error(f"Error checking WiFi status: {e}")
            return False

    def is_manual_mode(self):
        """Check if the BjornOrch is in manual mode."""
        return self.shared_data.manual_mode

    def is_interface_connected(self, interface):
        """Check if any device is connected to the specified interface."""
        try:
            result = subprocess.Popen(['ip', 'neigh', 'show', 'dev', interface], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output, error = result.communicate()
            if result.returncode != 0:
                logger.error(f"Error executing 'ip neigh show dev {interface}': {error}")
                return False
            return bool(output.strip())
        except Exception as e:
            logger.error(f"Error checking connection status on {interface}: {e}")
            return False

    def is_usb_connected(self):
        """Check if any device is connected to the USB interface."""
        try:
            result = subprocess.Popen(['ip', 'neigh', 'show', 'dev', 'usb0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output, error = result.communicate()
            if result.returncode != 0:
                logger.error(f"Error executing 'ip neigh show dev usb0': {error}")
                return False
            return bool(output.strip())
        except Exception as e:
            logger.error(f"Error checking USB connection status: {e}")
            return False

    # ---------------- Rendering ----------------

    def convert_palette(self, img):
        return img.convert("P", palette=Image.ADAPTIVE, colors=2)

    def run(self):
        logger.info("Portrait display loop started")

        while not self.shared_data.display_should_exit:
            try:
               # self.epd_helper.init_partial_update()
                self.display_comment(self.shared_data.bjornorch_status)
                logger.debug(f"Shared width x height: {self.shared_data.width} x {self.shared_data.height}")

                # Portrait dimensions (Tall: e.g., 122x250)
                p_w, p_h = self.portrait_size 

                self.display_comment(self.shared_data.bjornorch_status)

                # 2. INITIALIZE IMAGE
                image = Image.new('RGB', (p_w, p_h), color=(255, 255, 255))
                draw = ImageDraw.Draw(image)
                draw.rectangle((0, 0, p_w, p_h), fill=(255, 255, 255))

                draw.text((int(37 * self.scale_factor_x), int(5 * self.scale_factor_y)), "BJORN", font=self.shared_data.font_viking, fill=(0, 0, 0))
                draw.text((int(110 * self.scale_factor_x), int(170 * self.scale_factor_y)), self.manual_mode_txt, font=self.shared_data.font_arial14, fill=self.display.BLACK)

                if self.shared_data.wifi_connected:
                    image.paste(self.shared_data.wifi, (int(5 * self.scale_factor_x), int(5 * self.scale_factor_y)))
                # # # if shared_data.bluetooth_active:
                # # #     image.paste(shared_data.bluetooth, (int(23 * scale_factor_x), int(4 * scale_factor_y)))
                if self.shared_data.pan_connected:
                    image.paste(self.shared_data.connected, (int(104 * self.scale_factor_x), int(3 * self.scale_factor_y)))
                if self.shared_data.usb_active:
                    image.paste(self.shared_data.usb, (int(90 * self.scale_factor_x), int(4 * self.scale_factor_y)))

                stats = [
                    (shared_data.target, (int(8 * self.scale_factor_x), int(22 * self.scale_factor_y)), (int(28 * self.scale_factor_x), int(22 * self.scale_factor_y)), str(shared_data.targetnbr)),
                    (shared_data.port, (int(47 * self.scale_factor_x), int(22 * self.scale_factor_y)), (int(67 * self.scale_factor_x), int(22 * self.scale_factor_y)), str(shared_data.portnbr)),
                    (shared_data.vuln, (int(86 * self.scale_factor_x), int(22 * self.scale_factor_y)), (int(106 * self.scale_factor_x), int(22 * self.scale_factor_y)), str(shared_data.vulnnbr)),
                    (shared_data.cred, (int(8 * self.scale_factor_x), int(41 * self.scale_factor_y)), (int(28 * self.scale_factor_x), int(41 * self.scale_factor_y)), str(shared_data.crednbr)),
                    (shared_data.money, (int(3 * self.scale_factor_x), int(172 * self.scale_factor_y)), (int(3 * self.scale_factor_x), int(192 * self.scale_factor_y)), str(shared_data.coinnbr)),
                    (shared_data.level, (int(2 * self.scale_factor_x), int(217 * self.scale_factor_y)), (int(4 * self.scale_factor_x), int(237 * self.scale_factor_y)), str(shared_data.levelnbr)),
                    (shared_data.zombie, (int(47 * self.scale_factor_x), int(41 * self.scale_factor_y)), (int(67 * self.scale_factor_x), int(41 * self.scale_factor_y)), str(shared_data.zombiesnbr)),
                    (shared_data.networkkb, (int(102 * self.scale_factor_x), int(190 * self.scale_factor_y)), (int(102 * self.scale_factor_x), int(208 * self.scale_factor_y)), str(shared_data.networkkbnbr)),
                    (shared_data.data, (int(86 * self.scale_factor_x), int(41 * self.scale_factor_y)), (int(106 * self.scale_factor_x), int(41 * self.scale_factor_y)), str(shared_data.datanbr)),
                    (shared_data.attacks, (int(100 * self.scale_factor_x), int(218 * self.scale_factor_y)), (int(102 * self.scale_factor_x), int(237 * self.scale_factor_y)), str(shared_data.attacksnbr)),
                ]

                for img, img_pos, text_pos, text in stats:
                    image.paste(img, img_pos)
                    draw.text(text_pos, text, font=shared_data.font_arial9, fill=self.display.BLACK)

                shared_data.update_bjornstatus()
                image.paste(shared_data.bjornstatusimage, (int(3 * self.scale_factor_x), int(60 * self.scale_factor_y)))
                draw.text((int(35 * self.scale_factor_x), int(65 * self.scale_factor_y)), shared_data.bjornstatustext, font=shared_data.font_arial9, fill=self.display.BLACK)
                draw.text((int(35 * self.scale_factor_x), int(75 * self.scale_factor_y)), shared_data.bjornstatustext2, font=shared_data.font_arial9, fill=self.display.BLACK)

                # Get frise position based on display type
                frise_x, frise_y = self.get_frise_position()
                image.paste(shared_data.frise, (frise_x, frise_y))

                draw.rectangle((1, 1, p_w - 1, p_h - 1), outline=0)
                draw.line((1, 20, p_w - 1, 20), fill=self.display.BLACK)
                draw.line((1, 59, p_w - 1, 59), fill=self.display.BLACK)
                draw.line((1, 87, p_w - 1, 87), fill=self.display.BLACK)

                lines = shared_data.wrap_text(shared_data.bjornsay, shared_data.font_arialbold, p_w - 4)
                y_text = int(90 * self.scale_factor_y)

                if self.main_image is not None:
                    image.paste(self.main_image, (self.shared_data.x_center1, self.shared_data.y_bottom1))
                else:
                    logger.error("Main image not found in shared_data.")

                for line in lines:
                    draw.text((int(4 * self.scale_factor_x), y_text), line, font=shared_data.font_arialbold, fill=self.display.BLACK)
                    y_text += (self.shared_data.font_arialbold.getbbox(line)[3] - self.shared_data.font_arialbold.getbbox(line)[1]) + 3

                final_image = image.rotate(90, expand=True)

                self.display.set_image(final_image)
                self.display.show()
                                
                with open(os.path.join(self.shared_data.webdir, "screen.png"), 'wb') as img_file:
                    image.save(img_file)
                    img_file.flush()
                    os.fsync(img_file.fileno())

                time.sleep(max(getattr(self.shared_data, "screen_delay", 30), 30))

            except Exception as e:
                logger.error(f"Display error: {e}")
                time.sleep(30)


# ---------------- Shutdown ----------------

def handle_exit_display(signum, frame, display_thread):
    """Handle the exit signal and close the display."""
    global should_exit
    shared_data.display_should_exit = True
    logger.info("Exit signal received. Waiting for the main loop to finish...")
    try:
        if main_loop and main_loop.epd:
            main_loop.epd.init(main_loop.epd.sleep)
            main_loop.epd.Dev_exit()
    except Exception as e:
        logger.error(f"Error while closing the display: {e}")
    display_thread.join()
    logger.info("Main loop finished. Clean exit.")
    sys.exit(0)

# Declare main_loop globally
main_loop = None

if __name__ == "__main__":
    try:
        logger.info("Starting main loop...")
        main_loop = Display(shared_data)
        display_thread = threading.Thread(target=main_loop.run)
        display_thread.start()
        logger.info("Main loop started.")
        
        signal.signal(signal.SIGINT, lambda signum, frame: handle_exit_display(signum, frame, display_thread))
        signal.signal(signal.SIGTERM, lambda signum, frame: handle_exit_display(signum, frame, display_thread))
    except Exception as e:
        logger.error(f"An exception occurred during program execution: {e}")
        handle_exit_display(signal.SIGINT, None, display_thread)
        sys.exit(1)