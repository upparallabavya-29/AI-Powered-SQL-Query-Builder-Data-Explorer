# Stage 1: Build the React Application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package descriptors first to cache dependencies layers
COPY frontend/package*.json ./

# Install npm packages
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Compile application bundle
RUN npm run build

# Stage 2: Serve the build outputs using Nginx
FROM nginx:alpine

# Copy build artifacts to nginx public path
COPY --from=builder /app/dist /usr/share/nginx/html

# Apply custom client routing nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
