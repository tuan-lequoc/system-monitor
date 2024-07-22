# Generate a Self-Signed Certificate
 - openssl genpkey -algorithm RSA -out zabbix.key
 - openssl req -new -key zabbix.key -out csr.pem
 - openssl x509 -req -days 365 -in csr.pem -signkey zabbix.key -out certificate.crt