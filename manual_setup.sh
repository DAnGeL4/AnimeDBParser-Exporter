#!/bin/bash

#--System detection
OS_ID=$(grep -oP '(?<=^ID_LIKE=).+' /etc/os-release | tr -d '"')

if [[ ! "$OS_ID" =~ ^(debian|arch)$ ]]; then
    echo "Error: Unsupported operating system. (ID_LIKE: $OS_ID)"
    exit 1
fi

#--Helper functions
check_if_install_package() {
    local REQUIRED_PKG=$1
    echo "Checking for $REQUIRED_PKG package:"
    
    case "$OS_ID" in
        debian)
            local PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $REQUIRED_PKG 2>/dev/null | grep "install ok installed")
            ;;
        arch)
            local PKG_OK=$(pacman -Q $REQUIRED_PKG 2>/dev/null)
            ;;
    esac
    
    echo $PKG_OK
    [ -n "$PKG_OK" ]
}

install_required_pkg() {
    local REQUIRED_PKG=$1
    case "$OS_ID" in
        debian)
            sudo apt-get --yes install $REQUIRED_PKG
            ;;
        arch)
            sudo pacman -S --noconfirm $REQUIRED_PKG
            ;;
    esac
}

check_package() {
    local REQUIRED_PKG=$1
    if ! check_if_install_package $REQUIRED_PKG; then
        echo "No $REQUIRED_PKG package. Setting up $REQUIRED_PKG."
        install_required_pkg $REQUIRED_PKG
    fi
    echo
}

#--Redis setup
setup_redis() {
    # checking if Redis is installed
    REDIS_PKG="redis"
    if ! check_if_install_package $REDIS_PKG; then
        echo -e "No $REDIS_PKG package. Installing Redis.\n"
        
        case "$OS_ID" in
            debian)
                sudo apt-get update
                # checking if Redis dependencies are installed
                REQUIRED_PKGS="lsb-release curl gpg"
                for REQUIRED_PKG in $REQUIRED_PKGS; do
                    check_package "$REQUIRED_PKG"
                done
                
                # adding repository and keys
                echo "Setting up Redis repository."
                curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
                echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
                ;;
            arch)
                sudo pacman -Sy # updating packages database
                ;;
        esac
        
        install_required_pkg $REDIS_PKG
    fi

    # configuring Redis
    echo -e "\nDownload Redis config file."
    REDIS_PKG_VERSION=$(redis-server -v | cut -d= -f2 | cut -d ' ' -f1)
    curl -O https://raw.githubusercontent.com/redis/redis/$REDIS_PKG_VERSION/redis.conf
    wait $!
    mv redis.conf "$(pwd)/configs"

    # changing configuration
    echo -e "\nChanging configuration."
    sudo sed -i "s|^dir .*|dir $(pwd)/var/db_dumps|" "$(pwd)/configs/redis.conf"
    sudo sed -i "s|^dbfilename .*|dbfilename redis_dump.rdb|" "$(pwd)/configs/redis.conf"
}

#--Poetry setup
setup_poetry() {
    # checking if Poetry is installed
    if ! command -v poetry &> /dev/null; then
        echo -e "Poetry is not installed. You can install it using pip or pipx.\n"
        echo "Choose installation method:"
        echo "1) pip (system-wide installation)"
        echo "2) pipx (isolated installation, recommended)"
        read -p "Enter choice [1-2]: " choice

        case $choice in
            1)
                if ! command -v pip &> /dev/null; then
                    echo "pip is not installed. Installing pip first."
                    case "$OS_ID" in
                        debian)
                            sudo apt-get --yes install python3-pip
                            ;;
                        arch)
                            sudo pacman -S --noconfirm python-pip
                            ;;
                    esac
                fi
                pip install --user poetry
                ;;
            2)
                if ! command -v pipx &> /dev/null; then
                    echo "pipx is not installed. Installing pipx first."
                    case "$OS_ID" in
                        debian)
                            sudo apt-get --yes install pipx
                            ;;
                        arch)
                            sudo pacman -S --noconfirm python-pipx
                            ;;
                    esac
                    pipx ensurepath
                fi
                pipx install poetry
                ;;
            *)
                echo "Invalid choice. Please install Poetry manually."
                exit 1
                ;;
        esac
    fi
}

#--Main execution
setup_redis
setup_poetry

echo -e "\nInstalling project dependencies..."
poetry install --no-root --sync

echo -e "\nActivating virtual environment..."
eval $(poetry env activate) || {
    echo "Failed to activate virtual environment"
    exit 1
}

echo -e "\nSetup completed successfully!"
