#!/bin/bash

cat <<EOF > $PORTAL_HOME/application.properties
spring.datasource.url=$CBIO_DB_URL
spring.datasource.username=$CBIO_DB_USERNAME
spring.datasource.password=$CBIO_DB_PASSWORD
spring.datasource.driver-class-name=com.mysql.jdbc.Driver
spring.jpa.database-platform=org.hibernate.dialect.MySQL5InnoDBDialect
EOF

VALIDATE_SCRIPT="$PORTAL_HOME/scripts/importer/validateData.py"
if [ ! -e "$VALIDATE_SCRIPT.original" ]; then
  echo "Saving original validation script..."
  cp "$VALIDATE_SCRIPT" "$VALIDATE_SCRIPT.original"
fi

echo "Patching cbio validation..."
if [ -z "$CBIO_AUTH_TOKEN" ]; then
  echo "Token not set. Skipping."
else
  CBIO_AUTH_TOKEN="{\"Authorization\": \"Bearer $CBIO_AUTH_TOKEN\", \"Content-Type\": \"application\/json\"}"
  # Restore file to avoid chaining of headers
  cp "$VALIDATE_SCRIPT.original" "$VALIDATE_SCRIPT"
  sed -i -E "s/requests\.get\(([^)]+)\)/requests.get(\1, verify=False, headers=$CBIO_AUTH_TOKEN)/g" "$VALIDATE_SCRIPT"
  echo "Done"
fi

# Keep the container running
exec "$@"