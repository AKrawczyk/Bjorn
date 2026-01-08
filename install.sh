# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Main installation process
main() 
{
    echo "Starting BJORN installation..."
    

    echo -e "${BLUE}BJORN PI OS Installation Options:${NC}"
    echo "1. Pimoroni Inky pHat on Bookworm OS"
    echo "2. Pimoroni Inky pHat on Trixie OS"
    echo "3. Waveshare epd on Bookworm OS"
    echo "4. Waveshare epd on Trixie OS (Expermental)"
    read -p "Choose an option (1-4): " install_option

    if [$install_option -eq 1]; then
        echo "Installing Pimoroni Inky pHat drivers and software."

        git clone https://github.com/pimoroni/inky
        ~/inky/install.sh

        ~/.virtualenvs/pimoroni/bin/pip install pandas
        ~/.virtualenvs/pimoroni/bin/pip install netifaces pymysql pysmb paramiko sqlalchemy telnetlib-313-and-up
        ~/.virtualenvs/pimoroni/bin/pip install getmac legacy-cgi
        ~/.virtualenvs/pimoroni/bin/pip install python-nmap

        echo "Running the install_bookworm_inky_bjorn.sh script to isntall Bjorn on PI OS Bookworm."
        # Download and run the installer
        wget https://raw.githubusercontent.com/akrawczyk/Bjorn/refs/heads/main/install_bookworm_inky_bjorn.sh
        sudo chmod +x install_bookworm_inky_bjorn.sh && sudo ./install_bookworm_inky_bjorn.sh
        # Choose the choice 1 for automatic installation. It may take a while as a lot of packages and modules will be installed. You must reboot at the end.
    elif [$install_option -eq 2]; then
        echo "Installing Pimoroni Inky pHat drivers and software."

        git clone https://github.com/pimoroni/inky
        ~/inky/install.sh

        ~/.virtualenvs/pimoroni/bin/pip install pandas
        ~/.virtualenvs/pimoroni/bin/pip install netifaces pymysql pysmb paramiko sqlalchemy telnetlib-313-and-up
        ~/.virtualenvs/pimoroni/bin/pip install getmac legacy-cgi
        ~/.virtualenvs/pimoroni/bin/pip install python-nmap

        echo "Running the install_trixie_inky_bjorn.sh script to isntall Bjorn on PI OS Trixie."
        # Download and run the installer
        wget https://raw.githubusercontent.com/akrawczyk/Bjorn/refs/heads/main/install_trixie_inky_bjorn.sh
        sudo chmod +x install_trixie_inky_bjorn.sh && sudo ./install_trixie_inky_bjorn.sh
        # Choose the choice 1 for automatic installation. It may take a while as a lot of packages and modules will be installed. You must reboot at the end.
    elif [$install_option -eq 1]; then
        echo "Running the install_bjorn.sh script to isntall Bjorn on PI OS Bookworm."
        # Download and run the installer
        wget https://raw.githubusercontent.com/akrawczyk/Bjorn/refs/heads/main/install_bjorn.sh
        sudo chmod +x install_bjorn.sh && sudo ./install_bjorn.sh
        # Choose the choice 1 for automatic installation. It may take a while as a lot of packages and modules will be installed. You must reboot at the end.
    elif [$install_option -eq 1]; then
        echo "Running the install_trixie_bjorn.sh script to isntall Bjorn on PI OS Bookworm."
        # Download and run the installer
        wget https://raw.githubusercontent.com/akrawczyk/Bjorn/refs/heads/main/install_trixie_bjorn.sh
        sudo chmod +x install_trixie_bjorn.sh && sudo ./install_trixie_bjorn.sh
        # Choose the choice 1 for automatic installation. It may take a while as a lot of packages and modules will be installed. You must reboot at the end.
    else
        exit
    fi
}

main