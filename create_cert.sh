#!/usr/bin/env bash
#
usage() {
  cat << EOF
  Usage:
   create_certs.sh main.domain [some extra domains...]

   TESTING=1 create_certs.sh some.testing
   create_certs.sh domain.name
   create_certs.sh domain.name another.domain.name and.another.one

EOF
  exit 0
}

# LEDIR contains following dirs and files:
#   certs/ dir for successfully created csr, key and crt files
#   certs-test/ dir used when testing
#   user.pub  user account public key
#   user.key  optional user account private key for automatic signing
: ${LEDIR:=~/letsencrypt}
# "default" means webmaster@[shortest domain name of provided]
: ${EMAIL:=default}
: ${ACCOUNT_PUB:=$LEDIR/user.pub}
# if unset or non-existent you will get prompted to run openssl commands
: ${ACCOUNT_KEY:=$LEDIR/user.key}
: ${CERTSDIR:=$LEDIR/certs${TESTING:+-test}}
# optional WEBROOTS is dir that contains per-domain symlinks to their vhosts DocRoots.
# the idea is that sign_csr will write challenge data to $WEBROOTS/$DOMAIN/challenge-uri
# for LE to automatically verify the request (setting symlinks and permissions is up to you)
: ${WEBROOTS:=$LEDIR/webroots}

custom_ssl_config() {
  cat /etc/ssl/openssl.cnf 
  printf "[letsencryptSAN]\n"
  printf "subjectAltName=DNS:%s" $1
  shift
  for dom; do
    printf ",DNS:%s" $dom
  done
}

gencsr() {  # list of domains
  local base=$TMP/$1
  openssl genrsa 4096 > $base.key 2>/dev/null
  openssl req -new -sha256 -key $base.key -subj "/" \
    -reqexts letsencryptSAN \
    -config <(custom_ssl_config "$@") > $base.csr
}

sign() {
  local base=$TMP/$1
  python sign_csr.py --email $EMAIL \
    --public-key "$ACCOUNT_PUB" \
    ${ACCOUNT_KEY:+--private-key "$ACCOUNT_KEY"} \
    ${TESTING:+--testing} \
    ${WEBROOTS:+--webroots "$WEBROOTS"} \
    "$base.csr" > "$base.crt"
}

info() {
  local crt=$1
  openssl x509 -in "$crt" -noout -text -certopt no_pubkey,no_sigdump,no_aux,no_version
}

# so we don't overwrite (presumably real) certs if something goes wrong with sign
move() {
  local base=$TMP/$1
  mv "$base".* "$CERTSDIR/"
}

main() {
  [ -z "$1" ] && usage
  [ -f "$ACCOUNT_KEY" ] || unset ACCOUNT_KEY
  [ -d "$WEBROOTS" ] || unset WEBROOTS
  TMP=$(mktemp -d)
  trap "rm -rf '$TMP'" EXIT

  gencsr "$@"
  sign $1 && move $1 && info "$CERTSDIR/$1.crt"
}

main "$@"
