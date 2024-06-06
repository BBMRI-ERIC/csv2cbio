#!/bin/bash

cat <<EOF > $PORTAL_HOME/application.properties
spring.datasource.url=$CBIO_DB_URL
spring.datasource.username=$CBIO_DB_USERNAME
spring.datasource.password=$CBIO_DB_PASSWORD
spring.datasource.driver-class-name=com.mysql.jdbc.Driver
spring.jpa.database-platform=org.hibernate.dialect.MySQL5InnoDBDialect
EOF

# Keep the container running
exec "$@"