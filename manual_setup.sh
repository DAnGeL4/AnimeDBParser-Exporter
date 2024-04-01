#!/bin/bash

check_if_install_package () {
  # checking if required package installed
  local REQUIRED_PKG=$1
  echo "Checking for $REQUIRED_PKG package:"
  local PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $REQUIRED_PKG 2>/dev/null | grep "install ok installed")
  echo $PKG_OK

  if [ "" = "$PKG_OK" ]
  then
    # returns False
    return 1 
  else
    # returns True
    return 0
  fi
}

install_required_pkg () {
  # Installs required package
  local REQUIRED_PKG=$1
  sudo apt-get --yes install $REQUIRED_PKG
}

check_package () {
  # checking if requred package is install
  # and installing if not
  local REQUIRED_PKG=$1
  if ! check_if_install_package $REQUIRED_PKG
  then
    echo "No $REQUIRED_PKG package. Setting up $REQUIRED_PKG."
    install_required_pkg $REQUIRED_PKG
  fi
  echo
} 

# checking if Redis are installed
REDIS_PKG="redis"
if ! check_if_install_package $REDIS_PKG
then
  echo -e "No $REDIS_PKG package. Checking dependencies.\n"
  sudo apt-get update

  # checking if Redis dependecies are installed
  REQUIRED_PKGS="lsb-release curl gpg"
  for REQUIRED_PKG in $REQUIRED_PKGS
  do
  check_package "$REQUIRED_PKG"
  done

  # adding a repository and keys. Installing the Redis package
  echo "Setting up Redis repository."
  curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
  
  echo -e "Setting up $REDIS_PKG.\n"
  sudo apt-get --yes install redis
fi

# configuring Redis
#---
# donloading config file
echo -e "\nDownoad Redis config file."
REDIS_PKG_VERSION=$(redis-server -v | cut -d= -f2 | cut -d ' ' -f1)
curl -O https://raw.githubusercontent.com/redis/redis/$REDIS_PKG_VERSION/redis.conf
wait $!
mv redis.conf "$(pwd)/configs"

# starting Redis
echo -e "\nStarting Redis."
(redis-server "$(pwd)/configs/redis.conf" --bind 127.0.0.1 &)
for (( i=0; i<5; ++i )); do
    if [ "$(redis-cli ping 2>/dev/null)" = "PONG" ]; then break; fi
    sleep 1;
done

# changing configuration
echo -e "\nChanging configuration."
redis-cli CONFIG SET dir "$(pwd)/var/db_dumps"
redis-cli CONFIG SET "dbfilename" "redis_dump.rdb"
redis-cli CONFIG REWRITE
redis-cli SHUTDOWN SAVE

# making an executable Redis startup script
chmod u+x "$(pwd)/sh_scripts/redis_up.sh"
#---


# configuring Celery
#---
# making an executable Celery startup script
chmod u+x "$(pwd)/sh_scripts/celery_worker_up.sh"
#---