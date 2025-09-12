# --- Stage 1: Build the React App ---
FROM node:18-alpine AS build

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Build the static files
RUN npm run build

# --- Stage 2: Serve with NGINX ---
FROM nginx:1.25-alpine

# Copy the built static files from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy the custom NGINX configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# The command to start NGINX
CMD ["nginx", "-g", "daemon off;"]
