FROM node:20-alpine AS builder

WORKDIR /app

# Build arguments for Keycloak configuration
ARG VITE_AUTH_ENABLED=true
ARG VITE_KEYCLOAK_URL=https://auth.wellspringfields.com
ARG VITE_KEYCLOAK_REALM=blaze
ARG VITE_KEYCLOAK_CLIENT_ID=blaze-app

# Set as environment variables for Vite build
ENV VITE_AUTH_ENABLED=$VITE_AUTH_ENABLED
ENV VITE_KEYCLOAK_URL=$VITE_KEYCLOAK_URL
ENV VITE_KEYCLOAK_REALM=$VITE_KEYCLOAK_REALM
ENV VITE_KEYCLOAK_CLIENT_ID=$VITE_KEYCLOAK_CLIENT_ID

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
